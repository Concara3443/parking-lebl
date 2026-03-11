@echo off
chcp 65001 >nul
title LEBL Parking System

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Python no encontrado.
    echo  Abriendo Microsoft Store para instalarlo...
    echo.
    start ms-windows-store://search/?query=Python
    echo  Instala Python, marca "Add Python to PATH" y vuelve a abrir este archivo.
    echo.
    pause
    exit /b 1
)

python "%~dp0parking_finder.py"
if %errorlevel% neq 0 pause
