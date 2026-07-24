import argparse
import sys

from storage import init_db, add_to_buffer, get_stats
from indexer import run_indexer
from query import ask_rag
from logseq_importer import import_logseq
from pdf_importer import import_pdf
from tg_importer import import_telegram


def cmd_add(args):
    init_db()
    add_to_buffer(args.content, args.source, args.type)
    print(f"Added {args.type} record from '{args.source}' to buffer.")


def cmd_index(args):
    init_db()
    run_indexer()


def cmd_ask(args):
    response = ask_rag(args.query)
    print(response)


def cmd_status(args):
    init_db()
    stats = get_stats()
    print(f"Total records: {stats['total']}")
    print(f"Pending index: {stats['pending']}")
    print(f"Indexed:      {stats['total'] - stats['pending']}")


def cmd_import_tg(args):
    stats = import_telegram(args.file, args.min_length)
    print(f"Total messages: {stats['total']}")
    print(f"Imported:       {stats['imported']}")


def cmd_import_pdf(args):
    stats = import_pdf(args.file)
    print(f"Total pages: {stats['total']}")
    print(f"Imported:    {stats['imported']}")


def cmd_import_logseq(args):
    stats = import_logseq(args.file)
    print(f"Total blocks: {stats['total']}")
    print(f"Imported:     {stats['imported']}")


def main():
    parser = argparse.ArgumentParser(description="MyRAG - Local RAG System")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Add content to buffer")
    p_add.add_argument("content", help="Text content or path to .docx file")
    p_add.add_argument("--source", default="default", help="Source identifier")
    p_add.add_argument(
        "--type",
        dest="type",
        default="text",
        choices=["chat", "docx", "text"],
        help="Content type",
    )

    p_index = sub.add_parser("index", help="Run batch indexer")

    p_ask = sub.add_parser("ask", help="Ask a question")
    p_ask.add_argument("query", help="Your question")

    p_status = sub.add_parser("status", help="Show buffer stats")

    p_import_tg = sub.add_parser("import-tg", help="Import Telegram export")
    p_import_tg.add_argument("-f", "--file", default="result.json", help="Path to result.json")
    p_import_tg.add_argument("--min-length", type=int, default=15, help="Minimum text length")

    p_import_pdf = sub.add_parser("import-pdf", help="Import PDF document")
    p_import_pdf.add_argument("-f", "--file", required=True, help="Path to PDF file")

    p_import_logseq = sub.add_parser("import-logseq", help="Import Logseq JSON export")
    p_import_logseq.add_argument("-f", "--file", default="export.json", help="Path to Logseq export JSON")

    args = parser.parse_args()

    commands = {
        "add": cmd_add,
        "index": cmd_index,
        "ask": cmd_ask,
        "status": cmd_status,
        "import-tg": cmd_import_tg,
        "import-pdf": cmd_import_pdf,
        "import-logseq": cmd_import_logseq,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
