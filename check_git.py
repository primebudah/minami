import subprocess

with open('check_git_output.txt', 'w') as f:
    # Verifica o log do git
    result = subprocess.run(['git', 'log', '--oneline', '-5'], capture_output=True, text=True)
    f.write("=== GIT LOG ===\n")
    f.write(result.stdout)
    f.write(result.stderr)
    
    # Verifica o conteudo do database.py no HEAD
    result = subprocess.run(['git', 'show', 'HEAD:database.py'], capture_output=True, text=True)
    lines = result.stdout.split('\n')
    f.write("\n=== LINHAS 45-85 do database.py no HEAD ===\n")
    for i in range(44, 85):
        if i < len(lines):
            f.write(f"{i+1}: {lines[i]}\n")

print("Output salvo em check_git_output.txt")
