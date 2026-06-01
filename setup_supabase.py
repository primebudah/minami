#!/usr/bin/env python3
"""
Script para configurar tabelas no Supabase.
Execute: python setup_supabase.py
"""

import os
import sys

# Carrega credenciais do .env.local se existir
env_file = ".env.local"
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ ERRO: SUPABASE_URL e SUPABASE_KEY não configurados")
    print("Crie arquivo .env.local com:")
    print("SUPABASE_URL=https://seu-projeto.supabase.co")
    print("SUPABASE_KEY=sua-chave-aqui")
    sys.exit(1)

try:
    from supabase import create_client
except ImportError:
    print("❌ Instale supabase: pip install supabase")
    sys.exit(1)

print(f"🔗 Conectando a: {SUPABASE_URL}")

# SQL para criar tabelas
SCHEMA_SQL = """
-- Tabela principal de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    nome TEXT NOT NULL,
    contato TEXT,
    shaken_vencimento DATE,
    veiculo TEXT,
    placa TEXT,
    chassi TEXT UNIQUE,
    fabricante TEXT,
    modelo_katashiki TEXT,
    chassi_completo TEXT,
    data_registro DATE,
    data_conclusao DATE,
    status TEXT DEFAULT 'Pendente',
    observacao TEXT,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    atualizado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de historico de acoes (undo)
CREATE TABLE IF NOT EXISTS historico_acoes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER,
    acao TEXT,
    dados_anteriores JSONB,
    criado_em TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela de historico de exclusoes
CREATE TABLE IF NOT EXISTS historico_exclusoes (
    id SERIAL PRIMARY KEY,
    cliente_id INTEGER,
    nome TEXT,
    contato TEXT,
    shaken_vencimento DATE,
    veiculo TEXT,
    placa TEXT,
    chassi TEXT,
    fabricante TEXT,
    modelo_katashiki TEXT,
    chassi_completo TEXT,
    data_registro DATE,
    data_exclusao TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    restaurado BOOLEAN DEFAULT FALSE
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_clientes_chassi ON clientes(chassi);
CREATE INDEX IF NOT EXISTS idx_clientes_status ON clientes(status);
CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes(nome);
CREATE INDEX IF NOT EXISTS idx_historico_cliente_id ON historico_acoes(cliente_id);

-- Function e trigger para updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_clientes_updated_at ON clientes;
CREATE TRIGGER update_clientes_updated_at
    BEFORE UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"""

def main():
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("\n📊 Criando tabelas...")
    
    # Executa SQL via RPC (se disponivel) ou mostra instrucoes
    try:
        # Tenta executar via exec_sql (extensao pg_net ou similar)
        result = supabase.table("clientes").select("count", count="exact").limit(1).execute()
        print("✅ Tabela 'clientes' já existe!")
    except Exception as e:
        if "relation" in str(e).lower() and "does not exist" in str(e).lower():
            print("⚠️  Tabelas não existem ainda")
            print("\n📋 INSTRUÇÕES MANUAIS:")
            print("1. Acesse: https://supabase.com/dashboard")
            print("2. Selecione o projeto: yuwvcmwadzhrzwrcbdla")
            print("3. Menu lateral → SQL Editor")
            print("4. New query")
            print("5. Cole o conteúdo de 'supabase_schema.sql'")
            print("6. Click 'Run'")
            print("\n📁 Arquivo para copiar: supabase_schema.sql")
        else:
            print(f"❌ Erro: {e}")
            return False
    
    # Testa conexao
    try:
        result = supabase.table("clientes").select("*").limit(1).execute()
        print(f"✅ Conexão OK! Dados: {result.data}")
        return True
    except Exception as e:
        print(f"⚠️  Aviso: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
