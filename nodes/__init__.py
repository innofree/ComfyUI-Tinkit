from .resolution    import NODE_CLASS_MAPPINGS as _R,  NODE_DISPLAY_NAME_MAPPINGS as _RD
from .filename      import NODE_CLASS_MAPPINGS as _F,  NODE_DISPLAY_NAME_MAPPINGS as _FD
from .vram          import NODE_CLASS_MAPPINGS as _V,  NODE_DISPLAY_NAME_MAPPINGS as _VD
from .attention     import NODE_CLASS_MAPPINGS as _A,  NODE_DISPLAY_NAME_MAPPINGS as _AD
from .model_info    import NODE_CLASS_MAPPINGS as _M,  NODE_DISPLAY_NAME_MAPPINGS as _MD
from .seed          import NODE_CLASS_MAPPINGS as _S,  NODE_DISPLAY_NAME_MAPPINGS as _SD
from .prompt_saver  import NODE_CLASS_MAPPINGS as _PS, NODE_DISPLAY_NAME_MAPPINGS as _PSD

NODE_CLASS_MAPPINGS = {**_R, **_F, **_V, **_A, **_M, **_S, **_PS}
NODE_DISPLAY_NAME_MAPPINGS = {**_RD, **_FD, **_VD, **_AD, **_MD, **_SD, **_PSD}
