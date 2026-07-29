import json
import os
import threading

import flet as ft

from storage import add_to_buffer, get_stats, get_indexing_estimate, get_world
from indexer import run_indexer
from logseq_importer import import_logseq
from pdf_importer import import_pdf
from tg_importer import import_telegram


class AddView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.log_text = ft.Text(value="", selectable=True, size=13)
        self.status_text = ft.Text(size=13)
        self.source_field = ft.TextField(
            label="Source", value="default", expand=1,
        )
        self.type_dropdown = ft.Dropdown(
            label="Type",
            value="text",
            options=[
                ft.dropdown.Option("text"),
                ft.dropdown.Option("chat"),
                ft.dropdown.Option("docx"),
            ],
            expand=1,
        )
        self.content_field = ft.TextField(
            label="Text content",
            multiline=True,
            min_lines=4,
            max_lines=10,
            expand=True,
        )
        self.file_path_field = ft.TextField(
            label="File path (.docx / .pdf / .json)", expand=True,
        )
        self.index_button = ft.ElevatedButton(
            "▶ Run Indexer",
            on_click=self.on_index,
        )
        self.index_progress = ft.ProgressRing(width=16, height=16, visible=False)

    def _world_id(self) -> int:
        return self.page.session.store.get("world_id") or 1

    def build(self) -> ft.Control:
        return ft.Column(
            [
                ft.ResponsiveRow(
                    [
                        ft.Container(self.source_field, col={"xs": 12, "sm": 6}),
                        ft.Container(self.type_dropdown, col={"xs": 12, "sm": 6}),
                    ],
                    spacing=10,
                ),
                self.content_field,
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            self.file_path_field, col={"xs": 12, "sm": 7, "md": 7},
                        ),
                        ft.Container(
                            ft.Row(
                                [
                                    ft.ElevatedButton(
                                        "📁 Browse",
                                        on_click=self.on_browse,
                                    ),
                                    ft.ElevatedButton(
                                        "➕ Add File", on_click=self.on_add_file,
                                    ),
                                ],
                                spacing=5,
                            ),
                            col={"xs": 12, "sm": 5, "md": 5},
                        ),
                    ],
                    spacing=10,
                ),
                ft.Text(
                    "Supports: .docx (stored for indexing) | "
                    ".pdf (imported as text) | "
                    ".json (Telegram or Logseq export)",
                    size=11, italic=True,
                ),
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            ft.ElevatedButton(
                                "➕ Add Text", on_click=self.on_add,
                            ),
                            col={"xs": 12, "sm": 4, "md": 3},
                        ),
                    ],
                    spacing=10,
                ),
                ft.Divider(),
                ft.ResponsiveRow(
                    [
                        ft.Container(
                            self.index_button, col={"xs": 12, "sm": 4, "md": 3},
                        ),
                        ft.Container(
                            self.index_progress, col={"xs": 12, "sm": 8, "md": 9},
                        ),
                    ],
                    spacing=10,
                ),
                ft.Container(
                    self.log_text,
                    border=ft.Border.all(1, ft.Colors.OUTLINE),
                    border_radius=5,
                    padding=10,
                    expand=True,
                ),
                self.status_text,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    async def on_browse(self, _):
        files = await ft.FilePicker().pick_files(
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["docx", "pdf", "json"],
            allow_multiple=False,
        )
        if files:
            self.file_path_field.value = files[0].path
            self.page.update()

    def on_add(self, _):
        content = self.content_field.value
        if not content:
            return
        add_to_buffer(content, self.source_field.value, self.type_dropdown.value, world_id=self._world_id())
        self.content_field.value = ""
        self.page.update()
        self.refresh_status()

    def on_add_file(self, _):
        path = self.file_path_field.value
        if not path:
            return
        ext = os.path.splitext(path)[1].lower()

        if ext == ".json":
            self._import_json(path)
        elif ext == ".docx":
            add_to_buffer(path, self.source_field.value, "docx", world_id=self._world_id())
            self.file_path_field.value = ""
            self.page.update()
            self.refresh_status()
        elif ext == ".pdf":
            self._import_pdf(path)
        else:
            self.log_text.value = (
                f"Unsupported file type '{ext}'. "
                f"Use .docx, .pdf or .json."
            )
            self.page.update()

    def _import_json(self, path: str):
        wid = self._world_id()
        self.file_path_field.disabled = True
        self.log_text.value = f"Importing {path}..."
        self.page.update()

        def task():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)

                if "blocks" in data:
                    stats = import_logseq(path, world_id=wid)
                    label = "Logseq"
                elif "messages" in data:
                    stats = import_telegram(path, world_id=wid)
                    label = "Telegram"
                else:
                    self.log_text.value = (
                        "Unknown JSON format. Expected 'blocks' (Logseq) "
                        "or 'messages' (Telegram) key."
                    )
                    return

                self.log_text.value = (
                    f"{label} import complete:\n"
                    f"  Total items: {stats['total']}\n"
                    f"  Imported:    {stats['imported']}"
                )
            except Exception as e:
                self.log_text.value = f"Import failed: {e}"
            finally:
                self.file_path_field.value = ""
                self.file_path_field.disabled = False
                self.page.update()
                self.refresh_status()

        threading.Thread(target=task, daemon=True).start()

    def _import_pdf(self, path: str):
        wid = self._world_id()
        self.file_path_field.disabled = True
        self.log_text.value = f"Importing {path}..."
        self.page.update()

        def task():
            try:
                stats = import_pdf(path, world_id=wid)
                self.log_text.value = (
                    f"PDF import complete:\n"
                    f"  Total:      {stats['total']}\n"
                    f"  Imported:   {stats['imported']}"
                )
            except Exception as e:
                self.log_text.value = f"PDF import failed: {e}"
            finally:
                self.file_path_field.value = ""
                self.file_path_field.disabled = False
                self.page.update()
                self.refresh_status()

        threading.Thread(target=task, daemon=True).start()

    def on_index(self, _):
        wid = self._world_id()
        stats = get_stats(world_id=wid)
        pending = stats["pending"]
        if pending == 0:
            self.log_text.value = "Nothing to index."
            self.page.update()
            return

        estimate = get_indexing_estimate(pending, world_id=wid)
        msg = f"Indexing {pending} pending record{'s' if pending != 1 else ''}..."
        if estimate:
            msg += f"\nEstimated time: {estimate}"
        self.log_text.value = msg

        self.index_button.disabled = True
        self.index_progress.visible = True
        self.page.update()

        def task():
            import io
            import sys

            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            try:
                from storage import init_db as s_init
                s_init()
                run_indexer(world_id=wid)
            except Exception as e:
                print(f"Indexer failed: {e}")
            finally:
                sys.stdout = old_stdout

            self.log_text.value = buf.getvalue()
            self.index_button.disabled = False
            self.index_progress.visible = False
            try:
                self.page.update()
            except Exception:
                pass
            self.refresh_status()

        threading.Thread(target=task, daemon=True).start()

    def refresh_status(self):
        wid = self._world_id()
        world = get_world(wid)
        world_name = world["name"] if world else "?"
        stats = get_stats(world_id=wid)
        indexed = stats["total"] - stats["pending"]
        self.status_text.value = (
            f"🌍 {world_name}  |  "
            f"Total: {stats['total']}  "
            f"| Pending: {stats['pending']}  "
            f"| Indexed: {indexed}"
        )
        self.page.update()