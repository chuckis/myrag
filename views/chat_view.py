import threading

import flet as ft

from storage import save_chat, load_chat_history
from query import ask_rag_stream


class ChatView:
    def __init__(self, page: ft.Page):
        self.page = page
        self.chat_list = ft.ListView(
            spacing=10,
            auto_scroll=True,
            height=400,
        )
        self.query_field = ft.TextField(
            hint_text="Ask a question...",
            on_submit=self.on_ask,
            expand=True,
        )
        self.ask_button = ft.ElevatedButton("❓ Ask", on_click=self.on_ask)
        self.ask_progress = ft.ProgressRing(width=16, height=16, visible=False)
        self.streaming = False

    def build(self) -> ft.Control:
        self.load_history()
        return ft.Column(
            [
                ft.Container(
                    self.chat_list,
                    border=ft.Border.all(1, ft.Colors.OUTLINE),
                    border_radius=5,
                    padding=10,
                ),
                ft.Row(
                    [self.query_field, self.ask_button, self.ask_progress],
                    spacing=10,
                ),
            ],
            spacing=10,
        )

    def load_history(self):
        self.chat_list.controls.clear()
        for msg in load_chat_history(limit=5):
            self.chat_list.controls.append(
                ft.Container(
                    ft.Column(
                        [
                            ft.Text(f"Q: {msg['query']}", weight=ft.FontWeight.BOLD),
                            ft.Text(f"A: {msg['answer']}"),
                        ]
                    ),
                    bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
                    border_radius=5,
                    padding=10,
                )
            )
        if not self.chat_list.controls:
            self.chat_list.controls.append(
                ft.Text("No chat history yet.", italic=True)
            )

    def on_ask(self, _):
        query = self.query_field.value
        if not query or self.streaming:
            return

        self.streaming = True
        self.ask_button.disabled = True
        self.ask_progress.visible = True
        self.query_field.value = ""
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

        def stream_task():
            nonlocal full_answer
            try:
                for token in ask_rag_stream(query):
                    full_answer += token
                    answer_text.value = f"A: {full_answer}"
                    self.page.update()
            except Exception as e:
                answer_text.value = f"A: Error: {e}"
                self.page.update()

            save_chat(query, full_answer)
            self.streaming = False
            self.ask_button.disabled = False
            self.ask_progress.visible = False
            self.page.update()

        threading.Thread(target=stream_task, daemon=True).start()
