# PyInstaller spec for Atlas.app — build with:  pyinstaller desktop/Atlas.spec
# Run from the repo root so the relative data paths resolve.
import os

from PyInstaller.utils.hooks import collect_submodules

REPO = os.getcwd()

a = Analysis(
    [os.path.join(REPO, "desktop", "launcher.py")],
    pathex=[os.path.join(REPO, "backend"), REPO],
    binaries=[],
    datas=[
        (os.path.join(REPO, "frontend", "dist"), os.path.join("frontend", "dist")),
        (os.path.join(REPO, "backend", "app"), os.path.join("backend", "app")),
    ],
    hiddenimports=(
        collect_submodules("uvicorn")
        + collect_submodules("app")
        + ["desktop.server", "webview"]
    ),
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "_pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Atlas",
    console=False,  # windowed app — no terminal
)
coll = COLLECT(exe, a.binaries, a.datas, name="Atlas")

app = BUNDLE(
    coll,
    name="Atlas.app",
    icon=None,  # placeholder; real .icns added in a later plan
    bundle_identifier="dev.nashops.atlas",
)
