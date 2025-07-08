# Complete Project Save/Load Functionality Documentation

## Overview
Your chemometrics application now has comprehensive save/load functionality that preserves the **exact state** of the application, ensuring that when you load a project, it looks exactly like when you saved it.

## What Gets Saved and Restored

### 1. **Processing Settings**
- **Derivative Selection**: Whether you're viewing Original, 1st Derivative, or 2nd Derivative spectra
- **Region Selection**: Start and end wavenumbers for spectral region analysis
- **Wavenumber Axis**: The complete wavenumber scale for proper plotting

### 2. **UI State**
- **Auto PLS Components Checkbox**: Whether automatic PLS component selection is enabled or disabled
- **Component Table**: All chemical components with their settings (name, abbreviation, unit, PLS components, CV folds)
- **Derivative Buttons**: Which derivative button is selected/highlighted
- **Region Input Fields**: The exact values in the region start/end input fields

### 3. **Data and Models**
- **Spectral Data**: All loaded .spa files with their intensity values
- **Reference Values**: All manually entered reference values for each spectrum
- **Trained Models**: All PLS models with their scalers and parameters
- **Model Performance**: R² CV, RMSECV, and optimal component counts for each model

### 4. **Metadata**
- **Save Timestamp**: When the project was saved
- **Version Information**: For future compatibility
- **File Structure**: Organized data for efficient loading

## How It Works

### Saving (Save Complete Project)
```python
# Called when you click "Save Complete Project"
save_complete_project(
    spectra_data,           # Your loaded spectra
    chemical_components,    # Components from the table
    pls_models,            # Trained models
    model_performance,     # Performance metrics
    wavenumbers,           # X-axis data
    current_derivative,    # 0=Original, 1=1st, 2=2nd
    region_start,          # Region start wavenumber
    region_end,            # Region end wavenumber
    auto_pls_components,   # Checkbox state
    file_path             # Where to save
)
```

### Loading (Load Complete Project)
```python
# Called when you click "Load Complete Project"
project_data, message = load_complete_project(file_path)

# Then the UI automatically restores:
# - All data and models
# - Derivative setting and button highlighting
# - Region values in input fields
# - Auto PLS checkbox state
# - Component table with proper formatting
# - Spectral plot with correct processing applied
```

## UI Restoration Details

### Derivative Buttons
- The correct derivative button becomes highlighted/checked
- Spectra are plotted with the saved derivative processing
- Button states match the saved derivative setting

### Region Selection
- Start and end wavenumber input fields are populated
- The spectral plot reflects any region-based analysis
- Region boundaries are preserved for model training

### Auto PLS Components
- Checkbox state is restored exactly as saved
- If enabled, the PLS Components column shows "Auto" and is non-editable
- If disabled, the column shows actual values and is editable
- Component table formatting matches the saved state

### Component Table
- All chemical components are restored with their exact settings
- PLS components and CV folds values are preserved
- Table appearance matches the auto PLS setting

## File Format
- Files are saved as `.pkl` (Python pickle) format
- Compatible with existing model files
- Includes version information for future updates
- Efficiently stores both data and state information

## Usage Instructions

### To Save Your Work:
1. Set up your analysis exactly how you want it:
   - Load your spectra
   - Enter reference values
   - Choose derivative setting (Original, 1st, 2nd)
   - Set region boundaries if needed
   - Configure auto PLS components as desired
   - Train your models
2. Click "Save Complete Project"
3. Choose a filename (e.g., `my_analysis_complete_project.pkl`)

### To Resume Your Work:
1. Click "Load Complete Project"
2. Select your saved `.pkl` file
3. Confirm the load operation
4. Your application will look exactly as you left it:
   - Same derivative setting
   - Same region settings
   - Same auto PLS checkbox state
   - Same spectral data and models
   - Same component configuration

## Benefits
- **Exact State Restoration**: No need to remember or reconfigure settings
- **Efficient Workflow**: Pick up exactly where you left off
- **Complete Data Preservation**: All models, performance metrics, and settings saved
- **Future-Proof**: Version tracking ensures compatibility with updates
- **User-Friendly**: Simple save/load buttons with clear feedback

## Testing
The functionality has been thoroughly tested with various state combinations:
- Different derivative settings
- Various region configurations
- Auto PLS enabled/disabled states
- Multiple spectral datasets
- Complex model configurations

Your save/load functionality ensures that the application state is preserved completely, making it easy to resume work sessions with zero configuration time.
