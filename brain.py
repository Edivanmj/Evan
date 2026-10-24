# Núcleo de decisão do EVAN

import os
import re
import uuid
from collections import deque

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
        self.session_id = uuid.uuid4().hex[:8]
        self.short_term: deque = deque(maxlen=10)  # memória de curto prazo (RAM)

    def handle(self, user_text: str) -> str:
        """Processa uma fala, guardando-a no buffer de curto prazo e no histórico."""
        response = self._handle_inner(user_text)
        if user_text and user_text.strip():
            self._remember_turn("usuario", user_text.strip())
            self._remember_turn("evan", response)
        return response

    def _remember_turn(self, role: str, text: str) -> None:
        self.short_term.append((role, text))
        try:
            self.memory.save_episode(self.session_id, role, text)
        except Exception as erro:
            log_event(f"Erro ao salvar episódio: {erro}", "WARNING")

    def _handle_inner(self, user_text: str) -> str:
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

        # Comando: limpar duplicadas
        if normalized in [
            "limpar duplicadas",
            "limpar memorias duplicadas",
            "limpar memórias duplicadas",
        ]:
            return self._clean_duplicate_memories()

        # Comando: memórias
        if normalized in ["memorias", "memórias"]:
            return self._list_all_memories()

        # Comando: esqueça id 3
        if normalized.startswith("esqueca id") or normalized.startswith("esqueça id"):
            return self._forget_memory_by_id(normalized)

        # Comando: histórico da conversa
        if normalized in ["historico", "conversas", "ultimas conversas"]:
            return self._show_history()

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

    def _system_status(self) -> str:
        db_path = getattr(self.memory, "db_path", "data/evan_memory.db")

        database_status = "ativo" if os.path.exists(db_path) else "não encontrado"

        try:
            memory_count = self.memory.count_memories()
        except Exception as erro:
            log_event(f"Erro ao contar memórias no status: {erro}")
            memory_count = 0

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
                except Exception as erro:
                    log_event(f"Erro ao ler diário no status: {erro}")
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

    def _clean_duplicate_memories(self) -> str:
        # O banco recusa duplicadas automaticamente (índice único em norm_hash).
        return "O banco já bloqueia memórias duplicadas automaticamente."

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
            or "como estas" in normalized
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

        deleted = self.memory.delete_memory_by_id(memory_id)

        if deleted:
            log_event(f"Memória apagada por ID: {memory_id}")
            return f"Entendi. Apaguei a memória ID {memory_id}."

        return "Não encontrei nenhuma memória com esse ID."

    def _show_history(self) -> str:
        episodes = self.memory.recent_episodes(limit=10)
        if not episodes:
            return "Ainda não tenho conversas registradas."
        response = "Últimas falas registradas:\n"
        for ep in episodes:
            quem = "Você" if ep["role"] == "usuario" else "EVAN"
            response += f"- [{ep['ts']}] {quem}: {ep['text'][:120]}\n"
        return response

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

            "o que voce aprendeu",
            "o que você aprendeu",
            "o que aprendeu",
            "aprendeu sobre",
            "o que voce leu",
            "o que você leu",

            "pdf",
            "documento",

            "resuma os pdfs",
            "resumir pdfs",
            "resumo dos pdfs",
            "resuma documentos",
            "resumo dos documentos",

            "me explique",
            "explique sobre",
            "me ensine",
            "ensina sobre",
            "me ensina sobre",
            "fale sobre",
            "fala sobre",
            "resuma sobre",
            "resumo sobre",
            "o que sabe sobre",
            "o que voce sabe sobre",
            "o que você sabe sobre",
            "quais pdfs",
            "quais PDFs",
            "quais documentos",
            "listar pdfs",
            "listar documentos",
            "pdfs aprendidos",
            "documentos aprendidos",
            "me explique esse pdf",
            "explique esse pdf",
            "resuma esse pdf",
            "resuma o pdf",
            "resumo do pdf",
            "pdf em topicos",
            "pdf em tópicos",
            "me faça perguntas",
            "me faca perguntas",
            "quiz do pdf",
            "perguntas sobre o pdf",
        ]

        return any(keyword in normalized for keyword in keywords)

    def _answer_from_memory(self, question: str) -> str:
        normalized = normalize_text(question)
        if any(
            phrase in normalized
            for phrase in (
                "quais pdfs",
                "quais documentos",
                "listar pdfs",
                "listar documentos",
                "pdfs aprendidos",
                "documentos aprendidos",
            )
        ):
            return self._list_learned_pdfs()

        if any(
            phrase in normalized
            for phrase in (
                "me faca perguntas",
                "quiz do pdf",
                "perguntas sobre o pdf",
            )
        ):
            return self._answer_from_pdf(question, mode="quiz")

        memory_topic_without_pdf = (
            "memoria" in normalized
            and "pdf" not in normalized
            and "documento" not in normalized
        )
        if (
            ("sabe sobre" in normalized or "lembra sobre" in normalized)
            and "pdf" not in normalized
            and "documento" not in normalized
        ):
            # Pergunta pessoal: procura nos fatos antes de olhar os PDFs.
            subject = re.sub(r"o que (voce )?(sabe|lembra) sobre", " ", normalized)
            facts = self.memory.search_memories(subject, limit=5, tipos=["fato"])
            if facts:
                return "Eu lembro disso:\n" + "\n".join(
                    f"- {fact['valor']}" for fact in facts
                )

        pdf_question = not memory_topic_without_pdf and any(
            phrase in normalized
            for phrase in (
                "pdf",
                "documento",
                "aprendeu sobre",
                "o que voce aprendeu",
                "o que voce leu",
                "o que voce sabe sobre",
                "me explique",
                "explique sobre",
                "me ensine",
                "ensina sobre",
                "fale sobre",
                "resuma sobre",
                "resumo sobre",
                "o que sabe sobre",
            )
        )
        if pdf_question:
            summary_request = any(
                phrase in normalized
                for phrase in ("resuma", "resumir", "resumo", "em topicos")
            )
            return self._answer_from_pdf(
                question,
                mode="summary" if summary_request else "search",
            )

        # Atalhos de explicação sobre assuntos aprendidos
        if "me explique sobre pdf" in normalized or "explique sobre pdf" in normalized:
            return (
                "Pelo que eu aprendi nos documentos, o aprendizado por PDF permite que eu leia arquivos, "
                "extraia o texto, divida o conteúdo em partes menores e salve essas partes na minha memória. "
                "Isso serve para eu aprender assuntos novos, como programação, robótica, inteligência artificial, "
                "educação, ética e qualquer outro tema que você quiser me ensinar."
            )

        if "me ensine sobre pdf" in normalized or "fale sobre pdf" in normalized:
            return (
                "PDF é uma forma de me ensinar usando documentos. Você coloca o arquivo na pasta pdfs, "
                "roda o pdf_learning.py, e eu salvo o conteúdo em partes na memória. Depois posso responder "
                "perguntas sobre o que aprendi."
            )

        if "resuma sobre memoria" in normalized or "resuma sobre memória" in normalized:
            return (
                "Pelo que eu aprendi, minha memória serve para guardar fatos, comandos, informações sobre você, "
                "conteúdos de PDFs e aprendizados importantes. A memória fica salva no banco de dados, então eu posso "
                "lembrar mesmo depois que o programa fecha. Também devo evitar duplicatas e transformar memórias brutas "
                "em respostas naturais."
            )

        if "fale sobre memoria" in normalized or "fale sobre memória" in normalized:
            return (
                "Minha memória é uma das partes principais do EVAN. Ela permite que eu aprenda com você, lembre fatos, "
                "guarde conteúdos de documentos e use essas informações para responder melhor. Sem memória, eu seria apenas "
                "um chatbot simples de terminal."
            )
        
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

        matches = self.memory.search_memories(question, limit=3, tipos=["fato"])

        if matches:
            first = matches[0]
            return f"Eu lembro que {first['chave']} = {first['valor']}."

        return unknown_response()

    def _answer_from_pdf(self, question: str, mode: str = "search") -> str:
        pdf_memories = self._get_pdf_memories(limit=10000)
        if not pdf_memories:
            return "Ainda não encontrei PDFs aprendidos na memória."

        if mode == "quiz":
            return self._quiz_from_pdf(pdf_memories)

        ignored_words = {
            "a", "as", "ao", "aos", "com", "como", "da", "das", "de", "do",
            "dos", "e", "em", "esse", "esta", "este", "eu", "fale", "fazer",
            "me", "meu", "minha", "na", "nas", "no", "nos", "o", "os", "para",
            "pdf", "pdfs", "por", "que", "resuma", "resumir", "resumo", "sobre",
            "um", "uma", "voce", "aprendeu", "aprendi", "documento", "documentos",
            "explique", "explica", "ensine", "ensina", "topicos", "leu", "sabe",
            "quero", "qual", "quais",
        }
        question_words = set(normalize_text(question).split())
        terms = {
            word for word in question_words
            if len(word) > 2 and word not in ignored_words
        }

        ranked: list[tuple[int, int, dict]] = []
        for memory in pdf_memories:
            content_words = set(normalize_text(memory.get("valor", "")).split())
            key_words = set(normalize_text(memory.get("chave", "")).split())
            score = sum(word in content_words for word in terms)
            score += 2 * sum(word in key_words for word in terms)
            if score:
                ranked.append((score, int(memory.get("id", 0)), memory))

        if terms and not ranked:
            return "Não encontrei esse assunto nos trechos dos PDFs que aprendi."

        if ranked:
            ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
            selected = [item[2] for item in ranked[:3]]
        else:
            selected = sorted(
                pdf_memories,
                key=lambda item: int(item.get("id", 0)),
            )[:3]

        heading = (
            "Trechos relevantes dos documentos:"
            if mode == "search"
            else "Resumo baseado nos trechos que consegui recuperar:"
        )
        excerpts = []
        for memory in selected:
            value = memory.get("valor", "").strip()
            if not value:
                continue
            snippet = value if len(value) <= 420 else value[:417].rsplit(" ", 1)[0] + "..."
            excerpts.append(f"- {self._pdf_citation(memory)}: “{snippet}”")

        if not excerpts:
            return "Os PDFs estão registrados, mas não há trechos de texto disponíveis."
        return heading + "\n" + "\n".join(excerpts)

    @staticmethod
    def _pdf_citation(memory: dict) -> str:
        source = memory.get("fonte") or "PDF sem nome"
        key = memory.get("chave", "")
        page_match = re.search(r"p[aá]gina\s+(\d+)", key, re.IGNORECASE)
        if page_match:
            return f"{source}, página {page_match.group(1)}"
        return source

    def _explain_pdf_topics(self) -> str:
        return self._answer_from_pdf("resuma o PDF", mode="summary")

    def _get_pdf_memories(self, limit: int = 10000) -> list[dict]:
        return self.memory.list_memories(limit=limit, tipo="pdf")

    def _list_learned_pdfs(self) -> str:
        pdf_memories = self._get_pdf_memories()

        if not pdf_memories:
            return "Eu ainda não aprendi nenhum PDF."

        arquivos = {}

        for memory in pdf_memories:
            chave = memory.get("chave", "")

            if "PDF " in chave and " página" in chave:
                nome = chave.split("PDF ", 1)[1].split(" página", 1)[0]
            else:
                nome = "PDF sem nome identificado"

            arquivos[nome] = arquivos.get(nome, 0) + 1

        resposta = "Eu aprendi estes PDFs:\n"

        for nome, quantidade in sorted(arquivos.items()):
            resposta += f"- {nome}: {quantidade} partes salvas na memória\n"

        resposta += (
            "\nVocê pode perguntar:\n"
            "- me explique esse PDF em tópicos\n"
            "- resuma o PDF\n"
            "- me faça perguntas sobre o PDF\n"
        )

        return resposta

    def _quiz_from_pdf(self, pdf_memories: list[dict] | None = None) -> str:
        pdf_memories = pdf_memories or self._get_pdf_memories()
        if not pdf_memories:
            return "Ainda não aprendi nenhum PDF para criar perguntas."

        ignored_words = {
            "a", "as", "ao", "com", "da", "das", "de", "do", "dos", "e", "em",
            "foi", "na", "no", "o", "os", "para", "por", "que", "se", "um",
            "uma", "com", "sobre",
        }
        questions = []
        for memory in sorted(pdf_memories, key=lambda item: int(item.get("id", 0))):
            sentences = re.split(r"(?<=[.!?])\s+", memory.get("valor", "").strip())
            for sentence in sentences:
                words = re.findall(r"\b[\wÀ-ÿ-]+\b", sentence)
                candidates = [
                    word for word in words
                    if len(normalize_text(word)) >= 5
                    and normalize_text(word) not in ignored_words
                ]
                if len(words) < 7 or not candidates:
                    continue
                answer = max(candidates, key=len)
                cloze = re.sub(
                    rf"\b{re.escape(answer)}\b",
                    "_____",
                    sentence,
                    count=1,
                    flags=re.IGNORECASE,
                )
                questions.append(
                    f"- Complete: “{cloze}”\n"
                    f"  Resposta: {answer} ({self._pdf_citation(memory)})"
                )
                if len(questions) >= 5:
                    break
            if len(questions) >= 5:
                break

        if not questions:
            return (
                "Encontrei os PDFs, mas os trechos são curtos demais para gerar "
                "perguntas automáticas confiáveis."
            )
        return "Perguntas geradas a partir do texto real dos PDFs:\n" + "\n".join(questions)