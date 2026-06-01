#!/usr/bin/env python3
import subprocess
import sys

def run(cmd):
    print(f">>> {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, 
                          cwd=r'c:\Users\user\Desktop\Mianami Service')
    print(f"RC: {result.returncode}")
    if result.stdout:
        print(f"OUT: {result.stdout}")
    if result.stderr:
        print(f"ERR: {result.stderr}")
    return result

# Verificar status
run("git status --short")

# Adicionar todos
run("git add -A")

# Commit
result = run('git commit -m "Fix: protege import openai e melhora erros Supabase"')

# Push
result = run("git push origin main")
print(f"\nPush finalizado com RC={result.returncode}")
