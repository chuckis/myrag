import flet as ft

from storage import init_db, list_worlds, get_world
from views.add_view import AddView
from views.chat_view import ChatView
from views.settings_view import SettingsView
from views.worlds_view import WorldsView


class MyRagApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.title = "MyRag"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        init_db()

        self.add_view = AddView(page)
        self.chat_view = ChatView(page)
        self.settings_view = SettingsView(page)
        self.worlds_view = WorldsView(page, on_enter_world=self.enter_world)

        self.world_menu = ft.PopupMenuButton(
            content=ft.Text("Worlds", size=14),
            items=[],
            tooltip="Switch world",
        )

        self.back_btn = ft.IconButton(
            icon=ft.Icons.ARROW_BACK,
            tooltip="Back to worlds",
            on_click=lambda _: self._show_world_selection(),
            visible=False,
        )

        self.page.appbar = ft.AppBar(
            title=ft.Text("MyRag"),
            actions=[
                self.back_btn,
                self.world_menu,
                ft.IconButton(
                    icon=ft.Icons.SETTINGS,
                    tooltip="Settings",
                    on_click=lambda _: self.settings_view.open(),
                ),
                ft.IconButton(
                    icon=ft.Icons.DARK_MODE,
                    tooltip="Toggle theme",
                    on_click=self.toggle_theme,
                ),
            ],
        )

        self._show_world_selection()

    def toggle_theme(self, _):
        self.page.theme_mode = (
            ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.page.update()

    def _show_world_selection(self):
        self.page.session.store.set("world_id", 0)
        self._update_world_menu()
        self.back_btn.visible = False
        self.page.appbar.title = ft.Text("MyRag")
        self.page.clean()
        self.page.add(self.worlds_view.build())
        self.page.update()

    def _update_world_menu(self):
        worlds = list_worlds()
        current_id = self._current_world_id()

        current_name = "Worlds"
        items = []
        for w in worlds:
            is_current = w["id"] == current_id
            if is_current:
                current_name = w["name"]
            label = f"  {w['name']}  " if not is_current else f"✓ {w['name']}  "
            items.append(
                ft.PopupMenuItem(
                    content=ft.Text(label),
                    on_click=lambda _, wid=w["id"]: self.enter_world(wid),
                )
            )
        items.append(ft.PopupMenuItem(content=ft.Divider()))
        items.append(
            ft.PopupMenuItem(
                content=ft.Text("Manage worlds..."),
                on_click=lambda _: self._show_world_selection(),
            )
        )
        self.world_menu.content = ft.Text(current_name, size=14)
        self.world_menu.items = items
        self.world_menu.visible = len(worlds) > 0

    def _current_world_id(self) -> int | None:
        return self.page.session.store.get("world_id")

    def enter_world(self, world_id: int):
        self.page.session.store.set("world_id", world_id)
        world = get_world(world_id)
        world_name = world["name"] if world else "?"
        self.page.title = f"MyRag — {world_name}"
        self.page.appbar.title = ft.Text(f"MyRag — {world_name}")
        self.back_btn.visible = True
        self._update_world_menu()

        self.add_view = AddView(self.page)
        self.chat_view = ChatView(self.page)

        tab_bar = ft.TabBar(
            tabs=[
                ft.Tab(label="Add", icon=ft.Icons.ADD),
                ft.Tab(label="Chat", icon=ft.Icons.CHAT),
            ],
        )
        tab_view = ft.TabBarView(
            expand=True,
            controls=[
                self.add_view.build(),
                self.chat_view.build(),
            ],
        )

        content = ft.Column(
            expand=True,
            controls=[tab_bar, tab_view],
        )

        tabs = ft.Tabs(
            selected_index=0,
            expand=True,
            animation_duration=300,
            on_change=lambda e: self.chat_view.load_chat_list() if int(e.data) == 1 else None,
            length=2,
            content=content,
        )

        self.page.clean()
        self.page.add(tabs)
        self.add_view.refresh_status()
        self.page.update()


def main(page: ft.Page):
    MyRagApp(page)


import os

if os.environ.get("MYRAG_WEB"):
    ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=8080)
else:
    ft.run(main)