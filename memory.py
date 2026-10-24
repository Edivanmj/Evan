# Gerenciamento de memória persistente em SQLite (busca FTS5 + episódios)
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import DB_PATH
from utils import log_event, normalize_text

IGNORED_WORDS = {
    "a", "as", "ao", "aos", "com", "da", "das", "de", "do", "dos",
    "e", "em", "eu", "me", "meu", "minha", "na", "nas", "no", "nos",
    "o", "os", "para", "por", "que", "sobre", "um", "uma", "voce",
}

NEW_COLUMNS = {
    "importance": "REAL NOT NULL DEFAULT 0.5",
    "use_count": "INTEGER NOT NULL DEFAULT 0",
    "last_used_at": "TEXT",
    "norm_hash": "TEXT",
}


class MemoryStore:

    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.fts = False
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.initialize_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _hash(tipo: str, chave: str, valor: str) -> str:
        base = f"{normalize_text(tipo)}|{normalize_text(chave)}|{normalize_text(valor)}"
        return hashlib.sha1(base.encode("utf-8")).hexdigest()

    # ---------- criação / migração ----------

    def initialize_db(self) -> None:
        conn = self.connect()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo TEXT NOT NULL,
                    chave TEXT NOT NULL,
                    valor TEXT NOT NULL,
                    fonte TEXT NOT NULL,
                    data_criacao TEXT NOT NULL,
                    data_atualizacao TEXT NOT NULL
                )
            """)
            columns = {r["name"] for r in conn.execute("PRAGMA table_info(memories)")}
            needs_migration = "norm_hash" not in columns
            has_data = conn.execute("SELECT 1 FROM memories LIMIT 1").fetchone()

            if needs_migration and has_data:
                self._backup(conn)

            for name, ddl in NEW_COLUMNS.items():
                if name not in columns:
                    conn.execute(f"ALTER TABLE memories ADD COLUMN {name} {ddl}")

            if needs_migration:
                self._fill_hashes_and_dedup(conn)

            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_hash ON memories(norm_hash)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_tipo ON memories(tipo)")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    ts TEXT NOT NULL,
                    role TEXT NOT NULL,
                    text TEXT NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_episodes_ts ON episodes(ts)")
            self.fts = self._setup_fts(conn)
            conn.commit()

            if self.db_path != ":memory:":
                conn.execute("PRAGMA journal_mode=WAL")
        finally:
            conn.close()

    def _backup(self, conn: sqlite3.Connection) -> None:
        if self.db_path == ":memory:":
            return
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(self.db_path).parent / f"backup_antes_fts_{stamp}.db"
        dest = sqlite3.connect(str(backup_path))
        try:
            conn.backup(dest)
        finally:
            dest.close()
        log_event(f"Backup do banco criado em {backup_path}")

    def _fill_hashes_and_dedup(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            "SELECT id, tipo, chave, valor FROM memories ORDER BY id ASC"
        ).fetchall()
        seen: set[str] = set()
        to_delete = []
        for row in rows:
            h = self._hash(row["tipo"], row["chave"], row["valor"])
            if h in seen:
                to_delete.append((row["id"],))
            else:
                seen.add(h)
                conn.execute(
                    "UPDATE memories SET norm_hash = ? WHERE id = ?", (h, row["id"])
                )
        conn.executemany("DELETE FROM memories WHERE id = ?", to_delete)
        if to_delete:
            log_event(f"Migração: {len(to_delete)} memórias duplicadas removidas.")

    def _setup_fts(self, conn: sqlite3.Connection) -> bool:
        existed = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE name = 'memories_fts'"
        ).fetchone()
        try:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                    chave, valor,
                    content='memories', content_rowid='id',
                    tokenize='unicode61 remove_diacritics 2'
                )
            """)
        except sqlite3.OperationalError:
            log_event("FTS5 indisponível neste SQLite; usando busca simples.", "WARNING")
            return False

        conn.executescript("""
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, chave, valor)
                VALUES (new.id, new.chave, new.valor);
            END;
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, chave, valor)
                VALUES ('delete', old.id, old.chave, old.valor);
            END;
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE OF chave, valor ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, chave, valor)
                VALUES ('delete', old.id, old.chave, old.valor);
                INSERT INTO memories_fts(rowid, chave, valor)
                VALUES (new.id, new.chave, new.valor);
            END;
        """)
        if not existed:
            conn.execute("INSERT INTO memories_fts(memories_fts) VALUES ('rebuild')")
        return True

    # ---------- escrita ----------

    def save_memory(
        self,
        tipo: str,
        chave: str,
        valor: str,
        fonte: str = "usuario",
        replace_existing: bool = False,
        importance: float = 0.5,
    ) -> dict:
        """Salva uma memória ou atualiza uma existente, se solicitado."""
        chave = chave.strip()
        valor = valor.strip()
        now = datetime.now().isoformat(timespec="seconds")
        new_hash = self._hash(tipo, chave, valor)

        if replace_existing:
            existing = self.find_similar_memory(tipo, chave)
            if existing:
                conn = self.connect()
                try:
                    clash = conn.execute(
                        "SELECT * FROM memories WHERE norm_hash = ? AND id != ?",
                        (new_hash, existing["id"]),
                    ).fetchone()
                    if clash:
                        return dict(clash)
                    conn.execute(
                        "UPDATE memories SET valor = ?, fonte = ?, data_atualizacao = ?, "
                        "norm_hash = ? WHERE id = ?",
                        (valor, fonte, now, new_hash, existing["id"]),
                    )
                    conn.commit()
                    updated = conn.execute(
                        "SELECT * FROM memories WHERE id = ?", (existing["id"],)
                    ).fetchone()
                finally:
                    conn.close()
                return dict(updated)

        conn = self.connect()
        try:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO memories
                        (tipo, chave, valor, fonte, data_criacao, data_atualizacao,
                         importance, norm_hash)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (tipo, chave, valor, fonte, now, now, importance, new_hash),
                )
                conn.commit()
                row = conn.execute(
                    "SELECT * FROM memories WHERE id = ?", (cursor.lastrowid,)
                ).fetchone()
            except sqlite3.IntegrityError:  # duplicada: o banco recusa sozinho
                row = conn.execute(
                    "SELECT * FROM memories WHERE norm_hash = ?", (new_hash,)
                ).fetchone()
        finally:
            conn.close()
        return dict(row)

    def delete_memory_by_id(self, memory_id: int) -> bool:
        conn = self.connect()
        try:
            cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    # ---------- leitura ----------

    def find_similar_memory(self, tipo: str, chave: str) -> Optional[sqlite3.Row]:
        """Busca uma memória com chave normalizada igual, sem correspondência parcial."""
        normalized_key = normalize_text(chave)
        if not normalized_key:
            return None

        conn = self.connect()
        try:
            rows = conn.execute(
                "SELECT * FROM memories WHERE tipo = ? ORDER BY id DESC", (tipo,)
            ).fetchall()
        finally:
            conn.close()

        for row in rows:
            if normalize_text(row["chave"]) == normalized_key:
                return row
        return None

    def search_memories(
        self, query: str, limit: int = 5, tipos: Optional[list[str]] = None
    ) -> list[dict]:
        """Busca por palavras inteiras, ordenada por relevância (BM25).

        'tipos' filtra por tipo, ex.: tipos=["pdf"].
        """
        words = [
            w for w in normalize_text(query).split()
            if len(w) > 2 and w not in IGNORED_WORDS
        ]
        if not words or limit <= 0:
            return []

        if not self.fts:
            return self._search_without_fts(set(words), limit, tipos)

        match = " OR ".join(f'"{w}"' for w in dict.fromkeys(words))
        sql = (
            "SELECT m.* FROM memories_fts "
            "JOIN memories m ON m.id = memories_fts.rowid "
            "WHERE memories_fts MATCH ? "
        )
        params: list = [match]
        if tipos:
            sql += f"AND m.tipo IN ({','.join('?' * len(tipos))}) "
            params += tipos
        sql += "ORDER BY bm25(memories_fts, 3.0, 1.0) LIMIT ?"
        params.append(limit)

        conn = self.connect()
        try:
            rows = conn.execute(sql, params).fetchall()
            self._touch(conn, [r["id"] for r in rows])
        finally:
            conn.close()
        return [dict(r) for r in rows]

    def _search_without_fts(self, words: set, limit: int, tipos) -> list[dict]:
        conn = self.connect()
        try:
            rows = conn.execute("SELECT * FROM memories ORDER BY id DESC").fetchall()
        finally:
            conn.close()
        matches = []
        for row in rows:
            if tipos and row["tipo"] not in tipos:
                continue
            row_words = {
                w for item in (row["chave"], row["valor"], row["tipo"])
                for w in normalize_text(item).split()
            }
            overlap = len(words & row_words)
            if overlap:
                matches.append((overlap, int(row["id"]), dict(row)))
        matches.sort(key=lambda m: (m[0], m[1]), reverse=True)
        return [m[2] for m in matches[:limit]]

    @staticmethod
    def _touch(conn: sqlite3.Connection, ids: list[int]) -> None:
        if not ids:
            return
        now = datetime.now().isoformat(timespec="seconds")
        conn.executemany(
            "UPDATE memories SET use_count = use_count + 1, last_used_at = ? WHERE id = ?",
            [(now, i) for i in ids],
        )
        conn.commit()

    def list_memories(self, limit: int = 10, tipo: Optional[str] = None) -> list[dict]:
        conn = self.connect()
        try:
            if tipo:
                rows = conn.execute(
                    "SELECT * FROM memories WHERE tipo = ? ORDER BY id DESC LIMIT ?",
                    (tipo, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memories ORDER BY id DESC LIMIT ?", (limit,)
                ).fetchall()
        finally:
            conn.close()
        return [dict(r) for r in rows]

    def count_memories(self, tipo: Optional[str] = None) -> int:
        conn = self.connect()
        try:
            if tipo:
                row = conn.execute(
                    "SELECT COUNT(*) FROM memories WHERE tipo = ?", (tipo,)
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
        finally:
            conn.close()
        return row[0]

    # ---------- memória episódica (histórico de conversas) ----------

    def save_episode(self, session_id: str, role: str, text: str) -> None:
        """Registra uma fala (role = 'usuario' ou 'evan') com data e hora."""
        text = (text or "").strip()
        if not text:
            return
        now = datetime.now().isoformat(timespec="seconds")
        conn = self.connect()
        try:
            conn.execute(
                "INSERT INTO episodes (session_id, ts, role, text) VALUES (?, ?, ?, ?)",
                (session_id, now, role, text[:2000]),
            )
            conn.commit()
        finally:
            conn.close()

    def recent_episodes(self, limit: int = 10) -> list[dict]:
        conn = self.connect()
        try:
            rows = conn.execute(
                "SELECT * FROM episodes ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        finally:
            conn.close()
        return [dict(r) for r in reversed(rows)]

    def prune_episodes(self, keep_days: int = 90) -> int:
        """Consolidação simples: apaga falas mais antigas que keep_days."""
        conn = self.connect()
        try:
            cursor = conn.execute(
                "DELETE FROM episodes WHERE ts < datetime('now', ?)",
                (f"-{int(keep_days)} days",),
            )
            conn.commit()
            return cursor.rowcount
        finally:
            conn.close()
