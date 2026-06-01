@echo off
cd /d "c:\Users\user\Desktop\Mianami Service"
echo Status:
git status --short
echo.
echo Adicionando...
git add -A
echo.
echo Committing...
git commit -m "Fix openai import protection"
echo.
echo Pushing...
git push origin main
echo.
echo Done!
pause
