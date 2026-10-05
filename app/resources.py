import os
import sys

APP_NAME = "DSwingSpot"
PROJECT_URL = "https://github.com/GuoYuHeJason/DSwingSpot"


def app_root() -> str:
    """Folder containing the application files (the PyInstaller bundle when frozen)."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def executable_dir() -> str:
    """Folder the user launched the application from, where downloaded assets are usually extracted."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return app_root()


def icon_path(name: str) -> str:
    return os.path.join(app_root(), "app", "icons", name)


IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")

# asset key -> (label, file dialog filter, accepted extensions)
ASSET_FILES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "scale_bar_template": (
        "Scale bar template",
        "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff)",
        IMAGE_EXTENSIONS,
    ),
    "bg_removal_model": ("Background removal model", "U²-Net model (*.pth)", (".pth",)),
    "shape_predictor": ("Shape predictor", "dlib shape predictor (*.dat)", (".dat",)),
}


def find_assets(folder: str, max_depth: int = 2) -> dict[str, str]:
    """
    Looks for the model files in a folder (e.g. the extracted assets.zip) and its subfolders.
    Returns {asset key: path} for the files found.
    """
    found: dict[str, str] = {}
    images: list[str] = []
    base_depth = folder.rstrip(os.sep).count(os.sep)
    for root, dirs, files in os.walk(folder):
        if root.count(os.sep) - base_depth >= max_depth:
            dirs[:] = []
        for name in sorted(files):
            path = os.path.join(root, name)
            lower = name.lower()
            if lower.endswith(".dat"):
                found.setdefault("shape_predictor", path)
            elif lower.endswith(".pth"):
                found.setdefault("bg_removal_model", path)
            elif lower.endswith(IMAGE_EXTENSIONS):
                images.append(path)
    template_like = [p for p in images if any(w in os.path.basename(p).lower() for w in ("scale", "bar", "template"))]
    if template_like:
        found["scale_bar_template"] = template_like[0]
    elif len(images) == 1:
        found["scale_bar_template"] = images[0]
    return found


def default_asset_folders() -> list[str]:
    folders = [
        os.path.join(executable_dir(), "assets"),
        os.path.join(app_root(), "assets"),
        os.path.join(os.getcwd(), "assets"),
    ]
    return list(dict.fromkeys(f for f in folders if os.path.isdir(f)))
