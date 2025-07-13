# PowerShell script to build the PyInstaller application without a spec file

# Set PyInstaller options
$pyinstaller_options = @(
    "main.py",
    "--name", "IRIS",
    "--windowed",
    "--clean",
    "--icon", "icon.ico",
    # Add data files
    "--add-data", "icon.ico;.",
    "--add-data", "spa_data;spa_data",
    "--add-data", "Cassava (HCN);Cassava (HCN)",
    "--add-data", "Spectral data;Spectral data",
    "--add-data", "RICE_NITROGEN_PROJECT.pkl;.",
    # Exclude modules
    "--exclude-module", "tkinter",
    "--exclude-module", "test",
    "--hidden-import", "lazy_loader",
    # Collect all spectrochempy files including .pyi stubs
    "--collect-all", "spectrochempy",
    # Add hidden imports
    "--hidden-import", "scipy",
    "--hidden-import", "scipy.signal",
    "--hidden-import", "scipy.linalg",
    "--hidden-import", "scipy.sparse",
    "--hidden-import", "scipy.spatial",
    "--hidden-import", "scipy.stats",
    "--hidden-import", "scipy.optimize",
    "--hidden-import", "scipy.interpolate",
    "--hidden-import", "sklearn",
    "--hidden-import", "sklearn.cross_decomposition",
    "--hidden-import", "sklearn.preprocessing",
    "--hidden-import", "sklearn.model_selection",
    "--hidden-import", "sklearn.metrics",
    "--hidden-import", "sklearn.pipeline",
    "--hidden-import", "sklearn.decomposition",
    "--hidden-import", "sklearn.linear_model",
    "--hidden-import", "sklearn.ensemble",
    "--hidden-import", "joblib",
    "--hidden-import", "numpy",
    "--hidden-import", "pandas",
    "--hidden-import", "matplotlib",
    "--hidden-import", "matplotlib.pyplot",
    "--hidden-import", "matplotlib.backends",
    "--hidden-import", "matplotlib.backends.backend_qtagg",
    "--hidden-import", "matplotlib.backends.backend_qt5agg",
    "--hidden-import", "matplotlib.backends.backend_agg",
    "--hidden-import", "PySide6.QtCore",
    "--hidden-import", "PySide6.QtWidgets",
    "--hidden-import", "PySide6.QtGui",
    "--hidden-import", "importlib_metadata",
    "--hidden-import", "packaging",
    "--hidden-import", "importlib.util",
    "--hidden-import", "importlib.machinery",
    "--hidden-import", "types"
)

# Construct and execute the command
$command = "python -m PyInstaller " + ($pyinstaller_options | ForEach-Object { "`"$_`"" }) -join " "
Write-Output "Running command:"
Write-Output $command
Invoke-Expression $command
