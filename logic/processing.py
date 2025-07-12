import os
import glob
import spectrochempy as spc
import numpy as np
import json
import joblib
from datetime import datetime
from scipy.signal import savgol_filter
from sklearn.model_selection import train_test_split, cross_val_predict, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.pipeline import Pipeline


def load_spectra_from_folder(folder_path):
    """
    Load all .spa spectral files from a specified folder.
    Returns both the spectra data and the wavenumber axis from the first valid file.

    Args:
        folder_path (str): Path to the folder containing .spa files.

    Returns:
        tuple: (spectra_data, wavenumbers)
            - spectra_data (dict): Dictionary of spectra keyed by filename.
            - wavenumbers (np.ndarray): Wavenumber axis from the first valid file.
    """
    spectra_data = {}
    wavenumbers = None  # Initialize wavenumbers as None
    for file_path in glob.glob(os.path.join(glob.escape(folder_path), '*.spa')):
        filename = os.path.basename(file_path)
        try:
            nd = spc.read_spa(file_path)
            # Capture the wavenumber axis from the first valid file
            if wavenumbers is None:
                wavenumbers = nd.x.data
            spectra_data[filename] = {'nd': nd, 'intensity': nd.data.squeeze(), 'refs': {}}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    # Return both the data and the common x-axis
    return spectra_data, wavenumbers


def load_selected_spa_files(file_paths):
    """
    Load specific selected .spa files instead of an entire folder.

    Args:
        file_paths (list): List of absolute paths to .spa files.

    Returns:
        tuple: (spectra_data, wavenumbers)
            - spectra_data (dict): Dictionary containing spectral data keyed by filename.
            - wavenumbers (np.ndarray): Common wavenumber axis from the first valid file.
    """
    spectra_data = {}
    wavenumbers = None

    for file_path in file_paths:
        if not file_path.lower().endswith('.spa'):
            continue

        filename = os.path.basename(file_path)
        try:
            nd = spc.read_spa(file_path)
            # Capture the wavenumber axis from the first valid file
            if wavenumbers is None:
                wavenumbers = nd.x.data
            spectra_data[filename] = {'nd': nd, 'intensity': nd.data.squeeze(), 'refs': {}}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    
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

def find_optimal_pls_components(spectra_data, target_component, current_derivative, wavenumbers, region_start=None, region_end=None, cv_folds=5, max_components=20):
    """
    Find the optimal number of PLS components by testing different values and selecting the one with best R² CV.
    
    Parameters:
    - spectra_data: Dictionary containing spectral data
    - target_component: Name of the component to predict
    - current_derivative: Derivative order for preprocessing
    - wavenumbers: Wavenumber axis for region selection
    - region_start: Start of spectral region (optional)
    - region_end: End of spectral region (optional)
    - cv_folds: Number of cross-validation folds
    - max_components: Maximum number of components to test
    
    Returns:
    - optimal_components: Best number of components found
    - best_r2: Best R² CV score achieved
    - error_message: Error message if any, None otherwise
    """
    # Prepare data similar to train_pls_model
    X_list, y_list = [], []
    for data in spectra_data.values():
        ref_val = data['refs'].get(target_component)
        if ref_val is not None:
            processed_intensity = get_processed_intensity(data['intensity'], current_derivative)
            X_list.append(processed_intensity)
            y_list.append(ref_val)

    if len(X_list) < 5:
        return None, None, f"Need at least 5 reference values for '{target_component}' to find optimal components."

    # This is the full, unsliced data
    X_full = np.array(X_list)
    y = np.array(y_list)

    # Slice the X data based on the selected region (if any)
    if region_start is not None and region_end is not None and wavenumbers is not None:
        start_wn = min(region_start, region_end)
        end_wn = max(region_start, region_end)
        region_mask = (wavenumbers >= start_wn) & (wavenumbers <= end_wn)
        X = X_full[:, region_mask]
        if X.shape[1] == 0:
            return None, None, "The selected region contains no data points. Please check the values."
    else:
        X = X_full

    # Calculate maximum allowable components
    test_fold_size = -(-X.shape[0] // cv_folds)  # Ceiling division
    max_components_samples = X.shape[0] - test_fold_size
    max_components_features = X.shape[1]
    max_allowed_components = min(max_components_samples, max_components_features, max_components)

    if max_allowed_components < 1:
        return None, None, "Not enough data to determine optimal components."

    # Validate cv_folds
    if cv_folds > X.shape[0]:
        return None, None, f"CV folds ({cv_folds}) cannot be greater than number of samples ({X.shape[0]})."

    # Test different numbers of components
    best_r2 = -np.inf
    optimal_components = 1
    cv = KFold(n_splits=cv_folds, shuffle=True, random_state=42)

    for n_comp in range(1, max_allowed_components + 1):
        try:
            # Create pipeline with current number of components
            pipeline = Pipeline([
                ('scaler', StandardScaler()),
                ('pls', PLSRegression(n_components=n_comp))
            ])

            # Get cross-validated predictions
            y_cv_pred = cross_val_predict(pipeline, X, y, cv=cv)
            r2_cv = r2_score(y, y_cv_pred)

            # Update best if this is better
            if r2_cv > best_r2:
                best_r2 = r2_cv
                optimal_components = n_comp

        except Exception as e:
            # Skip this component count if there's an error
            continue

    return optimal_components, best_r2, None

def save_complete_project(spectra_data, chemical_components, pls_models, model_performance, wavenumbers, 
                         current_derivative, region_start, region_end, auto_pls_components, file_path):
    """
    Save complete project including spectral data, models, and all settings.
    
    This function saves the complete application state including:
    - Spectral data and reference values
    - Chemical components and trained models
    - Processing settings (derivative, region selection)
    - UI state (auto PLS components checkbox)
    - Model performance metrics
    
    Parameters:
    - spectra_data: Dictionary containing spectral data
    - chemical_components: List of component dictionaries
    - pls_models: Dictionary of trained PLS models
    - model_performance: Dictionary of model performance metrics
    - wavenumbers: Wavenumber axis array
    - current_derivative: Current derivative order (0=original, 1=1st, 2=2nd)
    - region_start: Start of spectral region for analysis
    - region_end: End of spectral region for analysis
    - auto_pls_components: Boolean status of auto PLS components checkbox
    - file_path: Path to save the project file
    
    Returns:
    - success: Boolean indicating if save was successful
    - message: Success or error message
    """
    try:
        # Extract reference values and spectral data
        reference_values = {}
        spectral_data = {}
        
        if spectra_data:
            for filename, data in spectra_data.items():
                # Save reference values
                if data['refs']:
                    reference_values[filename] = data['refs']
                
                # Save spectral data for plotting and analysis
                spectral_data[filename] = {
                    'intensity': data['intensity'].tolist(),  # Convert numpy to list for JSON compatibility
                    'filename': filename
                }
        
        # Create complete project data structure with all state information
        project_data = {
            'project_type': 'complete',
            'chemical_components': chemical_components,
            'pls_models': pls_models,
            'model_performance': model_performance,
            'wavenumbers': wavenumbers.tolist() if wavenumbers is not None else None,
            
            # Processing settings - these restore the exact analysis state
            'current_derivative': current_derivative,
            'region_start': region_start,
            'region_end': region_end,
            
            # UI state settings - these restore the exact UI appearance
            'auto_pls_components': auto_pls_components,
            
            # Data
            'reference_values': reference_values,
            'spectral_data': spectral_data,
            
            # Metadata
            'save_timestamp': datetime.now().isoformat(),
            'version': '1.1'  # Increment version for enhanced state saving
        }
        
        # Save using joblib for compatibility with existing model files
        with open(file_path, 'wb') as f:
            joblib.dump(project_data, f)
        
        stats = {
            'models': len(pls_models),
            'components': len(chemical_components),
            'reference_values': len(reference_values),
            'spectra': len(spectral_data)
        }
        
        # Get derivative description
        derivative_names = {0: "Original", 1: "1st Derivative", 2: "2nd Derivative"}
        derivative_desc = derivative_names.get(current_derivative, "Unknown")
        
        # Format region information
        region_info = ""
        if region_start is not None and region_end is not None:
            region_info = f"• Region: {region_start:.0f} - {region_end:.0f} cm⁻¹\n"
        
        # Auto PLS info
        auto_pls_status = "Enabled" if auto_pls_components else "Disabled"
        
        message = (f"Complete project saved successfully!\n"
                  f"• {stats['models']} trained models\n"
                  f"• {stats['components']} components\n"
                  f"• {stats['reference_values']} spectra with reference values\n"
                  f"• {stats['spectra']} spectral datasets\n"
                  f"• Derivative: {derivative_desc}\n"
                  f"{region_info}"
                  f"• Auto PLS Components: {auto_pls_status}\n"
                  f"• Saved to: {file_path}")
        
        return True, message
    
    except Exception as e:
        return False, f"Error saving complete project: {str(e)}"

def load_complete_project(file_path):
    """
    Load complete project including spectral data, models, and all settings.
    
    Parameters:
    - file_path: Path to the project file to load
    
    Returns:
    - project_data: Dictionary containing all project data (or None if failed)
    - message: Success or error message
    """
    try:
        project_data = joblib.load(file_path)
        
        # Verify this is a complete project file
        if project_data.get('project_type') != 'complete':
            # Try to handle legacy format
            if 'spectral_data' not in project_data:
                return None, "This appears to be a legacy model file without spectral data. Use 'Import Models' instead."
        
        # Set default values for missing keys (for backward compatibility)
        if 'auto_pls_components' not in project_data:
            project_data['auto_pls_components'] = False
        
        if 'current_derivative' not in project_data:
            project_data['current_derivative'] = 0
        
        if 'region_start' not in project_data:
            project_data['region_start'] = None
        
        if 'region_end' not in project_data:
            project_data['region_end'] = None
        
        # Convert wavenumbers back to numpy array
        if project_data.get('wavenumbers'):
            project_data['wavenumbers'] = np.array(project_data['wavenumbers'])
        
        # Convert spectral data back to numpy arrays
        if project_data.get('spectral_data'):
            for filename, spec_data in project_data['spectral_data'].items():
                spec_data['intensity'] = np.array(spec_data['intensity'])
        
        save_time = project_data.get('save_timestamp', 'Unknown')
        stats = {
            'models': len(project_data.get('pls_models', {})),
            'components': len(project_data.get('chemical_components', [])),
            'reference_values': len(project_data.get('reference_values', {})),
            'spectra': len(project_data.get('spectral_data', {}))
        }
        
        # Get derivative description
        derivative_names = {0: "Original", 1: "1st Derivative", 2: "2nd Derivative"}
        derivative_desc = derivative_names.get(project_data.get('current_derivative', 0), "Unknown")
        
        # Format region information
        region_info = ""
        if project_data.get('region_start') is not None and project_data.get('region_end') is not None:
            region_info = f"• Region: {project_data['region_start']:.0f} - {project_data['region_end']:.0f} cm⁻¹\n"
        
        # Auto PLS info
        auto_pls_status = "Enabled" if project_data.get('auto_pls_components', False) else "Disabled"
        
        message = (f"Complete project loaded successfully!\n"
                  f"• {stats['models']} trained models\n"
                  f"• {stats['components']} components\n"
                  f"• {stats['reference_values']} spectra with reference values\n"
                  f"• {stats['spectra']} spectral datasets\n"
                  f"• Derivative: {derivative_desc}\n"
                  f"{region_info}"
                  f"• Auto PLS Components: {auto_pls_status}\n"
                  f"• Saved: {save_time}")
        
        return project_data, message
    
    except Exception as e:
        return None, f"Error loading complete project: {str(e)}"

def save_reference_values_only(spectra_data, chemical_components, file_path):
    """
    Save only reference values in a lightweight format.
    
    Parameters:
    - spectra_data: Dictionary containing spectral data
    - chemical_components: List of component dictionaries
    - file_path: Path to save the reference values file
    
    Returns:
    - success: Boolean indicating if save was successful
    - message: Success or error message
    """
    try:
        # Extract reference values
        reference_values = {}
        if spectra_data:
            for filename, data in spectra_data.items():
                if data['refs']:
                    reference_values[filename] = data['refs']
        
        if not reference_values:
            return False, "No reference values found to save."
        
        # Create reference values data structure
        ref_data = {
            'data_type': 'reference_values',
            'chemical_components': chemical_components,
            'reference_values': reference_values,
            'save_timestamp': datetime.now().isoformat(),
            'version': '1.0'
        }
        
        # Save as JSON for easy reading/editing
        with open(file_path, 'w') as f:
            json.dump(ref_data, f, indent=2)
        
        stats = {
            'components': len(chemical_components),
            'reference_values': len(reference_values),
            'total_values': sum(len(refs) for refs in reference_values.values())
        }
        
        message = (f"Reference values saved successfully!\n"
                  f"• {stats['components']} components\n"
                  f"• {stats['reference_values']} spectra with reference values\n"
                  f"• {stats['total_values']} total reference values\n"
                  f"• Saved to: {file_path}")
        
        return True, message
    
    except Exception as e:
        return False, f"Error saving reference values: {str(e)}"

def load_reference_values_only(file_path):
    """
    Load reference values from a lightweight reference values file.
    
    Parameters:
    - file_path: Path to the reference values file to load
    
    Returns:
    - ref_data: Dictionary containing reference values data (or None if failed)
    - message: Success or error message
    """
    try:
        with open(file_path, 'r') as f:
            ref_data = json.load(f)
        
        # Verify this is a reference values file
        if ref_data.get('data_type') != 'reference_values':
            return None, "This file does not appear to be a reference values file."
        
        save_time = ref_data.get('save_timestamp', 'Unknown')
        stats = {
            'components': len(ref_data.get('chemical_components', [])),
            'reference_values': len(ref_data.get('reference_values', {})),
            'total_values': sum(len(refs) for refs in ref_data.get('reference_values', {}).values())
        }
        
        message = (f"Reference values loaded successfully!\n"
                  f"• {stats['components']} components\n"
                  f"• {stats['reference_values']} spectra with reference values\n"
                  f"• {stats['total_values']} total reference values\n"
                  f"• Saved: {save_time}")
        
        return ref_data, message
    
    except Exception as e:
        return None, f"Error loading reference values: {str(e)}"

def apply_loaded_reference_values(spectra_data, reference_values):
    """
    Apply loaded reference values to spectra data.
    
    Parameters:
    - spectra_data: Dictionary containing spectral data
    - reference_values: Dictionary of reference values by filename
    
    Returns:
    - updated_count: Number of spectra that had reference values applied
    - missing_spectra: List of filenames that have reference values but no matching spectra
    """
    updated_count = 0
    missing_spectra = []
    
    for filename, refs in reference_values.items():
        if filename in spectra_data:
            spectra_data[filename]['refs'] = refs
            updated_count += 1
        else:
            missing_spectra.append(filename)
    
    return updated_count, missing_spectra

def reconstruct_spectra_data(spectral_data, reference_values, wavenumbers):
    """
    Reconstruct the full spectra_data structure from saved project data.
    
    Parameters:
    - spectral_data: Dictionary of spectral data from saved project
    - reference_values: Dictionary of reference values from saved project
    - wavenumbers: Wavenumber axis array
    
    Returns:
    - spectra_data: Reconstructed spectra_data dictionary
    """
    spectra_data_reconstructed = {}
    
    for filename, spec_data in spectral_data.items():
        # Create a mock NDDataset for compatibility with existing code
        intensity = spec_data['intensity']
        
        # Create a basic mock nd object (just enough for plotting)
        class MockNDDataset:
            def __init__(self, intensity, wavenumbers):
                self.data = intensity
                self.x = type('obj', (object,), {'data': wavenumbers})()
        
        mock_nd = MockNDDataset(intensity, wavenumbers)
        
        spectra_data_reconstructed[filename] = {
            'nd': mock_nd,
            'intensity': intensity,
            'refs': reference_values.get(filename, {})
        }
    
    return spectra_data_reconstructed