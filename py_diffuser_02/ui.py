"""Tkinter desktop interface."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from . import config


class PyDiffuserApp:
    """Main desktop application window."""

    def __init__(self, root, model_manager, generation_service):
        self.root = root
        self.model_manager = model_manager
        self.generation_service = generation_service

        self.root.title(f"{config.APP_NAME} {config.APP_VERSION}")
        self.root.geometry("780x580")
        self.root.minsize(680, 500)

        self.status_var = tk.StringVar(value="Initializing...")
        self.video_mode_var = tk.BooleanVar(value=False)

        self.init_image_path = None
        self.init_image_label_var = tk.StringVar(
            value="No image selected (optional)"
        )

        self.build_ui()
        self.update_progressbar()

    def start_model_loading(self):
        """Start model loading after the application object is fully initialized."""
        self.model_manager.load_async()

    def build_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(
            main_frame,
            text=f"Prompt (max {config.MAX_PROMPT_CHARS} chars):",
        ).pack(anchor="w")

        self.prompt_var = tk.StringVar()
        self.prompt_entry = ttk.Entry(
            main_frame,
            textvariable=self.prompt_var,
        )
        self.prompt_entry.pack(fill="x", pady=5)
        self.prompt_entry.bind("<Return>", self.on_enter_pressed)

        ttk.Label(
            main_frame,
            text="Photorealistic generation is always enabled.",
        ).pack(anchor="w", pady=(0, 2))

        ttk.Checkbutton(
            main_frame,
            text="Generate video instead of image",
            variable=self.video_mode_var,
        ).pack(anchor="w", pady=(0, 5))

        upload_frame = ttk.Frame(main_frame)
        upload_frame.pack(fill="x", pady=(0, 5))

        ttk.Button(
            upload_frame,
            text="Load image for editing (optional)",
            command=self.on_load_image,
        ).pack(side="left")

        ttk.Label(
            upload_frame,
            textvariable=self.init_image_label_var,
        ).pack(side="left", padx=(8, 0))

        self.generate_button = ttk.Button(
            main_frame,
            text="Generate",
            command=self.on_generate,
        )
        self.generate_button.pack(pady=5)

        self.progress = ttk.Progressbar(
            main_frame,
            mode="determinate",
            maximum=100,
        )
        self.progress.pack(fill="x", pady=5)

        ttk.Label(
            main_frame,
            textvariable=self.status_var,
        ).pack(anchor="w", pady=(0, 5))

        ttk.Label(main_frame, text="Log:").pack(anchor="w")

        self.log_text = ScrolledText(
            main_frame,
            height=14,
            wrap="word",
        )
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")

    def set_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

    def log(self, text):
        def append():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", text + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        self.root.after(0, append)

    def on_load_image(self):
        path = filedialog.askopenfilename(
            title="Select image to edit",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.webp"),
                ("All files", "*.*"),
            ],
        )

        if not path:
            return

        self.init_image_path = path
        self.init_image_label_var.set(path.split("\\")[-1].split("/")[-1])
        self.log(f"Loaded init image for editing: {path}")

    def on_enter_pressed(self, event):
        self.on_generate()
        return "break"

    def on_generate(self):
        if self.generation_service.is_generating:
            return

        if not self.model_manager.loaded:
            if self.model_manager.error:
                messagebox.showerror(
                    "Model Error",
                    f"Could not load model:\n{self.model_manager.error}",
                )
            else:
                messagebox.showinfo(
                    "Please wait",
                    "Stable Diffusion is still loading.",
                )
            return

        prompt = self.prompt_var.get().strip()

        if not prompt:
            messagebox.showwarning("No prompt", "Please enter a prompt.")
            return

        if len(prompt) > config.MAX_PROMPT_CHARS:
            messagebox.showwarning(
                "Prompt too long",
                f"Prompt is {len(prompt)} characters. "
                f"Maximum is {config.MAX_PROMPT_CHARS}.",
            )
            return

        self.generate_button.config(state="disabled")

        if self.video_mode_var.get():
            if self.init_image_path:
                self.log("Note: the selected init image is ignored for video.")

            self.set_status("Starting video generation...")
            self.log(f'---\nNew VIDEO request: "{prompt}"')
            self.log(
                f"Frames: {config.VIDEO_NUM_FRAMES}, "
                f"FPS: {config.VIDEO_FPS}, "
                f"Resolution: {config.VIDEO_WIDTH}x{config.VIDEO_HEIGHT}"
            )

            self.generation_service.generate_video_async(
                prompt,
                self.on_generation_finished,
            )
        else:
            self.set_status("Starting image generation...")
            self.log(f'---\nNew IMAGE request: "{prompt}"')
            self.log(
                f"Base resolution: {config.BASE_WIDTH}x{config.BASE_HEIGHT}"
            )

            if config.UPSCALE_TO_4K:
                self.log(
                    f"Upscale target: "
                    f"{config.UPSCALE_WIDTH}x{config.UPSCALE_HEIGHT}"
                )

            self.generation_service.generate_image_async(
                prompt,
                self.on_generation_finished,
                self.init_image_path,
            )

    def on_generation_finished(self):
        self.root.after(
            0,
            lambda: self.generate_button.config(state="normal"),
        )

    def update_progressbar(self):
        self.progress["value"] = self.generation_service.progress["value"]
        self.root.after(100, self.update_progressbar)


def create_app():
    """Create the Tkinter root and application."""
    root = tk.Tk()
    return root
