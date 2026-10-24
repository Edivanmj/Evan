from pathlib import Path

from pypdf import PdfReader

from config import PDF_DIR
from memory import MemoryStore
from utils import log_event


PDF_FOLDER = PDF_DIR


def clean_text(text: str) -> str:
    if not text:
        return ""

    text = text.replace("\n", " ")
    text = " ".join(text.split())

    return text.strip()


def split_text(text: str, max_size: int = 900) -> list[str]:
    if max_size <= 0:
        raise ValueError("max_size precisa ser maior que zero.")

    words = text.split()
    parts: list[str] = []
    current_words: list[str] = []
    current_size = 0

    for word in words:
        while len(word) > max_size:
            if current_words:
                parts.append(" ".join(current_words))
                current_words = []
                current_size = 0
            parts.append(word[:max_size])
            word = word[max_size:]

        added_size = len(word) + (1 if current_words else 0)
        if current_words and current_size + added_size > max_size:
            parts.append(" ".join(current_words))
            current_words = [word]
            current_size = len(word)
        else:
            current_words.append(word)
            current_size += added_size

    if current_words:
        parts.append(" ".join(current_words))
    return parts


def learn_pdf(file_path: str | Path, memory: MemoryStore | None = None) -> int:
    memory = memory or MemoryStore()

    file_path = Path(file_path)
    file_name = file_path.name

    reader = PdfReader(file_path)

    saved_count = 0

    for page_number, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        text = clean_text(raw_text)

        if not text:
            log_event(
                f"PDF sem texto extraível: {file_name} | página {page_number}. "
                "Pode ser necessário OCR."
            )
            continue

        parts = split_text(text)

        for part_index, part in enumerate(parts, start=1):
            key = f"PDF {file_name} página {page_number} parte {part_index}"

            memory.save_memory(
                "pdf",
                key,
                part,
                fonte=file_name,
                replace_existing=True,
            )

            saved_count += 1

    log_event(f"PDF aprendido: {file_name} | partes salvas: {saved_count}")

    return saved_count


def learn_all_pdfs() -> str:
    if not PDF_FOLDER.exists():
        PDF_FOLDER.mkdir(parents=True, exist_ok=True)
        return "Criei a pasta pdfs. Coloque seus arquivos PDF lá dentro."

    pdf_files = [
        file for file in PDF_FOLDER.iterdir()
        if file.is_file() and file.suffix.lower() == ".pdf"
    ]

    if not pdf_files:
        return "Não encontrei nenhum PDF na pasta pdfs."

    total_parts = 0
    report = "Aprendizado por PDF concluído:\n"

    for file_path in pdf_files:
        try:
            saved = learn_pdf(file_path)
            total_parts += saved
            if saved:
                report += f"- {file_path.name}: {saved} partes aprendidas\n"
            else:
                report += (
                    f"- {file_path.name}: nenhum texto extraível; "
                    "se for digitalizado, será necessário OCR\n"
                )

        except Exception as erro:
            report += f"- {file_path.name}: erro ao ler PDF: {erro}\n"
            log_event(f"Erro ao aprender PDF {file_path.name}: {erro}")

    report += f"\nTotal de partes salvas na memória: {total_parts}"

    return report


if __name__ == "__main__":
    print(learn_all_pdfs())