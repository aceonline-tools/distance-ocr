@echo off
pip install -r requirements-windows.txt
pyinstaller --onefile --name ocr_mouse --console ocr_mouse.py
echo.
echo Built: dist\ocr_mouse.exe
pause
