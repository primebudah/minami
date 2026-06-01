import subprocess
import sys

with open('c:/Users/user/Desktop/push_log.txt', 'w') as f:
    f.write("=== Git Status ===\n")
    result = subprocess.run(['git', 'status', '--short'], capture_output=True, text=True)
    f.write(result.stdout or "(no output)\n")
    f.write(result.stderr or "(no errors)\n")
    
    f.write("\n=== Git Log ===\n")
    result = subprocess.run(['git', 'log', '--oneline', '-3'], capture_output=True, text=True)
    f.write(result.stdout or "(no output)\n")
    
    f.write("\n=== Adding database.py ===\n")
    result = subprocess.run(['git', 'add', 'database.py'], capture_output=True, text=True)
    f.write(result.stdout or "(no output)\n")
    f.write(result.stderr or "(no errors)\n")
    
    f.write("\n=== Committing ===\n")
    result = subprocess.run(['git', 'commit', '-m', 'database.py v3 - SQLite conditional block'], capture_output=True, text=True)
    f.write(result.stdout or "(no output)\n")
    f.write(result.stderr or "(no errors)\n")
    
    f.write("\n=== Pushing ===\n")
    result = subprocess.run(['git', 'push', '-f', 'origin', 'main'], capture_output=True, text=True)
    f.write(result.stdout or "(no output)\n")
    f.write(result.stderr or "(no errors)\n")
    f.write(f"Return code: {result.returncode}\n")
    
    f.write("\n=== Done ===\n")

print("Output salvo em push_output.txt")
