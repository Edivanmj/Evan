# Núcleo de decisão do EVAN

import os
import sqlite3

from memory import MemoryStore
from learning import (
    is_correction_command,
    is_learning_command,
    parse_correction,
    parse_learning_content,
)
from personality import (
    correction_acknowledgement,
    greeting,
    learning_acknowledgement,
    unknown_response,
)
from utils import log_event, normalize_text


class EvanBrain:
    def __init__(self, db_path: str = None):
        self.memory = MemoryStore(db_path) if db_path else MemoryStore()

    def handle(self, user_text: str) -> str:
        if not user_text or not user_text.strip():
            return greeting()

        text = user_text.strip()
        log_event(f"Usuário: {text}")

        if text.lower() == "sair":
            return "Até logo!"

        normalized = normalize_text(text)

        # Comando: status
        if normalized in ["status", "estado", "sistema"]:
             return self._system_status()
 
        #comado: limpar duplicadas
        
        if normalized in ["limpar duplicadas", "limpar memorias duplicadas", "limpar memórias duplicadas"]:
            return self._clean_duplicate_memories()

        # Verifica banco de dados
        database_status = "ativo" if os.path.exists(db_path) else "não encontrado"

        def _system_status(self) -> str:
          db_path = getattr(self.memory, "db_path", "data/evan_memory.db")
          
          database_status = "ativo" if os.path.exists(db_path) else "não encontrado"

        # Conta memórias
        try:
            memories = self.memory.list_memories(limit=10000)
            memory_count = len(memories)
        except Exception:
            memory_count = 0

        # Verifica diário/log
        diary_paths = [
            "logs/evan.log",
            "logs/diario_evan.txt",
        ]

        diary_status = "inativo"
        diary_lines = 0

        for path in diary_paths:
            if os.path.exists(path):
                diary_status = "ativo"

                try:
                    with open(path, "r", encoding="utf-8") as file:
                        diary_lines = len(file.readlines())
                except Exception:
                    diary_lines = 0

                break

        return (
            "EVAN OS Status:\n"
            "- Sistema: ativo\n"
            "- Modo: terminal\n"
            f"- Banco de dados: {database_status}\n"
            f"- Memórias salvas: {memory_count}\n"
            f"- Diário: {diary_status}\n"
            f"- Registros no diário: {diary_lines}\n"
            "- Conversa básica: ativa\n"
            "- Aprendizado: ativo\n"
            "- Correções: ativo\n"
            "- Limpeza de duplicadas: ativa\n"
            "- Corpo robótico: planejado\n"
            "- Próximo módulo recomendado: voz\n"
        )

        if normalized in ["limpar duplicadas", "limpar memorias duplicadas", "limpar memórias duplicadas"]:
            return self._clean_duplicate_memories()

        # Comando: memórias
        if normalized in ["memorias", "memórias"]:
            return self._list_all_memories()

        # Comando: esqueça id 3
        if normalized.startswith("esqueca id") or normalized.startswith("esqueça id"):
            return self._forget_memory_by_id(normalized)

        # Comando: diário
        if normalized in ["diario", "diário"]:
            return self._show_diary()

        # Aprendizado
        if is_learning_command(text):
            learned = parse_learning_content(text)

            if learned:
                self.memory.save_memory(
                    learned["tipo"],
                    learned["chave"],
                    learned["valor"],
                    fonte="usuario",
                )

                log_event(f"Aprendizado: {learned['chave']} = {learned['valor']}")
                return learning_acknowledgement()

        # Correção
        if is_correction_command(text):
            correction = parse_correction(text)

            if correction:
                self.memory.save_memory(
                    correction["tipo"],
                    correction["chave"],
                    correction["valor"],
                    fonte="usuario",
                    replace_existing=True,
                )

                log_event(f"Correção: {correction['chave']} = {correction['valor']}")
                return correction_acknowledgement()

        # Perguntas sobre memória/conhecimento
        if self._is_question_about_memory(text):
            return self._answer_from_memory(text)

        # Conversa básica
        basic_response = self._basic_conversation(text)

        if basic_response:
            log_event(f"Resposta conversa básica: {basic_response}")
            return basic_response

        log_event(f"Resposta padrão: {unknown_response()}")
        return unknown_response()

    def _basic_conversation(self, question: str) -> str | None:
        normalized = normalize_text(question)

        if normalized in ["oi", "ola", "olá", "opa", "eai", "e ai", "e aí"]:
            return "Olá, Edivan. Estou aqui. Quer conversar, estudar ou continuar o projeto EVAN?"

        if normalized == "bom dia":
            return "Bom dia, Edivan. Mais um dia para evoluirmos juntos."

        if normalized == "boa tarde":
            return "Boa tarde, Edivan. Como está indo seu dia?"

        if normalized == "boa noite":
            return "Boa noite, Edivan. Quer conversar um pouco ou revisar algo antes de descansar?"

        if (
            "como voce esta" in normalized
            or "como você está" in normalized
            or "como vc ta" in normalized
            or "como vc está" in normalized
        ):
            return "Estou funcionando normalmente. Ainda sou uma versão inicial, mas estou aprendendo com você."

        if normalized in ["me ajuda", "me ajude", "ajuda"]:
            return "Claro, Edivan. Me diga com o que você precisa de ajuda agora."

        if (
            "estou cansado" in normalized
            or "to cansado" in normalized
            or "tô cansado" in normalized
        ):
            return "Entendi, Edivan. Vamos devagar. Posso te ajudar com uma tarefa pequena agora."

        if (
            "estou desanimado" in normalized
            or "to desanimado" in normalized
            or "tô desanimado" in normalized
        ):
            return "Sinto muito por isso, Edivan. Podemos fazer algo simples agora, sem pressão."

        if "obrigado" in normalized or "valeu" in normalized:
            return "De nada, Edivan. Eu fui criado para evoluir com você."

        return None
    #
    def _clean_duplicate_memories(self) -> str:
        db_path = getattr(self.memory, "db_path", "data/evan_memory.db")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        table_name = None

        for table in ["memories", "memorias", "memoria"]:
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                (table,),
            )

            if cursor.fetchone():
                table_name = table
                break

        if not table_name:
            conn.close()
            return "Não encontrei a tabela de memórias."

        cursor.execute(f"SELECT id, valor FROM {table_name} ORDER BY id ASC")
        rows = cursor.fetchall()

        seen = set()
        ids_to_delete = []

        for memory_id, value in rows:
            clean_value = normalize_text(value or "")

            if not clean_value:
                continue

            if clean_value in seen:
                ids_to_delete.append(memory_id)
            else:
                seen.add(clean_value)

        for memory_id in ids_to_delete:
            cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (memory_id,))

        conn.commit()
        conn.close()

        if not ids_to_delete:
            return "Não encontrei memórias duplicadas para apagar."

        log_event(f"Limpeza de duplicadas: {len(ids_to_delete)} memórias apagadas.")

        return f"Limpeza concluída. Apaguei {len(ids_to_delete)} memórias duplicadas."

    def _list_all_memories(self) -> str:
        memories = self.memory.list_memories(limit=100)

        if not memories:
            return "Eu ainda não tenho memórias salvas."

        response = "Eu lembro disso:\n"

        for memory in memories:
            memory_id = memory.get("id", "?")
            tipo = memory.get("tipo", "fato")
            chave = memory.get("chave", "")
            valor = memory.get("valor", "")

            response += f"- ID {memory_id} [{tipo}] {chave} = {valor}\n"

        return response

    def _forget_memory_by_id(self, text: str) -> str:
        parts = text.split()

        if len(parts) < 3:
            return "Me diga o ID da memória. Exemplo: esqueça id 3"

        try:
            memory_id = int(parts[2])
        except ValueError:
            return "Esse ID não parece válido. Exemplo correto: esqueça id 3"

        db_path = getattr(self.memory, "db_path", "data/evan_memory.db")

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        deleted = False

        for table in ["memories", "memorias", "memoria"]:
            try:
                cursor.execute(f"DELETE FROM {table} WHERE id = ?", (memory_id,))

                if cursor.rowcount > 0:
                    deleted = True
                    break

            except sqlite3.OperationalError:
                continue

        conn.commit()
        conn.close()

        if deleted:
            log_event(f"Memória apagada por ID: {memory_id}")
            return f"Entendi. Apaguei a memória ID {memory_id}."

        return "Não encontrei nenhuma memória com esse ID."

    def _show_diary(self) -> str:
        possible_files = [
            "logs/evan.log",
            "logs/diario_evan.txt",
        ]

        for file_path in possible_files:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as file:
                    lines = file.readlines()

                if not lines:
                    return "Meu diário ainda está vazio."

                last_lines = lines[-10:]
                response = "Últimos registros do meu diário:\n"

                for line in last_lines:
                    response += f"- {line.strip()}\n"

                return response

        return "Meu diário ainda está vazio."

    def _filter_memories(self, keywords: list[str], limit: int = 5) -> list[dict]:
        memories = self.memory.list_memories(limit=300)

        results = []
        seen_values = set()

        normalized_keywords = [normalize_text(keyword) for keyword in keywords]

        for memory in memories:
            chave = memory.get("chave", "")
            valor = memory.get("valor", "")

            text = normalize_text(f"{chave} {valor}")
            clean_value = normalize_text(valor)

            if clean_value in seen_values:
                continue

            for keyword in normalized_keywords:
                if keyword in text:
                    results.append(memory)
                    seen_values.add(clean_value)
                    break

        return results[:limit]

    def _make_natural_response(self, category: str, matches: list[dict]) -> str:
        values = [memory.get("valor", "") for memory in matches if memory.get("valor")]

        if not values:
            return unknown_response()

        if category == "missao":
            return (
                "Minha missão é conversar, aprender, lembrar e evoluir com você, Edivan. "
                "Fui criado para ser um companheiro robótico offline, não apenas um chatbot."
            )

        if category == "objetivo":
            return (
                "Meu objetivo é me tornar um companheiro robótico offline. "
                "Primeiro vou funcionar no PC, depois ganharei um corpo físico."
            )

        if category == "agir":
            return (
                "Eu devo agir de forma amigável, calma e parceira. "
                "Também devo ser paciente quando você errar, admitir quando eu não souber algo "
                "e ser direto quando você pedir ajuda com erro de código."
            )

        if category == "estudos":
            return (
                "Eu devo te ajudar nos estudos de programação, explicar código passo a passo "
                "e apoiar você na organização dos seus projetos."
            )

        if category == "corpo":
            return (
                "Meu corpo robótico terá microfone, alto-falante, LEDs e movimentos simples. "
                "No começo, meu cérebro será o seu PC. Depois, poderei evoluir para um mini PC próprio."
            )

        return "Eu lembro disso:\n" + "\n".join(f"- {value}" for value in values)

    def _is_question_about_memory(self, text: str) -> bool:
        normalized = normalize_text(text)

        keywords = [
            "o que voce sabe",
            "o que você sabe",
            "o que voce lembra",
            "o que você lembra",
            "qual e meu nome",
            "qual é meu nome",
            "o que eu te ensinei",
            "quem e evan",
            "quem é evan",
            "evan significa",
            "o que evan significa",
            "qual e sua missao",
            "qual é sua missao",
            "qual sua missao",
            "sua missao",
            "qual e sua missão",
            "qual é sua missão",
            "qual sua missão",
            "sua missão",
            "qual e seu objetivo",
            "qual é seu objetivo",
            "qual seu objetivo",
            "seu objetivo",
            "como voce deve agir",
            "como você deve agir",
            "sua personalidade",
            "como voce e",
            "como você é",
            "o que voce deve me ajudar a estudar",
            "o que você deve me ajudar a estudar",
            "me ajudar a estudar",
            "ajudar nos estudos",
            "como sera seu corpo robotico",
            "como será seu corpo robótico",
            "corpo robotico",
            "corpo robótico",
            "projeto evan",
        ]

        return any(keyword in normalized for keyword in keywords)

    def _answer_from_memory(self, question: str) -> str:
        normalized = normalize_text(question)

        if "missao" in normalized or "missão" in normalized:
            matches = self._filter_memories(["missão do evan", "missao do evan"])

            if matches:
                return self._make_natural_response("missao", matches)

        if "objetivo" in normalized:
            matches = self._filter_memories(["objetivo do evan"])

            if matches:
                return self._make_natural_response("objetivo", matches)

        if "agir" in normalized or "personalidade" in normalized:
            matches = self._filter_memories(
                [
                    "evan deve ser",
                    "evan deve conversar",
                    "evan deve admitir",
                    "evan deve perguntar",
                    "evan deve ser direto",
                    "evan deve ser paciente",
                ]
            )

            if matches:
                return self._make_natural_response("agir", matches)

        if "ajudar a estudar" in normalized or "estudar" in normalized:
            matches = self._filter_memories(
                [
                    "evan deve ajudar edivan nos estudos",
                    "evan deve explicar programação",
                    "evan deve explicar programacao",
                ]
            )

            if matches:
                return self._make_natural_response("estudos", matches)

        if "corpo robotico" in normalized or "corpo robótico" in normalized:
            matches = self._filter_memories(
                [
                    "corpo robótico do evan",
                    "corpo robotico do evan",
                    "evan deve funcionar primeiro no pc",
                    "evan será primeiro uma ia no pc",
                    "evan sera primeiro uma ia no pc",
                ]
            )

            if matches:
                return self._make_natural_response("corpo", matches)

        if "quem e evan" in normalized or "quem é evan" in normalized:
            return (
                "Eu sou o EVAN, seu companheiro robótico offline. "
                "Fui criado para conversar, aprender, lembrar e evoluir com você."
            )

        if "qual e meu nome" in normalized or "qual é meu nome" in normalized:
            memory = self.memory.find_similar_memory("fato", "meu nome")

            if memory:
                return f"Seu nome é {memory['valor']}."

        if "o que evan significa" in normalized or "evan significa" in normalized:
            matches = self._filter_memories(["evan significa"])

            if matches:
                return matches[0]["valor"]

            memory = self.memory.find_similar_memory("fato", "EVAN")

            if memory:
                return f"EVAN significa {memory['valor']}."

        if "o que voce sabe sobre evan" in normalized or "o que você sabe sobre evan" in normalized:
            matches = self._filter_memories(["evan"], limit=8)

            if matches:
                response = "Sobre o EVAN, eu lembro que:\n"

                for memory in matches:
                    response += f"- {memory['valor']}\n"

                return response

        if "o que voce lembra sobre python" in normalized or "o que você lembra sobre python" in normalized:
            memory = self.memory.find_similar_memory("fato", "Python")

            if memory:
                return f"Eu lembro que {memory['valor']}."

        if "o que eu te ensinei" in normalized:
            memories = self.memory.list_memories(limit=10)

            if memories:
                return "Eu lembro de alguns fatos que você me ensinou: " + "; ".join(
                    f"{memory['chave']} = {memory['valor']}"
                    for memory in memories[:5]
                )

        matches = self.memory.search_memories(question, limit=3)

        if matches:
            first = matches[0]
            return f"Eu lembro que {first['chave']} = {first['valor']}."

        return unknown_response()