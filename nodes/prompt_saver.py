import os

DEFAULT_PATH = "models/wildcards/saved_prompts.txt"


class PromptSaver:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text":       ("STRING", {"forceInput": True}),
                "file_path":  ("STRING", {"default": DEFAULT_PATH, "multiline": False,
                                          "tooltip": "Absolute path or relative to ComfyUI root. One prompt per line."}),
            },
            "optional": {
                "enabled":    ("BOOLEAN", {"default": True,
                                           "tooltip": "Disable to pass through without saving."}),
                "skip_duplicate": ("BOOLEAN", {"default": True,
                                               "tooltip": "Skip if identical to the last saved line."}),
            },
        }

    RETURN_TYPES  = ("STRING",)
    RETURN_NAMES  = ("text",)
    OUTPUT_NODE   = True
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/io"
    DESCRIPTION   = (
        "Appends the incoming prompt to a .txt file (one line per prompt). "
        "Wire between ShowText and your sampler's text input. "
        "The saved file can be used directly as a wildcard source."
    )

    def execute(self, text, file_path, enabled=True, skip_duplicate=True):
        if not enabled or not text.strip():
            return {"ui": {"text": ["skipped"]}, "result": (text,)}

        # Resolve relative paths from ComfyUI root
        if not os.path.isabs(file_path):
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(root, file_path)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        prompt = text.strip()

        if skip_duplicate and os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
            if lines and lines[-1].strip() == prompt:
                msg = f"duplicate skipped → {os.path.basename(file_path)}"
                return {"ui": {"text": [msg]}, "result": (text,)}

        with open(file_path, "a", encoding="utf-8") as f:
            f.write(prompt + "\n")

        with open(file_path, "r", encoding="utf-8") as f:
            count = sum(1 for line in f if line.strip())

        msg = f"saved ({count} prompts) → {os.path.basename(file_path)}"
        print(f"[PromptSaver] {msg}")
        return {"ui": {"text": [msg]}, "result": (text,)}


NODE_CLASS_MAPPINGS        = {"PromptSaver": PromptSaver}
NODE_DISPLAY_NAME_MAPPINGS = {"PromptSaver": "Prompt Saver"}
