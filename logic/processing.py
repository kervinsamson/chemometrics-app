import os
import glob
import spectrochempy as spc
import numpy as np
from scipy.signal import savgol_filter
from sklearn.model_selection import train_test_split, cross_val_predict, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline

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

def train_pls_model(spectra_data, target_component, num_components, current_derivative, wavenumbers, region_start=None, region_end=None, cv_folds=5):
    """
    --- CHANGED ---
    Accepts wavenumber axis, region boundaries, and number of CV folds.
    Performs k-fold cross-validation instead of a single train-test split.
    """
    X_list, y_list = [], []
    for data in spectra_data.values():
        ref_val = data['refs'].get(target_component)
        if ref_val is not None:
            processed_intensity = get_processed_intensity(data['intensity'], current_derivative)
            X_list.append(processed_intensity)
            y_list.append(ref_val)

    if len(X_list) < 5:
        return None, None, None, None, f"Need at least 5 reference values for '{target_component}' to train a model."

    # This is the full, unsliced data
    X_full = np.array(X_list)
    y = np.array(y_list)

    # --- Slice the X data based on the selected region (if any) ---
    if region_start is not None and region_end is not None and wavenumbers is not None:
        start_wn = min(region_start, region_end)
        end_wn = max(region_start, region_end)
        region_mask = (wavenumbers >= start_wn) & (wavenumbers <= end_wn)
        X = X_full[:, region_mask]
        if X.shape[1] == 0:
            return None, None, None, None, "The selected region contains no data points. Please check the values."
    else:
        X = X_full

    # --- Validate the number of PLS components against CV folds ---
    # Max components is limited by the number of features or samples in the smallest training fold
    # Corrected calculation for the size of the smallest training fold
    test_fold_size = -(-X.shape[0] // cv_folds) # Ceiling division
    max_components_samples = X.shape[0] - test_fold_size
    max_components_features = X.shape[1]
    max_allowed_components = min(max_components_samples, max_components_features)

    if num_components > max_allowed_components:
        error_message = (
            f"Invalid number of PLS components: {num_components}.\n\n"
            f"With {cv_folds}-fold CV on {X.shape[0]} samples, the smallest training set has {max_components_samples} samples.\n"
            f"The number of features is {max_components_features}.\n\n"
            f"Please set the number of components to a value less than or equal to {max_allowed_components}."
        )
        return None, None, None, None, error_message

    n_samples = X.shape[0]
    if n_samples < 2:
        return None, None, None, None, "Not enough samples to train the model."

    # --- NEW: Validate that cv_folds is not greater than the number of samples ---
    if cv_folds > n_samples:
        error_message = (
            f"Invalid number of CV Folds: {cv_folds}.\n\n"
            f"The number of cross-validation folds cannot be greater than the number of samples.\n"
            f"You have {n_samples} samples for this component.\n\n"
            f"Please set 'CV Folds' to a value less than or equal to {n_samples}."
        )
        return None, None, None, None, error_message
    # --- END NEW ---

    # Create a pipeline with a scaler and PLS regression model
    pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('pls', PLSRegression(n_components=num_components))
    ])

    # Define the cross-validation strategy
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)

    # Get cross-validated predictions
    y_cv_pred = cross_val_predict(pipeline, X, y, cv=cv)

    # Calculate cross-validated metrics
    r2_cv = r2_score(y, y_cv_pred)
    rmsecv = np.sqrt(mean_squared_error(y, y_cv_pred))
    # --- END NEW ---

    # Finally, train the model on the entire dataset for future predictions
    final_scaler = StandardScaler()
    X_scaled = final_scaler.fit_transform(X)
    final_model = PLSRegression(n_components=num_components)
    final_model.fit(X_scaled, y)

    # Return the final model, its scaler, and the CV performance metrics
    return final_model, final_scaler, r2_cv, rmsecv, None

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