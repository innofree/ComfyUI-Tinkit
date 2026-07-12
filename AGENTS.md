# AGENTS.md — ComfyUI-Tinkit

Guidelines for AI coding agents (Claude Code, Copilot, etc.) working in this package.

---

## Package Overview

**Purpose:** Utility nodes for ComfyUI — resolution, attention optimization, monitoring, I/O helpers, seed tracking.
**Entry point:** `__init__.py` → `nodes/__init__.py` → individual `nodes/*.py` modules.
**One node class per file.** Each file owns its `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` dicts; `nodes/__init__.py` merges them.

---

## Adding a New Node

1. **Create `nodes/<name>.py`** with one class and a `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` at the bottom.
2. **Import it in `nodes/__init__.py`** using the `_X` / `_XD` alias pattern already there.
3. No other files need to change.

**Minimal template:**

```python
class MyNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"x": ("INT", {"default": 0})}}

    RETURN_TYPES  = ("INT",)
    RETURN_NAMES  = ("result",)
    FUNCTION      = "execute"
    CATEGORY      = "tinkit/<subcategory>"

    def execute(self, x):
        return (x,)

NODE_CLASS_MAPPINGS        = {"MyNode": MyNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MyNode": "My Node"}
```

---

## ComfyUI Node Conventions

### INPUT_TYPES structure
```python
{
    "required": { ... },   # always present, shown as connected slots
    "optional": { ... },   # shown as optional input slots
    # "hidden": { ... }    # use sparingly; not visible in UI
}
```

### Type declarations
- `("INT", {"default": 0, "min": 0, "max": N, "step": 1})`
- `("FLOAT", {"default": 1.0, "min": 0.01, "max": 64.0, "step": 0.01})`
- `("STRING", {"default": "", "multiline": False})`
- `("BOOLEAN", {"default": False})`
- `(["opt_a", "opt_b"],)` — dropdown; first element is the list, no second element needed for simple dropdowns
- `("MODEL",)`, `("LATENT",)`, `("IMAGE",)` — ComfyUI built-in connection types

### Pass-through pattern
When a node receives a `MODEL` (or any complex type) and must not mutate it, either return it unchanged or call `model.clone()` before modifying `model_options`. Never mutate the received object in place.

### IS_CHANGED
```python
@classmethod
def IS_CHANGED(cls, **kwargs):
    return float("nan")   # force re-execute every queue cycle
    # return False         # skip re-execute if inputs unchanged (default)
```
Only override when the node has side effects or external state (random seed, live VRAM, history deque).

### OUTPUT_NODE
Set `OUTPUT_NODE = True` when the node returns a `{"ui": ..., "result": ...}` dict. This signals ComfyUI to display the UI widget. The `result` key must contain the tuple matching `RETURN_TYPES`.

```python
def execute(self, ...):
    return {"ui": {"text": ["display text"]}, "result": (value1, value2)}
```

### Attention patching (ComfyUI standard)
```python
model_clone = model.clone()
if "transformer_options" not in model_clone.model_options:
    model_clone.model_options["transformer_options"] = {}
model_clone.model_options["transformer_options"]["optimized_attention_override"] = my_fn
return (model_clone,)
```
`my_fn` signature: `fn(q, k, v, *args, **kwargs) -> tensor`. Drop unknown kwargs; only forward what the underlying attention library accepts.

---

## Existing Node Patterns to Follow

| Pattern | Where used | Why |
|---|---|---|
| `_probe_backend()` with module-level cache | `attention.py` | GPU detection is slow; cache per `device_index` |
| `collections.deque` class variable | `seed.py` | Persist state across queue runs without a file |
| `os.path.splitext(os.path.basename(...))` | `filename.py`, `model_info.py` | Safe extraction of bare filename from any path |
| `re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', ...)` | `filename.py` | Cross-platform filename sanitization |
| Validate then compute (raise ValueError with `[NodeName]` prefix) | all nodes | Consistent error messages surfaced in ComfyUI UI |

---

## What NOT to Do

- **Do not** add `torch.nn.functional.scaled_dot_product_attention` monkey-patches. Use `transformer_options["optimized_attention_override"]` instead — it is per-model and reversible.
- **Do not** store mutable state in `execute()` local scope across calls. Use class variables or module-level variables with proper initialization guards.
- **Do not** use `print()` for normal flow in production nodes; use `logging.getLogger(__name__)`. Reserve bare `print()` for user-visible status lines prefixed with `[NodeName]`.
- **Do not** modify `model.model_options` in place. Always call `model.clone()` first.
- **Do not** add `try/except ImportError` around core imports. Only wrap optional heavy dependencies (`sageattn3`, `sageattention`) so the package loads even when they are absent.

---

## Validation Checklist Before Committing a New Node

- [ ] `INPUT_TYPES` has `"required"` and/or `"optional"` keys (never bare dict)
- [ ] `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, `CATEGORY` all defined
- [ ] Every `ValueError` is prefixed `[ClassName]` and names the offending value
- [ ] `IS_CHANGED` defined if the node reads external state (GPU, time, deque)
- [ ] `OUTPUT_NODE = True` if `execute()` returns `{"ui": ..., "result": ...}`
- [ ] Added to `nodes/__init__.py` with a unique alias pair (`_X`, `_XD`)
- [ ] `NODE_CLASS_MAPPINGS` key is unique across all ComfyUI custom nodes in this environment (check with `grep -r 'NODE_CLASS_MAPPINGS' custom_nodes/`)

---

## Testing

ComfyUI has no built-in test runner. Validate import correctness without starting the server:

```bash
cd ComfyUI/custom_nodes/ComfyUI-Tinkit
python -c "
import sys; sys.path.insert(0, '.')
from nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
for k, n in zip(NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS.values()):
    print(f'{k:30s} -> {n}')
print(f'Total: {len(NODE_CLASS_MAPPINGS)} nodes')
"
```

For logic testing, instantiate nodes directly:
```bash
python -c "
import sys; sys.path.insert(0, '.')
from nodes.resolution import ScaledResolution
node = ScaledResolution()
print(node.execute('1:1  square 1024', 0, 0, False, 4.0, 1, 42, 'fixed'))
# Expected: (1024, 1024, 4096, 4096, 1, 42)
"
```

---

## Environment Notes

- Python 3.13, ComfyUI on RTX PRO 5000 Blackwell (SM 12.0a, 48 GB VRAM)
- `sageattn3` v1.0.0 installed at `site-packages/sageattn3/` (CUTLASS-based CUDA kernels)
- `sageattention` 1.0.6 installed (triton-based, SM 8.6 fallback)
- ComfyUI restart required to register new/renamed node packages
- Custom nodes live in `/home/interbus/comfy/ComfyUI/custom_nodes/`
