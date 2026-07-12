import random as _random

MAX_SEED = 2**32 - 1
SEED_MODES = ["fixed", "randomize"]


class RandomTextPicker:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed":      ("INT",    {"default": 0, "min": 0, "max": MAX_SEED}),
                "seed_mode": (SEED_MODES, {"default": "fixed"}),
            },
            "optional": {
                "text1": ("STRING", {"forceInput": True}),
                "text2": ("STRING", {"forceInput": True}),
                "text3": ("STRING", {"forceInput": True}),
                "text4": ("STRING", {"forceInput": True}),
                "text5": ("STRING", {"forceInput": True}),
                "text6": ("STRING", {"forceInput": True}),
                "text7": ("STRING", {"forceInput": True}),
                "text8": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES  = ("STRING", "INT")
    RETURN_NAMES  = ("text",   "index")
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/text"
    DESCRIPTION   = (
        "Randomly picks one of up to 8 connected STRING inputs. "
        "Only connected (non-None) slots participate. "
        "'index' is 1-based and tells you which slot was chosen."
    )

    @classmethod
    def IS_CHANGED(cls, seed_mode, **kwargs):
        if seed_mode == "randomize":
            return float("nan")
        return False

    def execute(self, seed, seed_mode,
                text1=None, text2=None, text3=None, text4=None,
                text5=None, text6=None, text7=None, text8=None):
        candidates = [
            (i + 1, t)
            for i, t in enumerate([text1, text2, text3, text4,
                                    text5, text6, text7, text8])
            if t is not None
        ]

        if not candidates:
            print("[RandomTextPicker] No inputs connected — returning empty string.")
            return ("", 0)

        if seed_mode == "randomize":
            out_seed = _random.randint(0, MAX_SEED)
        else:
            out_seed = seed

        rng = _random.Random(out_seed)
        idx, text = rng.choice(candidates)

        print(f"[RandomTextPicker] seed={out_seed} → picked slot {idx} of {len(candidates)}")
        return (text, idx)


NODE_CLASS_MAPPINGS        = {"RandomTextPicker": RandomTextPicker}
NODE_DISPLAY_NAME_MAPPINGS = {"RandomTextPicker": "Random Text Picker"}
