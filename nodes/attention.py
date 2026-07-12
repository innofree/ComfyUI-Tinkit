import logging
import torch

log = logging.getLogger(__name__)

# ── backend probe (run once per Python session) ──────────────────────────────

_BACKEND_CACHE: dict = {}   # {device_index: (backend_name, attn_fn | None)}


def _probe_backend(device_index: int = 0) -> tuple:
    """Detect the best available attention backend for the given device."""
    if device_index in _BACKEND_CACHE:
        return _BACKEND_CACHE[device_index]

    cc = torch.cuda.get_device_capability(device_index)
    name = torch.cuda.get_device_properties(device_index).name
    backend = "default SDPA"
    fn = None

    if cc >= (12, 0):
        try:
            from sageattn3.api import sageattn3_blackwell
            fn = sageattn3_blackwell
            backend = f"sageattn3 (SM{cc[0]}.{cc[1]}, {name})"
        except ImportError:
            log.warning("[AttentionAutoSelect] sageattn3 not found for SM12+, trying sageattn.")

    if fn is None and cc >= (7, 5):
        try:
            from sageattention import sageattn
            fn = sageattn
            backend = f"sageattn (SM{cc[0]}.{cc[1]}, {name})"
        except ImportError:
            pass

    if fn is None:
        backend = f"default SDPA (SM{cc[0]}.{cc[1]}, {name})"

    _BACKEND_CACHE[device_index] = (backend, fn)
    return backend, fn


def _make_override(attn_fn):
    """Return a ComfyUI transformer_options attention override wrapper."""
    def override(q, k, v, *args, **kwargs):
        # Drop ComfyUI-specific extra args; pass only what the attn lib needs.
        return attn_fn(q, k, v, is_causal=kwargs.get("is_causal", False))
    return override


# ── node ─────────────────────────────────────────────────────────────────────

class AttentionAutoSelect:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
            },
            "optional": {
                "force_backend": (["auto", "sageattn3", "sageattn", "default"], {"default": "auto"}),
            },
        }

    RETURN_TYPES  = ("MODEL", "STRING")
    RETURN_NAMES  = ("model",  "backend_info")
    OUTPUT_NODE   = True
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/optimization"
    DESCRIPTION   = (
        "Automatically selects the fastest available attention backend for the current GPU: "
        "sageattn3 for SM12+ (Blackwell), sageattn for Ada/Ampere (SM7.5+), "
        "or default SDPA otherwise. Patches via ComfyUI transformer_options."
    )

    def execute(self, model, force_backend="auto"):
        device_index = 0
        try:
            device = next(model.model.parameters()).device
            device_index = device.index if device.index is not None else 0
        except (AttributeError, StopIteration):
            pass

        backend, fn = _probe_backend(device_index)

        # Handle force_backend override
        if force_backend != "auto":
            fn = None
            if force_backend == "sageattn3":
                try:
                    from sageattn3.api import sageattn3_blackwell
                    fn = sageattn3_blackwell
                    backend = f"sageattn3 (forced)"
                except ImportError:
                    backend = "sageattn3 not installed — using default SDPA"
            elif force_backend == "sageattn":
                try:
                    from sageattention import sageattn
                    fn = sageattn
                    backend = f"sageattn (forced)"
                except ImportError:
                    backend = "sageattn not installed — using default SDPA"
            elif force_backend == "default":
                backend = "default SDPA (forced)"

        model_clone = model.clone()

        if fn is not None:
            override = _make_override(fn)
            if "transformer_options" not in model_clone.model_options:
                model_clone.model_options["transformer_options"] = {}
            model_clone.model_options["transformer_options"]["optimized_attention_override"] = override

        log.info(f"[AttentionAutoSelect] {backend}")
        print(f"[AttentionAutoSelect] Active backend: {backend}")

        return {"ui": {"text": [backend]}, "result": (model_clone, backend)}


NODE_CLASS_MAPPINGS        = {"AttentionAutoSelect": AttentionAutoSelect}
NODE_DISPLAY_NAME_MAPPINGS = {"AttentionAutoSelect": "Attention Auto-Select"}
