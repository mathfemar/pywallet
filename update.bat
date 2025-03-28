@echo off
setlocal

REM Solicita o número da versão
set /p VERSAO=Digite o número da versão (ex: 0.0.1): 

REM Vai para a branch walletgaza
git checkout walletgaza

REM Atualiza a branch local
git pull origin walletgaza

REM Adiciona todas as mudanças
git add .

REM Faz o commit com a versão
git commit -m "Versão v%VERSAO%"

REM Envia para o fork
git push origin walletgaza

echo Branch walletgaza atualizada com sucesso com a versão v%VERSAO%!
pause
