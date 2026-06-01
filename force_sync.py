import subprocess
import os

cwd = r'c:\Users\user\Desktop\Mianami Service'

def run(cmd):
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    print(f"RC: {result.returncode}")
    if result.stdout:
        print(f"OUT: {result.stdout[:500]}")
    if result.stderr:
        print(f"ERR: {result.stderr[:500]}")
    return result

# Verifica status
run("git status")

# Adiciona arquivos modificados
run("git add database.py database_supabase.py ocr_service.py")

# Cria commit
result = run('git commit -m "Fix: listar_clientes returns DataFrame pandas"')

# Push forçado
result = run("git push origin main --force")

if result.returncode == 0:
    print("\n✅ Push realizado com sucesso!")
else:
    print(f"\n❌ Erro no push: {result.stderr}")
