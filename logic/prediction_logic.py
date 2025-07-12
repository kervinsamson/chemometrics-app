import numpy as np
from .processing import get_processed_intensity


def predict_from_model(prediction_model_data, prediction_spectra_data):
    """
    Predict component values for new spectra using a trained PLS model.

    Args:
        prediction_model_data (dict): The loaded .pkl model data containing model parameters and settings.
        prediction_spectra_data (dict): The new spectra data to predict, keyed by filename.

    Returns:
        tuple:
            - dict: A dictionary where keys are filenames and values are dicts of predicted component values.
            - str: An error message, if any.
    """
    try:
        # Retrieve processing settings from the loaded model
        settings = prediction_model_data['processing_settings']
        derivative_order = settings.get('derivative_order', 0)
        region_start = settings.get('region_start')
        region_end = settings.get('region_end')
        model_wavenumbers = prediction_model_data['wavenumbers']

        # Convert wavenumbers to numpy array if necessary
        if isinstance(model_wavenumbers, list):
            model_wavenumbers = np.array(model_wavenumbers)

        # Retrieve components and models
        pls_models = prediction_model_data['pls_models']
        component_names = [comp['name'] for comp in prediction_model_data['chemical_components']]

        # Prepare region mask if applicable
        region_mask = None
        if region_start is not None and region_end is not None:
            start_wn = min(region_start, region_end)
            end_wn = max(region_start, region_end)
            region_mask = (model_wavenumbers >= start_wn) & (model_wavenumbers <= end_wn)

        predictions = {}
        sorted_filenames = sorted(prediction_spectra_data.keys())

        for filename in sorted_filenames:
            spectrum_data = prediction_spectra_data[filename]
            original_intensity = spectrum_data['intensity']

            # 1. Apply the same preprocessing as the model
            processed_intensity = get_processed_intensity(original_intensity, derivative_order)

            # 2. Apply region mask if it exists
            if region_mask is not None:
                sliced_intensity = processed_intensity[region_mask]
            else:
                sliced_intensity = processed_intensity

            # 3. Reshape the single spectrum to be a 2D array (1, n_features)
            if sliced_intensity.ndim == 1:
                reshaped_intensity = sliced_intensity.reshape(1, -1)
            else:
                reshaped_intensity = sliced_intensity

            predictions[filename] = {}
            for comp_name in component_names:
                if comp_name in pls_models:
                    model_info = pls_models[comp_name]
                    scaler = model_info['scaler']
                    model = model_info['model']

                    # Scale the sliced data using the component's corresponding scaler
                    scaled_intensity = scaler.transform(reshaped_intensity)

                    # Make the prediction
                    predicted_value = model.predict(scaled_intensity)
                    predictions[filename][comp_name] = predicted_value[0]

                else:
                    predictions[filename][comp_name] = "Model or Scaler not found"

        return predictions, None

    except Exception as e:
        return None, f"An unexpected error occurred during prediction: {e}"
