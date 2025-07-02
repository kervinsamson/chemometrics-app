
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
    spectra_data = {}
    for file_path in glob.glob(os.path.join(glob.escape(folder_path), '*.spa')):
        filename = os.path.basename(file_path)
        try:
            nd = spc.read_spa(file_path)
            spectra_data[filename] = {'nd': nd, 'intensity': nd.data.squeeze(), 'refs': {}}
        except Exception as e:
            print(f"Error loading {filename}: {e}")
    return spectra_data

def train_pls_model(spectra_data, target_component, num_components, current_derivative):
    X_list, y_list = [], []
    for filename, data in spectra_data.items():
        ref_val = data['refs'].get(target_component)
        if ref_val is not None:
            X_list.append(get_processed_intensity(data['intensity'], current_derivative))
            y_list.append(ref_val)

    if len(X_list) < 5:
        return None, None, None, f"Need at least 5 reference values for '{target_component}' to train a model."

    X, y = np.array(X_list), np.array(y_list)
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
    if derivative_order == 0:
        return original_intensity
    
    window_length, polyorder = 11, 2
    if derivative_order == 1:
        return savgol_filter(original_intensity, window_length, polyorder, deriv=1)
    elif derivative_order == 2:
        return savgol_filter(original_intensity, window_length, polyorder, deriv=2)
    return original_intensity
