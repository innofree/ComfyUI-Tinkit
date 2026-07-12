# ComfyUI-Tinkit

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A collection of utility nodes for ComfyUI workflows, focused on resolution management, attention optimization, monitoring, and seed tracking.

Tested on: **RTX PRO 5000 Blackwell (SM 12.0a, 48 GB)** / ComfyUI latest / Python 3.13

---

## Nodes

### Scaled Resolution
**Category:** `tinkit/resolution`

All-in-one replacement for the common 5-node resolution setup
(`PrimitiveInt × 2` + `MathExpression × 2` + `EmptyLatentImage`).

| Input | Type | Description |
|---|---|---|
| `aspect_ratio` | Dropdown | 18 presets or `custom` |
| `width` / `height` | INT | Used only when `aspect_ratio = custom` |
| `swap_dimensions` | BOOLEAN | Flip portrait ↔ landscape |
| `upscale_factor` | FLOAT | Multiplier for `scaled_width` / `scaled_height` |
| `batch_size` | INT | Passed through to downstream latent nodes |
| `seed` | INT | Fixed seed value |
| `seed_mode` | Dropdown | `fixed` or `randomize` (new seed every queue run) |

| Output | Description |
|---|---|
| `width` / `height` | Base resolution (feeds `EmptyLatentImage`) |
| `scaled_width` / `scaled_height` | Upscaler target resolution (feeds `ImageScale`) |
| `batch_size` | Forwarded batch size |
| `seed` | Resolved seed (random or fixed) |

**Tip:** Connect `width`/`height` to `EmptyLatentImage`, `scaled_width`/`scaled_height` to your upscaler's target size, and `seed` to your sampler.

---

### Filename Formatter
**Category:** `tinkit/io`

Builds a sanitized filename string from a template. Useful as input to Image Saver nodes.

| Input | Type | Description |
|---|---|---|
| `template` | STRING | Format string, e.g. `{date}-{model}-{seed}` |
| `seed` | INT | Seed value (typically from Scaled Resolution) |
| `model_name` | STRING *(optional)* | Full or partial model path; basename is extracted |
| `prefix` / `suffix` | STRING *(optional)* | Static prefix/suffix strings |
| `index` | INT *(optional)* | Sequence counter |
| `date_format` | STRING *(optional)* | `strftime` format, default `%Y%m%d` |

**Available template keys:** `{date}`, `{model}`, `{seed}`, `{prefix}`, `{suffix}`, `{index}`

**Output:** `filename` (STRING) — invalid filesystem characters replaced with `_`.

**Example:** template `{date}_{model}_{seed}` → `20250712_wan21_4294967295`

---

### VRAM Monitor
**Category:** `tinkit/monitoring`

Passes a model through unchanged and reports current GPU VRAM usage. Wire anywhere in a model chain to sample stats at that point in the graph.

| Input | Description |
|---|---|
| `model` | MODEL pass-through |
| `warn_threshold_pct` | Print a console warning when usage exceeds this % (default 90) |

| Output | Description |
|---|---|
| `model` | Unchanged model |
| `vram_used_gb` | Reserved VRAM in GB |
| `vram_free_gb` | Free VRAM in GB |
| `vram_pct` | Usage as percentage |

Stats are also displayed in the node's UI text widget during execution.

---

### Attention Auto-Select
**Category:** `tinkit/optimization`

Detects the current GPU's compute capability and patches the model's attention mechanism with the fastest available backend.

| GPU | Backend selected |
|---|---|
| SM 12.0+ (Blackwell) | `sageattn3` (FP4 MMA) |
| SM 7.5–11.x (Turing → Ada) | `sageattn` (int8/fp16) |
| SM < 7.5 or no library | PyTorch default SDPA |

| Input | Description |
|---|---|
| `model` | MODEL to patch |
| `force_backend` | `auto` (default), `sageattn3`, `sageattn`, or `default` |

| Output | Description |
|---|---|
| `model` | Cloned model with attention patched |
| `backend_info` | Human-readable string describing the active backend |

Patches via `model_options["transformer_options"]["optimized_attention_override"]` — the same mechanism as KJNodes. The probe result is cached per device per session.

**Requirements (optional):**
- SM 12+: `pip install sageattn3`
- SM 7.5+: `pip install sageattention`

---

### Model Name Extractor
**Category:** `tinkit/model`

Extracts the bare filename (no path, no extension) from a model path string and passes the model through unchanged.

| Input | Description |
|---|---|
| `model` | MODEL pass-through |
| `model_path` | Path string, e.g. `checkpoints/wan_2.1_bf16.safetensors` |

| Output | Description |
|---|---|
| `model` | Unchanged model |
| `model_name` | `wan_2.1_bf16` |

**Tip:** Wire `model_name` into `Filename Formatter`'s `model_name` input for automatic naming.

---

### Seed History
**Category:** `tinkit/seed`

Records every seed used across successive queue runs (in-process, resets on ComfyUI restart). Useful for re-generating a specific image when using randomized seeds.

| Input | Description |
|---|---|
| `seed` | Current seed (connect from Scaled Resolution's `seed` output) |
| `history_size` | Maximum number of past seeds to remember (default 10) |

| Output | Description |
|---|---|
| `seed` | Current seed (pass-through) |
| `prev_seed` | Seed from the previous queue run |
| `prev2_seed` | Seed from two runs ago |
| `history` | Full history as newline-separated string (for a text display node) |

Always re-executes every queue cycle so history is always up to date.

---

## Recommended Workflow Chain

```
[Scaled Resolution]
  width/height      → EmptyLatentImage
  scaled_w/scaled_h → ImageScale (upscaler target)
  seed              → KSampler seed
  seed              → [Seed History] → prev_seed (backup)
  seed              → [Filename Formatter] → Image Saver

[Model Name Extractor]
  model_path        ← (Primitive String with model filename)
  model             → [VRAM Monitor] → [Attention Auto-Select] → KSampler model
  model_name        → [Filename Formatter] model_name
```

---

## Installation

Manual (already installed if you're reading this):
```bash
cd ComfyUI/custom_nodes
git clone <this-repo> ComfyUI-Tinkit
# restart ComfyUI
```

No pip dependencies beyond what ComfyUI already requires. `sageattn3` / `sageattention` are optional and only needed for `Attention Auto-Select`.

---

## File Structure

```
ComfyUI-Tinkit/
  __init__.py               # re-exports NODE_CLASS_MAPPINGS
  nodes/
    __init__.py             # aggregates all node modules
    resolution.py           # ScaledResolution
    filename.py             # FilenameFormatter
    vram.py                 # VRAMMonitor
    attention.py            # AttentionAutoSelect
    model_info.py           # ModelNameExtractor
    seed.py                 # SeedHistory
  README.md
  AGENTS.md
```
