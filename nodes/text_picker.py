import random as _random

MAX_SEED = 2**32 - 1
SEED_MODES = ["fixed", "randomize"]


class RandomTextPicker:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed":      ("INT",      {"default": 0, "min": 0, "max": MAX_SEED}),
                "seed_mode": (SEED_MODES, {"default": "fixed"}),
            },
            "optional": {
                # text_0 is the seed slot; JS auto-appends text_1, text_2, … as needed
                "text_0": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES  = ("STRING", "INT")
    RETURN_NAMES  = ("text",   "index")
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/text"
    DESCRIPTION   = (
        "Randomly picks one of N connected STRING inputs. "
        "A new slot appears automatically as each is connected. "
        "'index' is 1-based (text_0 → 1)."
    )

    @classmethod
    def IS_CHANGED(cls, seed_mode, **kwargs):
        if seed_mode == "randomize":
            return float("nan")
        return False

    @classmethod
    def VALIDATE_INPUTS(cls, **kwargs):
        # Accept dynamically-added text_N inputs not listed in INPUT_TYPES
        return True

    def execute(self, seed, seed_mode, **kwargs):
        candidates = sorted(
            ((int(k.split("_")[1]) + 1, v)
             for k, v in kwargs.items()
             if k.startswith("text_") and v is not None),
            key=lambda x: x[0],
        )

        if not candidates:
            print("[RandomTextPicker] No inputs connected — returning empty string.")
            return ("", 0)

        if seed_mode == "randomize":
            out_seed = _random.randint(0, MAX_SEED)
        else:
            out_seed = seed

        rng = _random.Random(out_seed)
        idx, text = rng.choice(candidates)

        print(f"[RandomTextPicker] seed={out_seed} → slot {idx} / {len(candidates)} connected")
        return (text, idx)


NODE_CLASS_MAPPINGS        = {"RandomTextPicker": RandomTextPicker}
NODE_DISPLAY_NAME_MAPPINGS = {"RandomTextPicker": "Random Text Picker"}
