@echo off
IF "%1"=="load" (
    echo 🚀 Running ETL pipeline...
    python src/etl/loader.py
    goto :eof
)
IF "%1"=="ratios" (
    echo 🧮 Calculating financial ratios...
    python src/kpi/ratios.py
    goto :eof
)
IF "%1"=="test" (
    echo 🧪 Running test suite...
    python -m pytest tests/ --html=reports/pytest_report.html -v
    goto :eof
)
IF "%1"=="report" (
    echo 🖨️ Generating all PDFs...
    python src/reports/tearsheet.py
    python src/reports/sector_report.py
    python src/reports/portfolio_summary.py
    goto :eof
)
IF "%1"=="dashboard" (
    echo 📊 Starting Streamlit dashboard...
    streamlit run src/dashboard/app.py
    goto :eof
)
IF "%1"=="api" (
    echo ⚡ Starting FastAPI server...
    uvicorn src.api.main:app --port 8000 --reload
    goto :eof
)
IF "%1"=="clean" (
    echo 🧹 Cleaning up cache files...
    FOR /d /r . %%d in (__pycache__) DO @IF EXIST "%%d" rd /s /q "%%d"
    FOR /d /r . %%d in (.pytest_cache) DO @IF EXIST "%%d" rd /s /q "%%d"
    echo ✅ Clean complete.
    goto :eof
)

echo Usage: make [load^|ratios^|test^|report^|dashboard^|api^|clean]