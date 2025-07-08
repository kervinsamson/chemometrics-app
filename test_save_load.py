#!/usr/bin/env python3
"""
Test script for the new save/load functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logic.processing import (
    save_complete_project, load_complete_project, 
    save_reference_values_only, load_reference_values_only
)
import numpy as np

def test_save_load_functionality():
    """Test the save/load functionality with mock data"""
    print("Testing save/load functionality...")
    
    # Create mock data
    mock_spectra_data = {
        'spectrum1.spa': {
            'intensity': np.array([1.0, 2.0, 3.0, 4.0, 5.0]),
            'refs': {'Protein': 12.5, 'Moisture': 8.2},
            'nd': None  # Mock NDDataset
        },
        'spectrum2.spa': {
            'intensity': np.array([1.1, 2.1, 3.1, 4.1, 5.1]),
            'refs': {'Protein': 15.1, 'Moisture': 6.8},
            'nd': None  # Mock NDDataset
        }
    }
    
    mock_components = [
        {'name': 'Protein', 'abbrev': 'P', 'unit': '%', 'pls_components': 8},
        {'name': 'Moisture', 'abbrev': 'M', 'unit': '%', 'pls_components': 5}
    ]
    
    mock_pls_models = {
        'Protein': {'model': 'mock_model', 'scaler': 'mock_scaler'},
        'Moisture': {'model': 'mock_model', 'scaler': 'mock_scaler'}
    }
    
    mock_performance = {
        'Protein': {'r2_cv': 0.95, 'rmsecv': 0.8, 'pls_components': 8},
        'Moisture': {'r2_cv': 0.92, 'rmsecv': 0.6, 'pls_components': 5}
    }
    
    mock_wavenumbers = np.array([4000, 3000, 2000, 1000, 500])
    
    # Test complete project save
    print("\n1. Testing complete project save...")
    success, message = save_complete_project(
        mock_spectra_data, mock_components, mock_pls_models, 
        mock_performance, mock_wavenumbers, 1, 3000, 2000, 
        'test_complete_project.pkl'
    )
    
    if success:
        print("✓ Complete project save successful")
        print(f"  {message}")
    else:
        print("✗ Complete project save failed")
        print(f"  {message}")
        return False
    
    # Test complete project load
    print("\n2. Testing complete project load...")
    project_data, message = load_complete_project('test_complete_project.pkl')
    
    if project_data:
        print("✓ Complete project load successful")
        print(f"  {message}")
        print(f"  Loaded {len(project_data.get('chemical_components', []))} components")
        print(f"  Loaded {len(project_data.get('spectral_data', {}))} spectra")
    else:
        print("✗ Complete project load failed")
        print(f"  {message}")
        return False
    
    # Test reference values save
    print("\n3. Testing reference values save...")
    success, message = save_reference_values_only(
        mock_spectra_data, mock_components, 'test_reference_values.json'
    )
    
    if success:
        print("✓ Reference values save successful")
        print(f"  {message}")
    else:
        print("✗ Reference values save failed")
        print(f"  {message}")
        return False
    
    # Test reference values load
    print("\n4. Testing reference values load...")
    ref_data, message = load_reference_values_only('test_reference_values.json')
    
    if ref_data:
        print("✓ Reference values load successful")
        print(f"  {message}")
        print(f"  Loaded {len(ref_data.get('chemical_components', []))} components")
        print(f"  Loaded {len(ref_data.get('reference_values', {}))} reference sets")
    else:
        print("✗ Reference values load failed")
        print(f"  {message}")
        return False
    
    # Cleanup
    print("\n5. Cleaning up test files...")
    try:
        os.remove('test_complete_project.pkl')
        os.remove('test_reference_values.json')
        print("✓ Test files cleaned up")
    except:
        print("⚠ Could not remove test files")
    
    print("\n✅ All tests passed!")
    return True

if __name__ == "__main__":
    test_save_load_functionality()
