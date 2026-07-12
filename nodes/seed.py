import collections

MAX_SEED = 2**32 - 1
_DEFAULT_HISTORY = 10


class SeedHistory:
    """
    Tracks seeds across successive queue runs using class-level storage
    (survives individual queue items but resets on ComfyUI restart).

    On every execution it:
      1. Records the incoming seed into the history deque.
      2. Outputs the current seed plus up to two previous seeds.
      3. Emits the full history list as a newline-separated string for display.
    """

    _history: collections.deque = collections.deque(maxlen=_DEFAULT_HISTORY)

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "seed":         ("INT", {"default": 0, "min": 0, "max": MAX_SEED,
                                         "forceInput": True}),
                "history_size": ("INT", {"default": _DEFAULT_HISTORY, "min": 1, "max": 100, "step": 1,
                                          "tooltip": "Maximum number of past seeds to remember."}),
            },
        }

    RETURN_TYPES  = ("INT",  "INT",       "INT",       "STRING")
    RETURN_NAMES  = ("seed", "prev_seed", "prev2_seed", "history")
    OUTPUT_NODE   = True
    FUNCTION      = "execute"
    CATEGORY      = "workflow-utils/seed"
    DESCRIPTION   = (
        "Records the incoming seed into a persistent per-session history. "
        "Outputs the current seed, the previous seed, the seed before that, "
        "and the full history as a text string for a display node."
    )

    @classmethod
    def IS_CHANGED(cls, seed, **kwargs):
        # Always re-execute so history updates every queue cycle
        return float("nan")

    def execute(self, seed: int, history_size: int):
        if not (0 <= seed <= MAX_SEED):
            raise ValueError(f"[SeedHistory] seed {seed} out of range [0, {MAX_SEED}].")
        if history_size < 1:
            raise ValueError(f"[SeedHistory] history_size must be >= 1, got {history_size}.")

        # Resize the deque if the user changed history_size
        if SeedHistory._history.maxlen != history_size:
            SeedHistory._history = collections.deque(SeedHistory._history, maxlen=history_size)

        SeedHistory._history.appendleft(seed)

        history_list = list(SeedHistory._history)
        prev_seed  = history_list[1] if len(history_list) > 1 else seed
        prev2_seed = history_list[2] if len(history_list) > 2 else seed

        history_str = "\n".join(str(s) for s in history_list)

        return {
            "ui":     {"text": [history_str]},
            "result": (seed, prev_seed, prev2_seed, history_str),
        }


NODE_CLASS_MAPPINGS        = {"SeedHistory": SeedHistory}
NODE_DISPLAY_NAME_MAPPINGS = {"SeedHistory": "Seed History"}
