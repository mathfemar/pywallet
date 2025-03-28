@echo off
setlocal

REM Solicita o numero da versao
set /p VERSAO=Digite o número da versao (ex: 0.0.1): 

REM Vai para a branch walletgaza
git checkout walletgaza

REM Atualiza a branch local
git pull origin walletgaza

REM Adiciona todas as mudanças
git add .

REM Faz o commit com a versao
git commit -m "Versao v%VERSAO%"

REM Envia para o fork
git push origin walletgaza

echo Branch walletgaza atualizada com sucesso com a versao v%VERSAO%!
pause
