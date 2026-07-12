import torch
import comfy.model_management


class VRAMMonitor:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
            },
            "optional": {
                "warn_threshold_pct": ("FLOAT", {
                    "default": 90.0, "min": 0.0, "max": 100.0, "step": 1.0,
                    "tooltip": "Print a warning to console when VRAM usage exceeds this %.",
                }),
            },
        }

    RETURN_TYPES  = ("MODEL", "FLOAT", "FLOAT", "FLOAT")
    RETURN_NAMES  = ("model",  "vram_used_gb", "vram_free_gb", "vram_pct")
    OUTPUT_NODE   = True
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/monitoring"
    DESCRIPTION   = (
        "Passes the model through unchanged and reports current VRAM usage. "
        "Wire anywhere in a model chain to sample stats at that point in the graph."
    )

    def execute(self, model, warn_threshold_pct=90.0):
        if not torch.cuda.is_available():
            print("[VRAMMonitor] CUDA not available — returning zeros.")
            return {"ui": {"text": ["CUDA not available"]},
                    "result": (model, 0.0, 0.0, 0.0)}

        # Always use the active CUDA device — model params may be on CPU (offloaded)
        device = comfy.model_management.get_torch_device()
        if not device.type.startswith("cuda"):
            device = torch.device("cuda:0")

        props     = torch.cuda.get_device_properties(device)
        total     = props.total_memory
        reserved  = torch.cuda.memory_reserved(device)
        free      = total - reserved

        used_gb = reserved / 1024 ** 3
        free_gb = free    / 1024 ** 3
        total_gb = total  / 1024 ** 3
        pct     = (reserved / total) * 100.0

        msg = (
            f"VRAM [{props.name}]: "
            f"{used_gb:.2f} GB used / {total_gb:.2f} GB total ({pct:.1f}%) "
            f"— {free_gb:.2f} GB free"
        )

        if pct >= warn_threshold_pct:
            print(f"\033[93m[VRAMMonitor] WARNING: {msg} (threshold {warn_threshold_pct:.0f}%)\033[0m")
        else:
            print(f"[VRAMMonitor] {msg}")

        return {"ui": {"text": [msg]}, "result": (model, used_gb, free_gb, pct)}


NODE_CLASS_MAPPINGS        = {"VRAMMonitor": VRAMMonitor}
NODE_DISPLAY_NAME_MAPPINGS = {"VRAMMonitor": "VRAM Monitor"}
