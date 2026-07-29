import flet as ft

from storage import list_worlds, create_world, delete_world, get_world_stats


class WorldsView:
    def __init__(self, page: ft.Page, on_enter_world):
        self.page = page
        self.on_enter_world = on_enter_world
        self.grid = ft.GridView(
            runs_count=3,
            max_extent=250,
            spacing=15,
            run_spacing=15,
            expand=True,
        )

    def build(self) -> ft.Control:
        self._load_grid()
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text("My Worlds", size=28, weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "+ New World",
                            icon=ft.Icons.ADD,
                            on_click=self.on_create_world,
                        ),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(self.grid, expand=True, padding=ft.Padding(0, 20, 0, 0)),
            ],
            spacing=10,
            expand=True,
        )

    def _load_grid(self):
        self.grid.controls.clear()
        worlds = list_worlds()
        for w in worlds:
            stats = get_world_stats(w["id"])
            card = self._build_card(w, stats)
            self.grid.controls.append(card)

    def _build_card(self, world: dict, stats: dict) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Icon(ft.Icons.PUBLIC, size=28),
                            ft.Text(
                                world["name"],
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                expand=True,
                                no_wrap=True,
                                overflow=ft.TextOverflow.ELLIPSIS,
                            ),
                        ],
                        spacing=8,
                    ),
                    ft.Text(
                        world["description"] or "No description",
                        size=13,
                        color=ft.Colors.OUTLINE,
                        no_wrap=True,
                        overflow=ft.TextOverflow.ELLIPSIS,
                    ),
                    ft.Divider(height=8),
                    ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(str(stats["chat_count"]), size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text("Chats", size=11, color=ft.Colors.OUTLINE),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Column(
                                [
                                    ft.Text(str(stats["staging_total"]), size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text("Sources", size=11, color=ft.Colors.OUTLINE),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                            ft.Column(
                                [
                                    ft.Text(str(stats["staging_pending"]), size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text("Pending", size=11, color=ft.Colors.OUTLINE),
                                ],
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_AROUND,
                    ),
                    ft.Row(
                        [
                            ft.ElevatedButton(
                                "Enter",
                                icon=ft.Icons.ARROW_FORWARD,
                                expand=True,
                                on_click=lambda _, wid=world["id"]: self.on_enter_world(wid),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_size=18,
                                tooltip="Delete world",
                                on_click=lambda _, wid=world["id"]: self._confirm_delete(wid, world["name"]),
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=6,
                horizontal_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=12,
            padding=16,
            ink=True,
            on_click=lambda _, wid=world["id"]: self.on_enter_world(wid),
        )

    def on_create_world(self, _):
        name_field = ft.TextField(label="World name", autofocus=True, expand=True)
        desc_field = ft.TextField(label="Description", multiline=True, min_lines=2, max_lines=4, expand=True)

        def close(e):
            self.page.pop_dialog()

        def save(e):
            name = name_field.value
            if not name:
                return
            create_world(name, desc_field.value or "")
            self.page.pop_dialog()
            self._load_grid()
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Create new world"),
            content=ft.Column([name_field, desc_field], spacing=10, tight=True),
            actions=[
                ft.TextButton("Cancel", on_click=close),
                ft.TextButton("Create", on_click=save),
            ],
        )
        self.page.show_dialog(dlg)

    def _confirm_delete(self, world_id: int, name: str):
        def close(e):
            self.page.pop_dialog()

        def confirm(e):
            delete_world(world_id)
            self.page.pop_dialog()
            self._load_grid()
            self.page.update()

        dlg = ft.AlertDialog(
            title=ft.Text("Delete world"),
            content=ft.Text(f'Delete "{name}" and all its data (sources, chats, index)?'),
            actions=[
                ft.TextButton("Cancel", on_click=close),
                ft.TextButton("Delete", on_click=confirm),
            ],
        )
        self.page.show_dialog(dlg)