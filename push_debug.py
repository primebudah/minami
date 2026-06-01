import subprocess
import os

cwd = r'c:\Users\user\Desktop\Mianami Service'

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    print(f"=== {cmd} ===")
    print(f"stdout: {result.stdout}")
    print(f"stderr: {result.stderr}")
    print(f"rc: {result.returncode}")
    print()
    return result

print("Iniciando push...")

# Verifica status
run("git status --short")

# Adiciona arquivos
run("git add -A")

# Commit
result = run('git commit -m "Fix openai import and Supabase error handling"')
if result.returncode != 0 and "nothing to commit" not in result.stderr:
    print("ERRO no commit!")
else:
    # Push
    run("git push origin main")

print("Done!")
