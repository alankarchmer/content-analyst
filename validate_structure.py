#!/usr/bin/env python3
"""
Validation script to check that all required files exist and have expected structure.
This can be run before installing dependencies.
"""

import os
import sys

def check_file(path, description):
    """Check if a file exists and is non-empty."""
    if not os.path.exists(path):
        print(f"❌ MISSING: {description} - {path}")
        return False
    
    size = os.path.getsize(path)
    if size == 0:
        print(f"⚠️  EMPTY: {description} - {path}")
        return False
    
    print(f"✅ OK: {description} ({size:,} bytes)")
    return True

def main():
    """Run validation checks."""
    print("🔍 Validating Magic Slate Project Structure...\n")
    
    all_ok = True
    
    # Core backend modules
    print("📦 Backend Modules:")
    backend_files = [
        ("magicslate/__init__.py", "Package init"),
        ("magicslate/data_generation.py", "Data generation"),
        ("magicslate/data_models.py", "Data models"),
        ("magicslate/loaders.py", "Data loaders"),
        ("magicslate/assumptions.py", "Business assumptions"),
        ("magicslate/metrics.py", "Core metrics"),
        ("magicslate/title_scorecard.py", "Title scorecard"),
        ("magicslate/portfolio_dashboard.py", "Portfolio dashboard"),
        ("magicslate/windowing_simulator.py", "Windowing simulator"),
        ("magicslate/greenlight_forecast.py", "Greenlight forecast"),
        ("magicslate/exports.py", "Excel exports"),
    ]
    
    for path, desc in backend_files:
        all_ok &= check_file(path, desc)
    
    print("\n🎬 Streamlit Application:")
    app_files = [
        ("app/__init__.py", "App package init"),
        ("app/streamlit_app.py", "Main entrypoint"),
    ]
    
    for path, desc in app_files:
        all_ok &= check_file(path, desc)
    
    print("\n📄 Streamlit Pages:")
    page_files = [
        ("app/pages/01_Overview.py", "Overview page"),
        ("app/pages/02_Title_Explorer.py", "Title Explorer page"),
        ("app/pages/03_Portfolio_Dashboard.py", "Portfolio Dashboard page"),
        ("app/pages/04_Windowing_Lab.py", "Windowing Lab page"),
        ("app/pages/05_Greenlight_Studio.py", "Greenlight Studio page"),
        ("app/pages/06_Data_&_Assumptions.py", "Data & Assumptions page"),
    ]
    
    for path, desc in page_files:
        all_ok &= check_file(path, desc)
    
    print("\n📋 Configuration Files:")
    config_files = [
        ("requirements.txt", "Python dependencies"),
        ("README.md", "Main documentation"),
        ("QUICKSTART.md", "Quick start guide"),
    ]
    
    for path, desc in config_files:
        all_ok &= check_file(path, desc)
    
    print("\n📁 Directories:")
    dirs = ["data", "magicslate", "app", "app/pages"]
    for d in dirs:
        if os.path.isdir(d):
            print(f"✅ OK: {d}/ directory exists")
        else:
            print(f"❌ MISSING: {d}/ directory")
            all_ok = False
    
    print("\n" + "="*60)
    
    if all_ok:
        print("✨ SUCCESS! All required files are present.")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Run the app: streamlit run app/streamlit_app.py")
        return 0
    else:
        print("❌ VALIDATION FAILED! Some files are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
