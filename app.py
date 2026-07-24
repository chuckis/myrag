import flet as ft

from storage import init_db
from views.add_view import AddView
from views.chat_view import ChatView


def main(page: ft.Page):
    page.title = "MyRag"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    init_db()

    add_view = AddView(page)
    chat_view = ChatView(page)

    def toggle_theme(_):
        page.theme_mode = (
            ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()

    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        on_change=lambda e: chat_view.load_history() if int(e.data) == 1 else None,
        tabs=[
            ft.Tab(
                text="Add",
                icon=ft.Icons.ADD,
                content=add_view.build(),
            ),
            ft.Tab(
                text="Chat",
                icon=ft.Icons.CHAT,
                content=chat_view.build(),
            ),
        ],
        expand=True,
    )

    page.appbar = ft.AppBar(
        title=ft.Text("MyRag"),
        actions=[
            ft.IconButton(
                icon=ft.Icons.DARK_MODE,
                tooltip="Toggle theme",
                on_click=toggle_theme,
            ),
        ],
    )

    page.add(tabs)
    add_view.refresh_status()


import os

if os.environ.get("MYRAG_WEB"):
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8080)
else:
    ft.app(target=main)
