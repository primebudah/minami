import requests
import base64
import json

# Configurações
REPO = "primebudah/minami-service"
BRANCH = "main"
TOKEN = input("Digite seu token do GitHub: ")

# Ler o conteúdo do arquivo local
with open('database.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Codificar em base64
content_b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')

# Primeiro, obter o SHA do arquivo atual
url_get = f"https://api.github.com/repos/{REPO}/contents/database.py?ref={BRANCH}"
headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

response = requests.get(url_get, headers=headers)
print(f"GET status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    current_sha = data['sha']
    print(f"Current SHA: {current_sha}")
    
    # Atualizar o arquivo
    url_put = f"https://api.github.com/repos/{REPO}/contents/database.py"
    payload = {
        "message": "database.py v3 - FIX SQLite conditional block via API",
        "content": content_b64,
        "sha": current_sha,
        "branch": BRANCH
    }
    
    response = requests.put(url_put, headers=headers, json=payload)
    print(f"PUT status: {response.status_code}")
    print(f"Response: {response.text}")
else:
    print(f"Erro ao obter arquivo: {response.text}")
