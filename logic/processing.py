import os
import glob
import spectrochempy as spc
import numpy as np
from scipy.signal import savgol_filter
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_squared_error, r2_score

def load_spectra_from_folder(folder_path):
    """
    --- CHANGED ---
    Now returns both the spectra data and the wavenumber axis from the first file.
    """
    spectra_data = {}
    wavenumbers = None  # Initialize wavenumbers as None
    for file_path in glob.glob(os.path.join(glob.escape(folder_path), '*.spa')):
        filename = os.path.basename(file_path)
        try:
            nd = spc.read_spa(file_path)
            # --- NEW: Capture the wavenumber axis from the first valid file ---
            if wavenumbers is None:
                wavenumbers = nd.x.data
            # --- END NEW ---
            spectra_data[filename] = {'nd': nd, 'intensity': nd.data.squeeze(), 'refs': {}}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
    # Return both the data and the common x-axis
    return spectra_data, wavenumbers

def train_pls_model(spectra_data, target_component, num_components, current_derivative, wavenumbers, region_start=None, region_end=None):
    """
    --- CHANGED ---
    Accepts wavenumber axis and region boundaries to slice the data before training.
    """
    X_list, y_list = [], []
    for data in spectra_data.values():
        ref_val = data['refs'].get(target_component)
        if ref_val is not None:
            processed_intensity = get_processed_intensity(data['intensity'], current_derivative)
            X_list.append(processed_intensity)
            y_list.append(ref_val)

    if len(X_list) < 5:
        return None, None, None, f"Need at least 5 reference values for '{target_component}' to train a model."

    # This is the full, unsliced data
    X_full = np.array(X_list)
    y = np.array(y_list)

    # --- NEW: Slice the X data based on the selected region ---
    if region_start is not None and region_end is not None and wavenumbers is not None:
        # Make it robust: user can enter start/end in any order
        start_wn = min(region_start, region_end)
        end_wn = max(region_start, region_end)
        
        # Create a boolean mask for the wavenumbers within the selected region
        region_mask = (wavenumbers >= start_wn) & (wavenumbers <= end_wn)
        
        # Apply the mask to the spectral data (X)
        X = X_full[:, region_mask]
        
        # Edge case: If the region is invalid and contains no data points
        if X.shape[1] == 0:
            return None, None, None, "The selected region contains no data points. Please check the values."
    else:
        # If no region is set, use the full spectrum
        X = X_full
    # --- END NEW ---

    # --- NEW: Validate the number of PLS components ---
    # The number of components cannot exceed the number of samples or features.
    # We check against the training set size, which is 70% of the total samples.
    max_components_samples = int(X.shape[0] * 0.7) # After train/test split
    max_components_features = X.shape[1]
    max_allowed_components = min(max_components_samples, max_components_features)

    if num_components > max_allowed_components:
        error_message = (
            f"Invalid number of PLS components: {num_components}.\n\n"
            f"With the current data and region selection:\n"
            f"- Number of Samples (for training): {max_components_samples}\n"
            f"- Number of Spectral Points (Features): {max_components_features}\n\n"
            f"Please set the number of components to a value less than or equal to {max_allowed_components}."
        )
        return None, None, None, error_message
    # --- END NEW ---

    # The rest of the function now operates on the new, potentially sliced X
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    model = PLSRegression(n_components=num_components)
    model.fit(X_train_scaled, y_train)
    
    y_pred = model.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    
    return model, scaler, r2, rmse

def get_processed_intensity(original_intensity, derivative_order):
    """
    --- NO CHANGE ---
    This function is self-contained and does not need to be modified.
    """
    if derivative_order == 0:
        return original_intensity
    
    window_length, polyorder = 11, 2
    if derivative_order == 1:
        return savgol_filter(original_intensity, window_length, polyorder, deriv=1)
    elif derivative_order == 2:
        return savgol_filter(original_intensity, window_length, polyorder, deriv=2)
    return original_intensity