import argparse
import sys

from storage import init_db, add_to_buffer, get_stats, list_worlds, create_world, delete_world, get_world
from indexer import run_indexer
from query import ask_rag
from logseq_importer import import_logseq
from pdf_importer import import_pdf
from tg_importer import import_telegram


def _resolve_world_id(world_arg: str | None) -> int:
    if world_arg is None:
        from config import DEFAULT_WORLD_ID
        return DEFAULT_WORLD_ID
    try:
        return int(world_arg)
    except ValueError:
        worlds = list_worlds()
        for w in worlds:
            if w["name"] == world_arg:
                return w["id"]
        print(f"World '{world_arg}' not found.", file=sys.stderr)
        sys.exit(1)


def cmd_add(args):
    init_db()
    wid = _resolve_world_id(args.world)
    add_to_buffer(args.content, args.source, args.type, world_id=wid)
    print(f"Added {args.type} record from '{args.source}' to buffer.")


def cmd_index(args):
    init_db()
    wid = _resolve_world_id(args.world)
    run_indexer(world_id=wid)


def cmd_ask(args):
    wid = _resolve_world_id(args.world)
    response = ask_rag(
        args.query,
        api_key=args.api_key or "",
        model_name=args.model or "",
        force_local=args.force_local,
        world_id=wid,
    )
    print(response)


def cmd_status(args):
    init_db()
    wid = _resolve_world_id(args.world)
    stats = get_stats(world_id=wid)
    print(f"Total records: {stats['total']}")
    print(f"Pending index: {stats['pending']}")
    print(f"Indexed:      {stats['total'] - stats['pending']}")


def cmd_import_tg(args):
    wid = _resolve_world_id(args.world)
    stats = import_telegram(args.file, args.min_length, world_id=wid)
    print(f"Total messages: {stats['total']}")
    print(f"Imported:       {stats['imported']}")


def cmd_import_pdf(args):
    wid = _resolve_world_id(args.world)
    stats = import_pdf(args.file, world_id=wid)
    print(f"Total pages: {stats['total']}")
    print(f"Imported:    {stats['imported']}")


def cmd_import_logseq(args):
    wid = _resolve_world_id(args.world)
    stats = import_logseq(args.file, world_id=wid)
    print(f"Total blocks: {stats['total']}")
    print(f"Imported:     {stats['imported']}")


def cmd_world_list(args):
    init_db()
    worlds = list_worlds()
    if not worlds:
        print("No worlds found.")
        return
    print(f"{'ID':<4} {'Name':<20} {'Description':<30} {'Created'}")
    print("-" * 70)
    for w in worlds:
        print(f"{w['id']:<4} {w['name']:<20} {w['description']:<30} {w['created_at']}")


def cmd_world_create(args):
    init_db()
    wid = create_world(args.name, args.description or "")
    print(f"Created world '{args.name}' with id {wid}.")


def cmd_world_delete(args):
    init_db()
    wid = _resolve_world_id(str(args.id))
    world = get_world(wid)
    if not world:
        print(f"World {args.id} not found.")
        return
    delete_world(wid)
    print(f"Deleted world '{world['name']}' (id {wid}).")


def main():
    parser = argparse.ArgumentParser(description="MyRAG - Local RAG System")
    parser.add_argument("--world", default=None, help="World name or ID (default: 1)")
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
    p_ask.add_argument(
        "--model", default="",
        help="OpenRouter model name (e.g. qwen/qwen-2.5-72b-instruct)",
    )
    p_ask.add_argument(
        "--api-key", default="",
        help="OpenRouter API key (overrides OPENROUTER_API_KEY env)",
    )
    p_ask.add_argument(
        "--force-local", action="store_true",
        help="Force local LLM only",
    )

    p_status = sub.add_parser("status", help="Show buffer stats")

    p_import_tg = sub.add_parser("import-tg", help="Import Telegram export")
    p_import_tg.add_argument("-f", "--file", default="result.json", help="Path to result.json")
    p_import_tg.add_argument("--min-length", type=int, default=15, help="Minimum text length")

    p_import_pdf = sub.add_parser("import-pdf", help="Import PDF document")
    p_import_pdf.add_argument("-f", "--file", required=True, help="Path to PDF file")

    p_import_logseq = sub.add_parser("import-logseq", help="Import Logseq JSON export")
    p_import_logseq.add_argument("-f", "--file", default="export.json", help="Path to Logseq export JSON")

    p_world = sub.add_parser("world", help="Manage worlds")
    wsub = p_world.add_subparsers(dest="world_command", required=True)

    w_list = wsub.add_parser("list", help="List all worlds")
    w_create = wsub.add_parser("create", help="Create a new world")
    w_create.add_argument("--name", required=True, help="World name")
    w_create.add_argument("--description", default="", help="World description")
    w_delete = wsub.add_parser("delete", help="Delete a world")
    w_delete.add_argument("--id", required=True, help="World ID or name")

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

    if args.command == "world":
        world_commands = {
            "list": cmd_world_list,
            "create": cmd_world_create,
            "delete": cmd_world_delete,
        }
        world_commands[args.world_command](args)
    else:
        commands[args.command](args)


if __name__ == "__main__":
    main()