import threading

import flet as ft

from storage import (
    save_chat, load_chat_history, get_chat_title,
    create_chat, rename_chat, delete_chat, list_chats,
)
from query import ask_rag_stream


class ChatView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_chat_id: int | None = None
        self.current_messages: list[tuple[str, str]] = []
        self.streaming = False

        self.chat_list = ft.ListView(
            spacing=10,
            auto_scroll=True,
            expand=True,
        )

        self.sidebar_list = ft.ListView(spacing=2, expand=True)

        self.new_chat_btn = ft.ElevatedButton(
            "+ New Chat",
            on_click=self.on_new_chat,
        )

        self.query_field = ft.TextField(
            hint_text="Ask a question...",
            on_submit=self.on_ask,
            expand=True,
        )
        self.ask_button = ft.ElevatedButton("❓ Ask", on_click=self.on_ask)
        self.ask_progress = ft.ProgressRing(width=16, height=16, visible=False)

        self.input_row = ft.Row(
            [self.query_field, self.ask_button, self.ask_progress],
            spacing=10,
        )

        self.chat_container = ft.Container(
            self.chat_list,
            border=ft.Border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=True,
        )

        self.main_area = ft.Column(
            [self.chat_container, self.input_row],
            spacing=10,
            expand=True,
        )

        self.sidebar_col = ft.Column(
            [
                self.new_chat_btn,
                ft.Divider(height=1),
                ft.Text("Chats", size=12, weight=ft.FontWeight.BOLD),
                self.sidebar_list,
            ],
            spacing=5,
            expand=True,
        )

        self.sidebar = ft.Container(
            content=self.sidebar_col,
            width=220,
            padding=10,
            border=ft.Border(
                right=ft.BorderSide(1, ft.Colors.OUTLINE),
            ),
        )

    def build(self) -> ft.Control:
        chats = list_chats()
        if not chats:
            chat_id = create_chat("General")
        else:
            chat_id = chats[0]["id"]

        self.current_chat_id = chat_id

        for chat in chats:
            self.sidebar_list.controls.append(self._build_chat_row(chat))

        for msg in load_chat_history(chat_id, limit=50):
            self.chat_list.controls.append(
                self._make_bubble(msg["query"], msg["answer"])
            )
            self.current_messages.append((msg["query"], msg["answer"]))

        if not self.chat_list.controls:
            self.chat_list.controls.append(
                ft.Text("No messages yet.", italic=True)
            )

        return ft.Row(
            [
                self.sidebar,
                ft.Container(self.main_area, expand=True, padding=10),
            ],
            expand=True,
            spacing=0,
        )

    def _make_bubble(self, query: str, answer: str) -> ft.Container:
        return ft.Container(
            ft.Column(
                [
                    ft.Text(f"Q: {query}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"A: {answer}"),
                ]
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=5,
            padding=10,
        )

    def _build_chat_row(self, chat: dict) -> ft.Container:
        is_active = chat["id"] == self.current_chat_id
        return ft.Container(
            content=ft.Row(
                [
                    ft.Text(
                        chat["title"],
                        expand=True,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.EDIT_OUTLINE,
                        icon_size=14,
                        tooltip="Rename",
                        on_click=lambda _, cid=chat["id"]: self.on_rename_chat(cid),
                    ),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_size=14,
                        tooltip="Delete",
                        on_click=lambda _, cid=chat["id"]: self.on_delete_chat(cid),
                    ),
                ],
                spacing=2,
            ),
            bgcolor=ft.Colors.SECONDARY_CONTAINER if is_active else None,
            border_radius=5,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
            on_click=lambda _, cid=chat["id"]: self.switch_chat(cid),
        )

    def load_chat_list(self):
        chats = list_chats()

        if self.current_chat_id is not None:
            exists = any(c["id"] == self.current_chat_id for c in chats)
            if not exists:
                if chats:
                    self.switch_chat(chats[0]["id"])
                else:
                    self.switch_chat(create_chat("General"))
                return

        self.sidebar_list.controls.clear()
        for chat in chats:
            self.sidebar_list.controls.append(self._build_chat_row(chat))
        self.page.update()

    def switch_chat(self, chat_id: int):
        self.current_chat_id = chat_id
        self.current_messages.clear()
        self.chat_list.controls.clear()

        for msg in load_chat_history(chat_id, limit=50):
            self.chat_list.controls.append(
                self._make_bubble(msg["query"], msg["answer"])
            )
            self.current_messages.append((msg["query"], msg["answer"]))

        if not self.chat_list.controls:
            self.chat_list.controls.append(
                ft.Text("No messages yet.", italic=True)
            )

        self.load_chat_list()

    def on_new_chat(self, _):
        chat_id = create_chat("New Chat")
        self.switch_chat(chat_id)

    def on_rename_chat(self, chat_id: int):
        current_title = get_chat_title(chat_id) or ""

        title_field = ft.TextField(value=current_title, autofocus=True)

        def close(e):
            dlg.open = False
            self.page.update()

        def save(e):
            new_title = title_field.value
            if new_title:
                rename_chat(chat_id, new_title)
                self.load_chat_list()
            dlg.open = False
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Rename chat"),
            content=title_field,
            actions=[
                ft.TextButton("Cancel", on_click=close),
                ft.TextButton("Save", on_click=save),
            ],
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def on_delete_chat(self, chat_id: int):
        chat_title = get_chat_title(chat_id) or "Untitled"

        def close(e):
            dlg.open = False
            self.page.update()

        def confirm(e):
            delete_chat(chat_id)
            dlg.open = False
            self.page.update()
            chats = list_chats()
            if chats:
                self.switch_chat(chats[0]["id"])
            else:
                self.switch_chat(create_chat("General"))

        dlg = ft.AlertDialog(
            title=ft.Text("Delete chat"),
            content=ft.Text(f'Delete "{chat_title}" and all its messages?'),
            actions=[
                ft.TextButton("Cancel", on_click=close),
                ft.TextButton("Delete", on_click=confirm),
            ],
        )

        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def on_ask(self, _):
        query = self.query_field.value
        if not query or self.streaming:
            return

        self.streaming = True
        self.ask_button.disabled = True
        self.ask_progress.visible = True
        self.query_field.value = ""

        if not self.current_messages:
            title = query[:50] + ("..." if len(query) > 50 else "")
            rename_chat(self.current_chat_id, title)
            self.load_chat_list()

        self.page.update()

        answer_bubble = ft.Container(
            ft.Column(
                [
                    ft.Text(f"Q: {query}", weight=ft.FontWeight.BOLD),
                    ft.Text("A: ", italic=True),
                ]
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border_radius=5,
            padding=10,
        )
        self.chat_list.controls.append(answer_bubble)
        self.page.update()

        answer_text = answer_bubble.content.controls[1]
        full_answer = ""

        recent = self.current_messages[-5:]
        chat_context = "\n".join(
            f"User: {q}\nAssistant: {a}" for q, a in recent
        )

        def stream_task():
            nonlocal full_answer
            try:
                for token in ask_rag_stream(query, chat_context=chat_context):
                    full_answer += token
                    answer_text.value = f"A: {full_answer}"
                    self.page.update()
            except Exception as e:
                answer_text.value = f"A: Error: {e}"
                self.page.update()

            save_chat(query, full_answer, self.current_chat_id)
            self.current_messages.append((query, full_answer))
            self.streaming = False
            self.ask_button.disabled = False
            self.ask_progress.visible = False
            self.page.update()

        threading.Thread(target=stream_task, daemon=True).start()
