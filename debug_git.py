import subprocess
import os

def run(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=r'c:\Users\user\Desktop\Mianami Service')
    return f"Command: {cmd}\nstdout: {result.stdout}\nstderr: {result.stderr}\nrc: {result.returncode}\n\n"

output = "=== GIT DEBUG ===\n\n"
output += run("git status --short")
output += run("git log --oneline -3")
output += run("git remote -v")
output += run("git branch -vv")
output += run("git push origin main --dry-run 2>&1")

with open(r'c:\Users\user\Desktop\git_debug.txt', 'w') as f:
    f.write(output)

print("Debug info salvo em c:\\Users\\user\\Desktop\\git_debug.txt")
