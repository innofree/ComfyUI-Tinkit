import torch


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
    CATEGORY      = "workflow-utils/monitoring"
    DESCRIPTION   = (
        "Passes the model through unchanged and reports current VRAM usage. "
        "Wire anywhere in a model chain to sample stats at that point in the graph."
    )

    def execute(self, model, warn_threshold_pct=90.0):
        if not torch.cuda.is_available():
            print("[VRAMMonitor] CUDA not available — returning zeros.")
            return {"ui": {"text": ["CUDA not available"]},
                    "result": (model, 0.0, 0.0, 0.0)}

        # Prefer the device the model's parameters live on; fall back to cuda:0
        device = torch.device("cuda:0")
        try:
            device = next(model.model.parameters()).device
        except (AttributeError, StopIteration):
            pass

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
