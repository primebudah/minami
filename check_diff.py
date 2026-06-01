import subprocess

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=r'c:\Users\user\Desktop\Mianami Service')
    return f"Command: {cmd}\nstdout: {result.stdout}\nstderr: {result.stderr}\nrc: {result.returncode}\n\n"

output = "=== GIT DIFF CHECK ===\n\n"

# Ver diferenças entre HEAD e origin/main
output += run("git fetch origin main")
output += run("git diff HEAD origin/main --stat")
output += run("git log HEAD..origin/main --oneline")
output += run("git log origin/main..HEAD --oneline")

# Mostrar o conteúdo do database.py local (primeiras linhas)
output += "\n=== Local database.py (first 10 lines) ===\n"
with open(r'c:\Users\user\Desktop\Mianami Service\database.py', 'r') as f:
    lines = f.readlines()[:10]
    for i, line in enumerate(lines, 1):
        output += f"{i}: {line}"

# Tentar fazer o push forçado
output += "\n\n=== Forçando push ===\n"
output += run("git push origin main --force-with-lease 2>&1")

with open(r'c:\Users\user\Desktop\diff_check.txt', 'w', encoding='utf-8') as f:
    f.write(output)

print("Diff check salvo em c:\\Users\\user\\Desktop\\diff_check.txt")
