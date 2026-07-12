import os


class ModelNameExtractor:
    """
    Accepts a MODEL pass-through and an optional model path string.
    Extracts the bare filename (no directory, no extension) and returns it
    alongside the model so it can feed FilenameFormatter or a text display node.

    The model_path string can come from any source — a Primitive String widget,
    a CheckpointLoaderSimple 'model_name' widget linked via text, etc.
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
            },
            "optional": {
                "model_path": ("STRING", {
                    "default": "",
                    "tooltip": (
                        "Full or partial path to the model file. "
                        "e.g. 'checkpoints/my_model.safetensors' → 'my_model'"
                    ),
                }),
            },
        }

    RETURN_TYPES  = ("MODEL", "STRING")
    RETURN_NAMES  = ("model",  "model_name")
    FUNCTION      = "execute"
    CATEGORY      = "workflow-utils/model"
    DESCRIPTION   = (
        "Extracts the bare filename (no path, no extension) from a model path string "
        "and passes the model through unchanged."
    )

    def execute(self, model, model_path=""):
        if model_path:
            name = os.path.splitext(os.path.basename(model_path))[0]
        else:
            # Attempt to read from model metadata as a best-effort fallback
            name = ""
            for attr in ("filename", "model_name", "name"):
                candidate = getattr(model, attr, None) or getattr(
                    getattr(model, "model", None), attr, None
                )
                if candidate:
                    name = os.path.splitext(os.path.basename(str(candidate)))[0]
                    break
            if not name:
                name = "unknown_model"

        return (model, name)


NODE_CLASS_MAPPINGS        = {"ModelNameExtractor": ModelNameExtractor}
NODE_DISPLAY_NAME_MAPPINGS = {"ModelNameExtractor": "Model Name Extractor"}
