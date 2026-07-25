import flet as ft

from storage import init_db
from views.add_view import AddView
from views.chat_view import ChatView
from views.settings_view import SettingsView


def main(page: ft.Page):
    page.title = "MyRag"
    page.theme_mode = ft.ThemeMode.LIGHT
    init_db()

    add_view = AddView(page)
    chat_view = ChatView(page)

    def toggle_theme(_):
        page.theme_mode = (
            ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        page.update()

    content_row = ft.Column(
        expand=True,
        controls=[
            ft.TabBar(
                tabs=[
                    ft.Tab(label="Add", icon=ft.Icons.ADD),
                    ft.Tab(label="Chat", icon=ft.Icons.CHAT),
                ],
            ),
            ft.TabBarView(
                expand=True,
                controls=[
                    add_view.build(),
                    chat_view.build(),
                ],
            ),
        ],
    )

    tabs = ft.Tabs(
        selected_index=0,
        expand=True,
        animation_duration=300,
        on_change=lambda e: chat_view.load_chat_list() if int(e.data) == 1 else None,
        length=2,
        content=content_row,
    )

    settings_view = SettingsView(page)

    page.appbar = ft.AppBar(
        title=ft.Text("MyRag"),
        actions=[
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                tooltip="Settings",
                on_click=lambda _: settings_view.open(),
            ),
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
    ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8080)
else:
    ft.run(main)
