# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec file for LED Hex Game
#
# Build on Windows:
#   pip install pyinstaller
#   pyinstaller ledhex.spec
#
# Output: dist\ledhex\ledhex.exe  (folder-mode, recommended)
# For single file: set EXE(console=..., ..., onefile=True) — but slower to start

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# ── Data files to bundle ──────────────────────────────────────────────────────
# Format: (source_path, dest_folder_inside_bundle)
added_data = [
    # Game assets
    ('photo',       'photo'),
    ('audio',       'audio'),
    ('source',      'source'),
    ('video',       'video'),

    # Hardware DLLs (dongle + LED controller)
    ('use_dll',     'use_dll'),

    # Web simulator static files
    ('simulator/static', 'simulator/static'),

    # Settings / DB (initial state — gets updated at runtime)
    ('setting',     'setting'),
    ('data',        'data'),

    # Game config / shelve files
    ('game_set',    'game_set'),
]

# Only include folders that actually exist
import os
added_data = [(src, dst) for src, dst in added_data if os.path.exists(src)]

# ── Hidden imports PyInstaller misses ─────────────────────────────────────────
hidden_imports = [
    'sqlite3',
    'shelve',
    'dbm',
    'dbm.dumb',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.font',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'PIL._tkinter_finder',
    'pygame',
    'pygame.mixer',
    'fastapi',
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'starlette',
    'starlette.routing',
    'starlette.staticfiles',
    'starlette.responses',
    'starlette.websockets',
    'websockets',
    'anyio',
    'anyio._backends._asyncio',
    'loguru',
    'Crypto',
    'Crypto.Cipher',
    'Crypto.PublicKey',
    'rsa',
    'moviepy',
    'pynput',
    'pynput.keyboard',
    'pynput.mouse',
    'importlib',
    'importlib.util',
    'ctypes',
    'ctypes.util',
    'serial',
    'serial.tools',
    'serial.tools.list_ports',
]

a = Analysis(
    ['run_simulator.py'],       # entry point
    pathex=['.'],
    binaries=[],
    datas=added_data,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'scipy',
        'numpy.testing',
        'IPython',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Set DEBUG_BUILD=1 env var before running pyinstaller to get a console window:
#   set DEBUG_BUILD=1 && pyinstaller ledhex.spec
import os as _os
_debug_build = _os.environ.get('DEBUG_BUILD', '0') == '1'

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,         # folder mode (faster startup than --onefile)
    name='ledhex',
    debug=_debug_build,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=_debug_build,          # True = show console window with error output
    disable_windowed_traceback=False,
    icon='photo/ledplay.ico' if _os.path.exists('photo/ledplay.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ledhex',
)
