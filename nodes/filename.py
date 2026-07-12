import os
import re
from datetime import datetime

_VALID_KEYS = {"date", "model", "seed", "prefix", "suffix", "index"}
_KEY_PATTERN = re.compile(r'%(\w+)%')


class FilenameFormatter:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "template":    ("STRING",  {"default": "image/%date%/%model%-seed%seed%", "multiline": False,
                                            "tooltip": "Variables: %date% %model% %seed% %prefix% %suffix% %index%  |  Use / for subfolders."}),
                "seed":        ("INT",     {"default": 0, "min": 0, "max": 2**32 - 1}),
            },
            "optional": {
                "model_name":  ("STRING",  {"default": ""}),
                "prefix":      ("STRING",  {"default": ""}),
                "suffix":      ("STRING",  {"default": ""}),
                "index":       ("INT",     {"default": 0, "min": 0, "max": 99999}),
                "date_format": ("STRING",  {"default": "%Y-%m-%d",
                                            "tooltip": "strftime format, e.g. %Y-%m-%d or %Y%m%d_%H%M%S"}),
            },
        }

    RETURN_TYPES  = ("STRING",)
    RETURN_NAMES  = ("filename",)
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/io"
    DESCRIPTION   = (
        "Formats a filename/path from a template using %variable% syntax. "
        "Variables: %date%, %model%, %seed%, %prefix%, %suffix%, %index%.  "
        "Use / in the template to create subfolders (e.g. image/%date%/%model%-seed%seed%)."
    )

    def execute(self, template, seed, model_name="", prefix="", suffix="",
                index=0, date_format="%Y-%m-%d"):
        try:
            date_str = datetime.now().strftime(date_format)
        except Exception as e:
            raise ValueError(f"[FilenameFormatter] Invalid date_format '{date_format}': {e}")

        model_base = os.path.splitext(os.path.basename(model_name))[0] if model_name else "model"

        values = {
            "date":   date_str,
            "model":  model_base,
            "seed":   str(seed),
            "prefix": prefix,
            "suffix": suffix,
            "index":  str(index),
        }

        def _replace(m):
            key = m.group(1).lower()
            if key not in _VALID_KEYS:
                valid = "  ".join(f"%{k}%" for k in sorted(_VALID_KEYS))
                raise ValueError(
                    f"[FilenameFormatter] Unknown variable '%{m.group(1)}%'. "
                    f"Valid: {valid}"
                )
            return values[key]

        try:
            result = _KEY_PATTERN.sub(_replace, template)
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"[FilenameFormatter] Template error: {e}")

        # Sanitize per-segment (allow / as subfolder separator, strip OS-invalid chars)
        segments = result.split("/")
        segments = [re.sub(r'[<>:"|?*\\\x00-\x1f]', '_', s).strip('. ') for s in segments]
        result = "/".join(s for s in segments if s)

        if not result:
            raise ValueError("[FilenameFormatter] Template produced an empty filename after sanitization.")

        return (result,)


NODE_CLASS_MAPPINGS        = {"FilenameFormatter": FilenameFormatter}
NODE_DISPLAY_NAME_MAPPINGS = {"FilenameFormatter": "Filename Formatter"}
