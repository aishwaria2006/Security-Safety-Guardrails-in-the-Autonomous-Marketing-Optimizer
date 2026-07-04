@echo off
echo ====================================================================
echo   Marketing AI Hub - Running Twin Innovators Modules
echo ====================================================================
echo.
echo Setting environment variables (UTF-8 encoding and custom python library path)...
set PYTHONIOENCODING=utf-8
set PYTHONPATH=d:\python_packages;%PYTHONPATH%

echo.
echo Installing Gradio to D:\python_packages due to low space on C: drive...
pip install --target=d:\python_packages gradio
echo.
echo Starting all modules in separate windows...
echo.

:: Core Modules
start "Sentiment Tracker [Port 5000]" cmd /k "python last.py"
start "Smart Lead Scorer [Port 5002]" cmd /k "python final.py"
start "Content Engine [Port 5004]" cmd /k "python main.py"
start "Campaign Generator [Port 5005]" cmd /k "python mailingcampaign.py"
start "Digital Twin [Port 5006]" cmd /k "python digital.py"
start "Strategic Engine [Port 5010]" cmd /k "python meta.py"
start "Poster Creator [Port 9000]" cmd /k "python postergen.py"

:: Side Analytics Modules
start "Market Predictor [Port 4000]" cmd /k "python competative_market.py"
start "Inflation Tracker [Port 3000]" cmd /k "python inflasion.py"
start "Demand Forecaster [Port 8000]" cmd /k "python demand_supply.py"

echo.
echo ====================================================================
echo   All 10 modules have been launched!
echo   To access the application:
echo   1. Make sure your .env file is configured with the required keys.
echo   2. Open login.html in your browser.
echo ====================================================================
echo.
pause
