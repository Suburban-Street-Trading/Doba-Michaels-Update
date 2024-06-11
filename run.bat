@echo off
SET ENV_DIR=env

:: Step 1: Create a python virtual environment if an env directory does not exist
IF NOT EXIST %ENV_DIR% (
    python -m venv %ENV_DIR%
)

:: Step 2: Activate the virtual environment
CALL %ENV_DIR%\Scripts\activate

:: Step 3: Install any requirements from the requirements.txt file if they are not already installed
IF EXIST requirements.txt (
    pip install -r requirements.txt
)

:: Step 4: Run the main.py file
python main.py

:: Step 5: Deactivate the virtual environment (optional)
CALL deactivate
