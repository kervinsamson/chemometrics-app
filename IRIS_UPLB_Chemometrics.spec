# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('spa_data', 'spa_data'), ('Cassava (HCN)', 'Cassava (HCN)'), ('Spectral data', 'Spectral data'), ('RICE_NITROGEN_PROJECT.pkl', '.')]
binaries = []
hiddenimports = ['lazy_loader', 'scipy', 'scipy.signal', 'scipy.linalg', 'scipy.sparse', 'scipy.spatial', 'scipy.stats', 'scipy.optimize', 'scipy.interpolate', 'sklearn', 'sklearn.cross_decomposition', 'sklearn.preprocessing', 'sklearn.model_selection', 'sklearn.metrics', 'sklearn.pipeline', 'sklearn.decomposition', 'sklearn.linear_model', 'sklearn.ensemble', 'joblib', 'numpy', 'pandas', 'matplotlib', 'matplotlib.pyplot', 'matplotlib.backends', 'matplotlib.backends.backend_qtagg', 'matplotlib.backends.backend_qt5agg', 'matplotlib.backends.backend_agg', 'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'importlib_metadata', 'packaging', 'importlib.util', 'importlib.machinery', 'types']
tmp_ret = collect_all('spectrochempy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'test'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='IRIS_UPLB_Chemometrics',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='IRIS_UPLB_Chemometrics',
)
