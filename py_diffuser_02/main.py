"""Application entry point."""

from .model_manager import ModelManager
from .generator import GenerationService
from .ui import PyDiffuserApp, create_app


def main():
    root = create_app()

    # Tkinter callbacks must be supplied to the model/generator managers.
    app_holder = {}

    def log_func(message):
        app_holder["app"].log(message)

    def set_status(message):
        app_holder["app"].set_status(message)

    model_manager = ModelManager(log_func, set_status)
    generation_service = GenerationService(
        model_manager,
        log_func,
        set_status,
    )

    app_holder["app"] = PyDiffuserApp(
        root,
        model_manager,
        generation_service,
    )
    app_holder["app"].start_model_loading()

    root.mainloop()


if __name__ == "__main__":
    main()
