@echo off
cd /d "c:\Users\user\Desktop\Mianami Service"
git add -A
git commit -m "Fix listar_clientes returns DataFrame"
git push origin main --force
echo Done
