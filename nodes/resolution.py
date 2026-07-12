import math
import random
import torch
import comfy.model_management

MAX_RESOLUTION = 32768
MAX_SEED = 2**32 - 1

ASPECT_RATIO_PRESETS = {
    "custom":              None,
    "1:1  square 1024":    (1024, 1024),
    "3:4  portrait 768":   (768,  1024),
    "4:3  landscape 768":  (1024, 768),
    "2:3  portrait 832":   (832,  1216),
    "3:2  landscape 832":  (1216, 832),
    "9:16 portrait 576":   (576,  1024),
    "16:9 landscape 576":  (1024, 576),
    "9:16 portrait 768":   (768,  1344),
    "16:9 landscape 768":  (1344, 768),
    "5:8  portrait":       (640,  1024),
    "8:5  landscape":      (1024, 640),
    "21:9 cinematic":      (1024, 436),
    "3:4  portrait 896":   (896,  1152),
    "4:3  landscape 896":  (1152, 896),
    "1:1  square 1224":    (1224, 1224),
    "3:4  portrait 1224":  (1224, 1632),
    "4:3  landscape 1224": (1632, 1224),
}
SEED_MODES = ["fixed", "randomize"]


class ScaledResolution:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "aspect_ratio":    (list(ASPECT_RATIO_PRESETS.keys()),),
                "width":           ("INT",     {"default": 1024, "min": 1,    "max": MAX_RESOLUTION, "step": 8,
                                                "tooltip": "Used only when aspect_ratio is 'custom'."}),
                "height":          ("INT",     {"default": 1024, "min": 1,    "max": MAX_RESOLUTION, "step": 8,
                                                "tooltip": "Used only when aspect_ratio is 'custom'."}),
                "swap_dimensions": ("BOOLEAN", {"default": False,
                                                "tooltip": "Swap width and height (portrait ↔ landscape)."}),
                "upscale_factor":  ("FLOAT",   {"default": 4.0,  "min": 0.01, "max": 64.0,           "step": 0.01,
                                                "tooltip": "Scale multiplier for scaled_width / scaled_height."}),
                "batch_size":      ("INT",     {"default": 1,    "min": 1,    "max": 64,              "step": 1}),
                "seed":            ("INT",     {"default": 0,    "min": 0,    "max": MAX_SEED}),
                "seed_mode":       (SEED_MODES, {"default": "fixed"}),
            }
        }

    RETURN_TYPES  = ("INT", "INT", "INT", "INT", "INT", "INT", "LATENT")
    RETURN_NAMES  = ("width", "height", "scaled_width", "scaled_height", "batch_size", "seed", "latent")
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/resolution"
    DESCRIPTION   = (
        "All-in-one resolution node. Selects a preset aspect ratio (or custom W×H), "
        "computes upscaler target dims (width×upscale_factor), forwards batch_size and seed, "
        "and emits an empty latent — replacing EmptyLatentImage."
    )

    @classmethod
    def IS_CHANGED(cls, seed_mode, **kwargs):
        if seed_mode == "randomize":
            return float("nan")
        return False

    def execute(self, aspect_ratio, width, height, swap_dimensions,
                upscale_factor, batch_size, seed, seed_mode):
        preset = ASPECT_RATIO_PRESETS.get(aspect_ratio)
        if preset is None and aspect_ratio != "custom":
            raise ValueError(
                f"[ScaledResolution] Unknown aspect_ratio '{aspect_ratio}'. "
                f"Valid: {list(ASPECT_RATIO_PRESETS.keys())}"
            )
        if preset is not None:
            width, height = preset
        if swap_dimensions:
            width, height = height, width
        if width <= 0:
            raise ValueError(f"[ScaledResolution] width must be > 0, got {width}")
        if height <= 0:
            raise ValueError(f"[ScaledResolution] height must be > 0, got {height}")
        if not math.isfinite(upscale_factor) or upscale_factor <= 0:
            raise ValueError(f"[ScaledResolution] upscale_factor must be a positive finite number, got {upscale_factor}")

        scaled_width  = int(round(width  * upscale_factor))
        scaled_height = int(round(height * upscale_factor))

        for label, value, base, factor in (
            ("scaled_width",  scaled_width,  width,  upscale_factor),
            ("scaled_height", scaled_height, height, upscale_factor),
        ):
            if value > MAX_RESOLUTION:
                raise ValueError(
                    f"[ScaledResolution] {label} {value} exceeds MAX_RESOLUTION {MAX_RESOLUTION}. "
                    f"Reduce base ({base}) or upscale_factor ({factor})."
                )
            if value <= 0:
                raise ValueError(
                    f"[ScaledResolution] {label} rounded to {value}. "
                    f"Increase base ({base}) or upscale_factor ({factor})."
                )

        if batch_size < 1:
            raise ValueError(f"[ScaledResolution] batch_size must be >= 1, got {batch_size}")

        if seed_mode == "randomize":
            out_seed = random.randint(0, MAX_SEED)
        elif seed_mode == "fixed":
            if not (0 <= seed <= MAX_SEED):
                raise ValueError(f"[ScaledResolution] seed {seed} out of range [0, {MAX_SEED}].")
            out_seed = seed
        else:
            raise ValueError(f"[ScaledResolution] Unknown seed_mode '{seed_mode}'. Valid: {SEED_MODES}")

        device = comfy.model_management.intermediate_device()
        latent = torch.zeros([batch_size, 4, height // 8, width // 8], device=device)

        return (width, height, scaled_width, scaled_height, batch_size, out_seed, {"samples": latent})


NODE_CLASS_MAPPINGS        = {"ScaledResolution": ScaledResolution}
NODE_DISPLAY_NAME_MAPPINGS = {"ScaledResolution": "Scaled Resolution"}
