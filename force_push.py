import subprocess
import sys

def run_cmd(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
    return result.stdout, result.stderr, result.returncode

print("=== Verificando git remote ===")
stdout, stderr, rc = run_cmd("git remote -v")
print(f"stdout: {stdout}")
print(f"stderr: {stderr}")

print("\n=== Verificando branch atual ===")
stdout, stderr, rc = run_cmd("git branch -v")
print(f"stdout: {stdout}")

print("\n=== Adicionando database.py ===")
stdout, stderr, rc = run_cmd("git add database.py")
print(f"stdout: {stdout}")
print(f"stderr: {stderr}")

print("\n=== Commit ===")
stdout, stderr, rc = run_cmd('git commit -m "database.py v3 FIX"')
print(f"stdout: {stdout}")
print(f"stderr: {stderr}")

print("\n=== Push forçado ===")
stdout, stderr, rc = run_cmd("git push origin main --force-with-lease")
print(f"stdout: {stdout}")
print(f"stderr: {stderr}")
print(f"return code: {rc}")

if rc != 0:
    print("\n=== Tentando push normal ===")
    stdout, stderr, rc = run_cmd("git push origin main")
    print(f"stdout: {stdout}")
    print(f"stderr: {stderr}")
    print(f"return code: {rc}")
