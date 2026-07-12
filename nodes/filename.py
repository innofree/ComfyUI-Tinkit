import os
import re
from datetime import datetime

_VALID_KEYS = {"date", "model", "seed", "prefix", "suffix", "index"}


class FilenameFormatter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template":    ("STRING",  {"default": "{date}-{model}-{seed}", "multiline": False,
                                            "tooltip": "Keys: {date} {model} {seed} {prefix} {suffix} {index}"}),
                "seed":        ("INT",     {"default": 0, "min": 0, "max": 2**32 - 1}),
            },
            "optional": {
                "model_name":  ("STRING",  {"default": ""}),
                "prefix":      ("STRING",  {"default": ""}),
                "suffix":      ("STRING",  {"default": ""}),
                "index":       ("INT",     {"default": 0, "min": 0, "max": 99999}),
                "date_format": ("STRING",  {"default": "%Y%m%d",
                                            "tooltip": "strftime format string, e.g. %Y%m%d_%H%M%S"}),
            },
        }

    RETURN_TYPES  = ("STRING",)
    RETURN_NAMES  = ("filename",)
    FUNCTION      = "execute"
    CATEGORY      = "workflow-utils/io"
    DESCRIPTION   = (
        "Formats a filename string from a template. "
        "Available keys: {date}, {model}, {seed}, {prefix}, {suffix}, {index}."
    )

    def execute(self, template, seed, model_name="", prefix="", suffix="",
                index=0, date_format="%Y%m%d"):
        try:
            date_str = datetime.now().strftime(date_format)
        except Exception as e:
            raise ValueError(f"[FilenameFormatter] Invalid date_format '{date_format}': {e}")

        model_base = os.path.splitext(os.path.basename(model_name))[0] if model_name else "model"

        try:
            result = template.format(
                date=date_str,
                model=model_base,
                seed=seed,
                prefix=prefix,
                suffix=suffix,
                index=index,
            )
        except KeyError as e:
            raise ValueError(
                f"[FilenameFormatter] Unknown template key {e}. "
                f"Valid keys: {{{', '.join(sorted(_VALID_KEYS))}}}"
            )
        except Exception as e:
            raise ValueError(f"[FilenameFormatter] Template error: {e}")

        # Strip characters invalid in most filesystems
        result = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', result)
        result = result.strip('. ')

        if not result:
            raise ValueError("[FilenameFormatter] Template produced an empty filename after sanitization.")

        return (result,)


NODE_CLASS_MAPPINGS        = {"FilenameFormatter": FilenameFormatter}
NODE_DISPLAY_NAME_MAPPINGS = {"FilenameFormatter": "Filename Formatter"}
