import flet as ft

from storage import get_all_settings, set_setting

OPENROUTER_MODELS = [
    "qwen/qwen-2.5-72b-instruct",
    "qwen/qwen-2.5-32b-instruct",
    "anthropic/claude-3.5-sonnet",
    "openai/gpt-4o",
    "openai/gpt-4o-mini",
    "google/gemini-2.0-flash-001",
    "deepseek/deepseek-chat",
    "meta-llama/llama-3.3-70b-instruct",
    "microsoft/phi-3-medium-128k-instruct",
    "custom...",
]


class SettingsView:
    def __init__(self, page: ft.Page):
        self.page = page

    def open(self):
        settings = get_all_settings()
        api_key = settings.get("openrouter_api_key", "")
        current_model = settings.get("openrouter_model", "")
        force_local = settings.get("force_local", "0") == "1"

        api_field = ft.TextField(
            label="OpenRouter API Key",
            value=api_key,
            password=True,
            can_reveal_password=True,
            expand=True,
        )

        model_dropdown = ft.Dropdown(
            label="Model",
            value=current_model if current_model in OPENROUTER_MODELS else "custom...",
            options=[ft.dropdown.Option(m) for m in OPENROUTER_MODELS],
            expand=True,
        )

        custom_model_field = ft.TextField(
            label="Custom model name",
            value=current_model if current_model not in OPENROUTER_MODELS else "",
            expand=True,
            visible=(current_model not in OPENROUTER_MODELS),
        )

        def on_model_change(e):
            is_custom = model_dropdown.value == "custom..."
            custom_model_field.visible = is_custom
            if is_custom and custom_model_field.value:
                pass
            elif not is_custom and not is_custom:
                pass
            self.page.update()

        model_dropdown.on_change = on_model_change

        force_local_switch = ft.Switch(
            label="Force local LLM only",
            value=force_local,
        )

        def save(_):
            selected_model = custom_model_field.value if custom_model_field.visible else model_dropdown.value
            if selected_model == "custom...":
                selected_model = ""
            set_setting("openrouter_api_key", api_field.value)
            set_setting("openrouter_model", selected_model)
            set_setting("force_local", "1" if force_local_switch.value else "0")
            self.page.close_dialog()

        dlg = ft.AlertDialog(
            title=ft.Text("Settings"),
            content=ft.Column(
                [
                    api_field,
                    model_dropdown,
                    custom_model_field,
                    ft.Divider(),
                    force_local_switch,
                ],
                width=400,
                spacing=10,
                scroll=ft.ScrollMode.AUTO,
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda _: self.page.close_dialog()),
                ft.TextButton("Save", on_click=save),
            ],
        )

        self.page.show_dialog(dlg)
