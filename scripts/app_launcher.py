# scripts/app_launcher.py
import runpy, sys

# Pass through to `streamlit run app/streamlit_app.py`
# This keeps the same Python env that PyInstaller bundles.

sys.argv = [
    "streamlit",
    "run",
    "app/streamlit_app.py",
    "--server.headless=true",
    "--browser.gatherUsageStats=false",
]

runpy.run_module("streamlit", run_name="__main__")