import math
import random
import torch
import comfy.model_management

MAX_RESOLUTION = 32768
MAX_SEED = 2**32 - 1

# Preset keys embed exact W×H and target model family for at-a-glance UX.
# Rename note: old names (e.g. "3:2  landscape 832") map to the new equivalents below.
ASPECT_RATIO_PRESETS = {
    "custom":                            None,
    "1:1  square   1024×1024  SDXL":    (1024, 1024),
    "3:4  portrait  768×1024  SDXL":    (768,  1024),
    "4:3  landscape 1024×768  SDXL":    (1024, 768),
    "2:3  portrait  832×1216  SDXL":    (832,  1216),
    "3:2  landscape 1216×832  SDXL":    (1216, 832),
    "9:16 portrait  576×1024  SDXL":    (576,  1024),
    "16:9 landscape 1024×576  SDXL":    (1024, 576),
    "9:16 portrait  768×1344  SDXL":    (768,  1344),
    "16:9 landscape 1344×768  SDXL":    (1344, 768),
    "5:8  portrait  640×1024  SDXL":    (640,  1024),
    "8:5  landscape 1024×640  SDXL":    (1024, 640),
    "21:9 cinematic 1024×440  SDXL":    (1024, 440),
    "3:4  portrait  896×1152  SDXL":    (896,  1152),
    "4:3  landscape 1152×896  SDXL":    (1152, 896),
    "1:1  square   1224×1224  Flux":    (1224, 1224),
    "3:4  portrait 1224×1632  Flux":    (1224, 1632),
    "4:3  landscape 1632×1224  Flux":   (1632, 1224),
}
SEED_MODES = ["fixed", "randomize"]


class ScaledResolution:
    def __init__(self):
        self.device = comfy.model_management.intermediate_device()

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "aspect_ratio":    (list(ASPECT_RATIO_PRESETS.keys()),),
                "width":           ("INT",   {"default": 1024, "min": 1,    "max": MAX_RESOLUTION, "step": 8,
                                              "tooltip": "Used only when aspect_ratio is 'custom'."}),
                "height":          ("INT",   {"default": 1024, "min": 1,    "max": MAX_RESOLUTION, "step": 8,
                                              "tooltip": "Used only when aspect_ratio is 'custom'."}),
                "prescale_factor": ("FLOAT", {"default": 1.0,  "min": 0.01, "max": 8.0,   "step": 0.01,
                                              "tooltip": "Scales base W×H before upscale factors; snapped to 8px."}),
                "upscale_factor":  ("FLOAT", {"default": 4.0,  "min": 0.01, "max": 64.0,  "step": 0.01,
                                              "tooltip": "Primary upscale multiplier → scaled_width / scaled_height."}),
                "upscale_factor2": ("FLOAT", {"default": 2.0,  "min": 0.01, "max": 64.0,  "step": 0.01,
                                              "tooltip": "Secondary upscale multiplier → scaled_width2 / scaled_height2."}),
                "batch_size":      ("INT",   {"default": 1,    "min": 1,    "max": 64,     "step": 1}),
                "seed":            ("INT",   {"default": 0,    "min": 0,    "max": MAX_SEED}),
                "seed_mode":       (SEED_MODES, {"default": "fixed"}),
                "swap_dimensions": ("BOOLEAN", {"default": False,
                                                "tooltip": "Swap width ↔ height (portrait ↔ landscape)."}),
            }
        }

    RETURN_TYPES  = ("INT", "INT", "INT", "INT", "INT", "INT", "INT", "INT", "LATENT")
    RETURN_NAMES  = ("width", "height", "scaled_width", "scaled_height",
                     "scaled_width2", "scaled_height2", "batch_size", "seed", "latent")
    OUTPUT_NODE   = True
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/resolution"
    DESCRIPTION   = (
        "All-in-one resolution node. Preset names show exact W×H and target model family (SDXL/Flux). "
        "width/height inputs are only used when 'custom' is selected. "
        "prescale_factor scales the base first (snapped to 8px); "
        "upscale_factor / upscale_factor2 produce two independent HiRes outputs. "
        "Emits an empty latent, replacing EmptyLatentImage."
    )

    @classmethod
    def IS_CHANGED(cls, seed_mode, **kwargs):
        if seed_mode == "randomize":
            return float("nan")
        return False

    def execute(self, aspect_ratio, width, height,
                prescale_factor, upscale_factor, upscale_factor2, batch_size, seed, seed_mode,
                swap_dimensions):
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
        for name, val in (("prescale_factor", prescale_factor),
                          ("upscale_factor", upscale_factor),
                          ("upscale_factor2", upscale_factor2)):
            if not math.isfinite(val) or val <= 0:
                raise ValueError(f"[ScaledResolution] {name} must be positive and finite, got {val}")

        # prescale: snap to nearest 8px for VAE compatibility
        width  = max(8, int(round(width  * prescale_factor / 8)) * 8)
        height = max(8, int(round(height * prescale_factor / 8)) * 8)
        if width > MAX_RESOLUTION:
            raise ValueError(f"[ScaledResolution] prescaled width {width} exceeds MAX_RESOLUTION {MAX_RESOLUTION}.")
        if height > MAX_RESOLUTION:
            raise ValueError(f"[ScaledResolution] prescaled height {height} exceeds MAX_RESOLUTION {MAX_RESOLUTION}.")

        scaled_width   = int(round(width  * upscale_factor))
        scaled_height  = int(round(height * upscale_factor))
        scaled_width2  = int(round(width  * upscale_factor2))
        scaled_height2 = int(round(height * upscale_factor2))

        for lbl, val, base, factor in (
            ("scaled_width",   scaled_width,   width,  upscale_factor),
            ("scaled_height",  scaled_height,  height, upscale_factor),
            ("scaled_width2",  scaled_width2,  width,  upscale_factor2),
            ("scaled_height2", scaled_height2, height, upscale_factor2),
        ):
            if val > MAX_RESOLUTION:
                raise ValueError(
                    f"[ScaledResolution] {lbl} {val} exceeds MAX_RESOLUTION {MAX_RESOLUTION}. "
                    f"Reduce prescale_factor ({prescale_factor}), base ({base}), or factor ({factor})."
                )
            if val <= 0:
                raise ValueError(
                    f"[ScaledResolution] {lbl} rounded to {val}. "
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

        latent = torch.zeros([batch_size, 4, height // 8, width // 8], device=self.device)

        # Build node preview display — shown in the node's output area after each execution
        std   = aspect_ratio.split()[-1] if aspect_ratio != "custom" else "custom"
        pre   = f"  (prescale ×{prescale_factor})" if prescale_factor != 1.0 else ""
        label = (
            f"base  {width} × {height}  [{std}]{pre}\n"
            f"×{upscale_factor}  →  {scaled_width} × {scaled_height}\n"
            f"×{upscale_factor2}  →  {scaled_width2} × {scaled_height2}"
        )

        return {
            "ui": {"text": [label]},
            "result": (
                width, height,
                scaled_width, scaled_height,
                scaled_width2, scaled_height2,
                batch_size, out_seed,
                {"samples": latent},
            ),
        }


NODE_CLASS_MAPPINGS        = {"ScaledResolution": ScaledResolution}
NODE_DISPLAY_NAME_MAPPINGS = {"ScaledResolution": "Scaled Resolution"}
