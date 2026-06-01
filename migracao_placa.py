#!/usr/bin/env python3
"""
Migração: Adiciona coluna 'placa' se não existir (bancos antigos)
"""

with open('database.py', 'r', encoding='utf-8') as f:
    c = f.read()

# Adiciona função de migração após inicializar_banco
old = '''def inicializar_banco():
    """Cria a tabela de clientes se não existir."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            veiculo TEXT,
            placa TEXT,
            chassi TEXT UNIQUE,
            contato TEXT,
            shaken_vencimento TEXT,
            data_registro TEXT
        )
    """)
    conn.commit()
    conn.close()'''

new = '''def inicializar_banco():
    """Cria a tabela de clientes se não existir."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            veiculo TEXT,
            placa TEXT,
            chassi TEXT UNIQUE,
            contato TEXT,
            shaken_vencimento TEXT,
            data_registro TEXT
        )
    """)
    conn.commit()
    
    # Migração: adiciona coluna placa se não existir (bancos antigos)
    try:
        cursor.execute("SELECT placa FROM clientes LIMIT 1")
    except sqlite3.OperationalError:
        # Coluna não existe, adicionar
        cursor.execute("ALTER TABLE clientes ADD COLUMN placa TEXT")
        conn.commit()
    
    conn.close()'''

if old in c:
    c = c.replace(old, new)
    with open('database.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("✅ Migração automática adicionada!")
else:
    print("⚠️ Função inicializar_banco não encontrada")
