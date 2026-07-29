from pypdf import PdfReader

from storage import add_to_buffer, init_db


def parse_pdf(filepath: str) -> str:
    reader = PdfReader(filepath)
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages)


def import_pdf(filepath: str, world_id: int = 1) -> dict[str, int]:
    init_db()
    content = parse_pdf(filepath)
    if not content:
        return {"total": 0, "imported": 0}

    import os
    source = os.path.splitext(os.path.basename(filepath))[0]
    add_to_buffer(content, source, "text", world_id=world_id)

    return {"total": 1, "imported": 1}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Import PDF into RAG buffer")
    parser.add_argument("-f", "--file", required=True, help="Path to PDF file")
    args = parser.parse_args()

    stats = import_pdf(args.file)
    print(f"Total pages: {stats['total']}")
    print(f"Imported:    {stats['imported']}")


if __name__ == "__main__":
    main()
