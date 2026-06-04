@echo off
chcp 65001 >nul

:main_menu
cls
echo ====================================================================
echo                          Silero Portable
echo ====================================================================
echo 1. Start Silero TTS
echo 2. Install/Re-install Silero
echo 3. Update Silero
echo ====================================================================
echo By NeiroVlad (oti.by), 2026
echo ====================================================================
set /p choice=Choose action 1-3:
if "%choice%"=="1" goto start_Silero
if "%choice%"=="2" goto install_Silero
if "%choice%"=="3" goto update_Silero
echo Wrong choice. Please, try again.
pause
goto main_menu

:install_Silero
cls
REM Paths
set "ROOT=%CD%"
set "TOOLS=%ROOT%\tools"
set "CONDA_DIR=%TOOLS%\miniconda"
set "VENV=%ROOT%\.venv"
set "CACHE=%ROOT%\cache"

REM Cache directories (все кэши внутри папки проекта)
set "UV_CACHE_DIR=%CACHE%\uv"
set "UV_PYTHON_CACHE_DIR=%CACHE%\uv\python"
set "UV_TOOL_DIR=%CACHE%\uv\tools"
set "UV_PYTHON_INSTALL_DIR=%CACHE%\uv\python-installs"
set "PIP_CACHE_DIR=%CACHE%\pip"
set "HF_HOME=%CACHE%\huggingface"
set "TORCH_HOME=%CACHE%\torch"

REM UV + pip режим копирования (для портативности)
set "UV_LINK_MODE=copy"

set "GIT_EXE=%TOOLS%\PortableGit\bin\git.exe"
set "PORTABLEGIT_EXE=%TOOLS%\PortableGit.7z.exe"
set "MINICONDA_EXE=%TOOLS%\miniconda.exe"
set "UV_EXE=%TOOLS%\uv.exe"

set "GIT_URL=https://github.com/git-for-windows/git/releases/download/v2.42.0.windows.1/PortableGit-2.42.0-64-bit.7z.exe"
set "CONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-py310_24.9.2-0-Windows-x86_64.exe"
set "UV_URL=https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"

echo Root: %ROOT%
echo Tools: %TOOLS%
echo Cache: %CACHE%
echo UV cache: %UV_CACHE_DIR%
echo PIP cache: %PIP_CACHE_DIR%

REM Re-install checkup
if exist "%VENV%\python.exe" (
    echo Found existed Silero.
    choice /C YN /M "Would you agree to re-install it?"
    if errorlevel 2 (
        echo Quit to main menu...
        goto main_menu
    )
    if errorlevel 1 (
        echo Deleting old installation...
        if exist "%VENV%" rmdir /s /q "%VENV%" 2>nul
        if exist "%CACHE%" rmdir /s /q "%CACHE%" 2>nul
        if exist "%TOOLS%" rmdir /s /q "%TOOLS%" 2>nul
        echo Old folders deleted. Starting re-installation...
    )
)

REM Create required folders
if not exist "%TOOLS%" mkdir "%TOOLS%"
if not exist "%CACHE%" mkdir "%CACHE%"
if not exist "%UV_CACHE_DIR%" mkdir "%UV_CACHE_DIR%"
if not exist "%UV_PYTHON_CACHE_DIR%" mkdir "%UV_PYTHON_CACHE_DIR%"
if not exist "%UV_TOOL_DIR%" mkdir "%UV_TOOL_DIR%"
if not exist "%UV_PYTHON_INSTALL_DIR%" mkdir "%UV_PYTHON_INSTALL_DIR%"
if not exist "%PIP_CACHE_DIR%" mkdir "%PIP_CACHE_DIR%"
if not exist "%HF_HOME%" mkdir "%HF_HOME%"
if not exist "%TORCH_HOME%" mkdir "%TORCH_HOME%"

REM Download PortableGit
if exist "%GIT_EXE%" goto :git_present
echo Downloading PortableGit...
powershell -NoProfile -NonInteractive -Command "Invoke-WebRequest -Uri '%GIT_URL%' -OutFile '%PORTABLEGIT_EXE%'"
pushd "%TOOLS%"
powershell -NoProfile -NonInteractive -Command "Start-Process -FilePath '%PORTABLEGIT_EXE%' -ArgumentList '-y','-gm2' -Wait -NoNewWindow"
popd
del "%PORTABLEGIT_EXE%" >nul 2>&1
:git_present
echo PortableGit ready.

REM Download Miniconda
if exist "%CONDA_DIR%\Scripts\conda.exe" goto :conda_present
echo Downloading Miniconda...
powershell -NoProfile -NonInteractive -Command "Invoke-WebRequest -Uri '%CONDA_URL%' -OutFile '%MINICONDA_EXE%'"
start /wait "" "%MINICONDA_EXE%" /S /D=%CONDA_DIR%
del "%MINICONDA_EXE%" >nul 2>&1
:conda_present
echo Conda ready.

REM Download UV
if exist "%UV_EXE%" goto :uv_present
echo Downloading UV package manager...
set "UV_ZIP=%TOOLS%\uv.zip"
powershell -NoProfile -NonInteractive -Command "Invoke-WebRequest -Uri '%UV_URL%' -OutFile '%UV_ZIP%'"
powershell -NoProfile -NonInteractive -Command "Expand-Archive -Path '%UV_ZIP%' -DestinationPath '%TOOLS%' -Force"
del "%UV_ZIP%" >nul 2>&1
:uv_present
echo UV ready: %UV_EXE%

REM Update PATH
set "OLD_PATH=%PATH%"
set "PATH=%CONDA_DIR%\Scripts;%CONDA_DIR%;%TOOLS%\PortableGit\cmd;%TOOLS%;%PATH%"

REM Create conda env
if exist "%VENV%\python.exe" goto :env_present
echo Creating conda environment at %VENV% (Python 3.11)...
"%CONDA_DIR%\Scripts\conda.exe" create -p "%VENV%" python=3.11 -y --quiet
call "%CONDA_DIR%\Scripts\activate.bat" "%VENV%"
:env_present
echo Environment ready.

REM Activate env
call "%CONDA_DIR%\Scripts\activate.bat" "%VENV%"

REM Install UV into the environment
echo Installing UV into virtual environment...
python -m pip install uv --quiet

REM Install dependencies: torch+cu128, torchaudio+cu128, omegaconf, gradio
echo Installing dependencies with CUDA 12.8 support...

REM Uninstall CPU versions if present
uv pip uninstall torch torchvision torchaudio --python "%VENV%\python.exe" 2>nul

REM Install PyTorch 2.8.0 + cu128
echo Installing PyTorch with CUDA 12.8 support...
uv pip install torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128 --python "%VENV%\python.exe"

REM Install remaining dependencies
echo Installing omegaconf, gradio...
uv pip install omegaconf "gradio>=6.0" --python "%VENV%\python.exe"

REM Check for silero_ui.py
if not exist "%ROOT%\silero_ui.py" (
    echo [WARNING] silero_ui.py not found!
    echo Please create silero_ui.py manually in: %ROOT%
    echo See the provided code above.
    pause
    goto main_menu
)

REM НЕ удаляем кэш — он нужен для портативности!
REM rmdir /s /q "%CACHE%\." 2>nul

REM Restore PATH
set "PATH=%OLD_PATH%"
echo [INFO] Installation finished.
echo [INFO] UV cache: %UV_CACHE_DIR%
echo [INFO] PIP cache: %PIP_CACHE_DIR%
echo [INFO] HF cache: %HF_HOME%
echo [INFO] Torch cache: %TORCH_HOME%
pause
goto main_menu

:update_Silero
set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"

set "TOOLS=%ROOT%\tools"
set "CONDA_DIR=%TOOLS%\miniconda"
set "VENV=%ROOT%\.venv"
set "CACHE=%ROOT%\cache"

REM Cache directories (все кэши внутри папки проекта)
set "UV_CACHE_DIR=%CACHE%\uv"
set "UV_PYTHON_CACHE_DIR=%CACHE%\uv\python"
set "UV_TOOL_DIR=%CACHE%\uv\tools"
set "UV_PYTHON_INSTALL_DIR=%CACHE%\uv\python-installs"
set "PIP_CACHE_DIR=%CACHE%\pip"
set "HF_HOME=%CACHE%\huggingface"
set "TORCH_HOME=%CACHE%\torch"

REM UV + pip режим копирования
set "UV_LINK_MODE=copy"

set "PATH=%CONDA_DIR%\Scripts;%CONDA_DIR%;%TOOLS%\PortableGit\cmd;%TOOLS%;%PATH%"

REM === Checkup ===
if not exist "%VENV%\python.exe" (
    echo [INFO] Silero is not installed. Launch installing...
    goto install_Silero
)

cls
call "%CONDA_DIR%\Scripts\activate.bat" "%VENV%"
cd /d "%ROOT%"

echo [INFO] Updating PyTorch with CUDA 12.8 support...
uv pip uninstall torch torchvision torchaudio --python "%VENV%\python.exe" 2>nul
uv pip install torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128 --python "%VENV%\python.exe"

echo [INFO] Updating remaining dependencies...
uv pip install --upgrade omegaconf "gradio>=6.0" --python "%VENV%\python.exe"

if %ERRORLEVEL% == 0 goto :done_update

echo [WARN] Update failed, retrying...
uv pip install torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128 --python "%VENV%\python.exe"
uv pip install --upgrade omegaconf "gradio>=6.0" --python "%VENV%\python.exe"

:done_update
echo [INFO] Update finished.
echo [INFO] UV cache: %UV_CACHE_DIR%
echo [INFO] PIP cache: %PIP_CACHE_DIR%
pause
goto main_menu

:start_Silero
cls
set "ROOT=%CD%"
set "CACHE=%ROOT%\cache"

REM Cache directories (все кэши внутри папки проекта)
set "UV_CACHE_DIR=%CACHE%\uv"
set "PIP_CACHE_DIR=%CACHE%\pip"
set "XDG_CACHE_HOME=%ROOT%\cache"
set "HF_HOME=%XDG_CACHE_HOME%\huggingface"
set "TORCH_HOME=%XDG_CACHE_HOME%\torch"
set "VENV=%ROOT%\.venv"

REM UV режим копирования
set "UV_LINK_MODE=copy"

if not exist "%VENV%\python.exe" (
    echo [ERROR] Virtual environment not found. Please install Silero before starting.
    pause
    goto main_menu
)

if not exist "%ROOT%\silero_ui.py" (
    echo [ERROR] silero_ui.py not found in %ROOT%
    pause
    goto main_menu
)

call "%~dp0tools\miniconda\Scripts\activate.bat" "%~dp0.venv"

echo [INFO] Starting Silero TTS...
echo [INFO] If you're launching Silero first time, models will be downloaded for using them offline.
echo [INFO] Browser will open automatically when server is ready.
echo [INFO] Press Ctrl+C or close this window to stop.
echo [INFO] UV cache: %UV_CACHE_DIR%
echo [INFO] HF cache: %HF_HOME%

REM Run Python in foreground (same window) - stops when window closes
python "%ROOT%\silero_ui.py"

echo.
echo [INFO] Silero stopped.
pause
goto main_menu