@echo off
chcp 65001 >nul
title Maquete Smart City - deixe esta janela aberta
cd /d "%~dp0"

rem Se o servidor ja estiver rodando, so abre o site.
curl -s -o nul http://localhost:8000/api/dados && (start http://localhost:8000 & exit /b)

rem Confere se o Python esta instalado.
where python >nul 2>nul || (echo Python nao encontrado. Instale em https://www.python.org/downloads/ marcando "Add python.exe to PATH". & pause & exit /b)

rem Instala as bibliotecas na primeira vez (precisa de internet so nessa vez).
python -c "import fastapi, uvicorn, serial" 2>nul || (echo Instalando bibliotecas... & python -m pip install -r requirements.txt)

echo.
echo Servidor ligado. Pode plugar o Arduino a qualquer momento: ele e encontrado sozinho.
echo Deixe esta janela aberta durante a apresentacao. Para desligar, feche a janela.
echo.
start "" cmd /c "timeout /t 3 >nul & start http://localhost:8000"
python servidor.py %*
echo.
echo O servidor parou. Confira o cabo USB e feche o Monitor Serial da Arduino IDE.
pause
