import threading

import flet as ft

from storage import add_to_buffer, get_stats
from indexer import run_indexer


class AddView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.log_text = ft.Text(value="", selectable=True, size=13)
        self.status_text = ft.Text(size=13)
        self.source_field = ft.TextField(label="Source", value="default", width=250)
        self.type_dropdown = ft.Dropdown(
            label="Type",
            value="text",
            options=[
                ft.dropdown.Option("text"),
                ft.dropdown.Option("chat"),
                ft.dropdown.Option("docx"),
            ],
            width=150,
        )
        self.content_field = ft.TextField(
            label="Text content",
            multiline=True,
            min_lines=4,
            max_lines=10,
            width=600,
        )
        self.file_path_field = ft.TextField(
            label="File path (for docx)", width=600,
        )
        self.index_button = ft.ElevatedButton(
            "▶ Run Indexer",
            on_click=self.on_index,
        )
        self.index_progress = ft.ProgressRing(width=16, height=16, visible=False)

    def build(self) -> ft.Control:
        return ft.Column(
            [
                ft.Row(
                    [self.source_field, self.type_dropdown],
                    spacing=10,
                ),
                self.content_field,
                ft.Row(
                    [self.file_path_field, ft.ElevatedButton("➕ Add File", on_click=self.on_add_file)],
                    spacing=10,
                ),
                ft.Row(
                    [ft.ElevatedButton("➕ Add Text", on_click=self.on_add)],
                    spacing=10,
                ),
                ft.Divider(),
                ft.Row(
                    [self.index_button, self.index_progress],
                    spacing=10,
                ),
                ft.Container(
                    self.log_text,
                    border=ft.Border.all(1, ft.Colors.OUTLINE),
                    border_radius=5,
                    padding=10,
                    width=600,
                    height=200,
                ),
                self.status_text,
            ],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
        )

    def on_add(self, _):
        content = self.content_field.value
        if not content:
            return
        add_to_buffer(content, self.source_field.value, self.type_dropdown.value)
        self.content_field.value = ""
        self.page.update()
        self.refresh_status()

    def on_add_file(self, _):
        path = self.file_path_field.value
        if not path:
            return
        add_to_buffer(path, self.source_field.value, "docx")
        self.file_path_field.value = ""
        self.page.update()
        self.refresh_status()

    def on_index(self, _):
        self.index_button.disabled = True
        self.index_progress.visible = True
        self.log_text.value = ""
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
                run_indexer()
            finally:
                sys.stdout = old_stdout

            self.log_text.value = buf.getvalue()
            self.index_button.disabled = False
            self.index_progress.visible = False
            self.page.update()
            self.refresh_status()

        threading.Thread(target=task, daemon=True).start()

    def refresh_status(self):
        stats = get_stats()
        indexed = stats["total"] - stats["pending"]
        self.status_text.value = (
            f"Status: Total: {stats['total']}  "
            f"| Pending: {stats['pending']}  "
            f"| Indexed: {indexed}"
        )
        self.page.update()
