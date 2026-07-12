import os
import subprocess
import sys

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
CNR_ID = "comfyui-tinkit"


def set_cnr_id():
    cnr_path = os.path.join(PACKAGE_DIR, ".git", ".cnr-id")
    git_dir = os.path.join(PACKAGE_DIR, ".git")
    if not os.path.isdir(git_dir):
        return
    if os.path.exists(cnr_path):
        return
    with open(cnr_path, "w") as f:
        f.write(CNR_ID)
    print(f"[ComfyUI-Tinkit] cnr_id set: {CNR_ID}")


def install_optional_deps():
    """
    Optional GPU attention backends.
    Uncomment the one matching your GPU and re-run install.py,
    or install manually (see requirements.txt).
    """
    # cc = None
    # try:
    #     import torch
    #     cc = torch.cuda.get_device_capability()
    # except Exception:
    #     pass
    #
    # if cc and cc >= (12, 0):
    #     subprocess.run([sys.executable, "-m", "pip", "install", "sageattn3"], check=False)
    # elif cc and cc >= (7, 5):
    #     subprocess.run([sys.executable, "-m", "pip", "install", "sageattention"], check=False)
    pass


if __name__ == "__main__":
    set_cnr_id()
    install_optional_deps()
    print("[ComfyUI-Tinkit] install complete.")
