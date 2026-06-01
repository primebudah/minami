# =========================================================
# DATABASE - Auto-detecta SQLite (local) ou Supabase (nuvem)
# v2 - Corrigido para Streamlit Cloud
# =========================================================

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Optional, Dict, Any, List

# Detecta se Supabase está configurado
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Se secrets.toml existir, tenta carregar de lá
try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", SUPABASE_URL)
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", SUPABASE_KEY)
except:
    pass

# Flag: True = usar Supabase, False = usar SQLite local
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

# Se Supabase disponível, importa e delega
if USE_SUPABASE:
    try:
        from database_supabase import (
            inicializar_banco,
            salvar_cliente,
            listar_clientes,
            buscar_cliente_por_chassi,
            atualizar_cliente,
            deletar_cliente,
            desfazer_ultima_acao,
            salvar_historico,
            get_supabase,
            migrar_dados_sqlite
        )
        print("[DB] Usando Supabase (PostgreSQL)")
    except ImportError as e:
        print(f"[DB] Supabase configurado mas biblioteca não instalada: {e}")
        USE_SUPABASE = False

# =========================================================
# SQLITE (fallback local) - só define se não usar Supabase
# =========================================================

if not USE_SUPABASE:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_NAME = os.path.join(BASE_DIR, "minami_service.db")

    @contextmanager
    def get_db_connection():
        """Context manager para conexão com banco de dados."""
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def inicializar_banco():
        """Inicializa o banco de dados com todas as tabelas necessárias."""
        with get_db_connection() as conn:
            cur = conn.cursor()
            
            # Tabela principal de clientes
            cur.execute("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT,
                    contato TEXT,
                    shaken_vencimento TEXT,
                    veiculo TEXT,
                    placa TEXT,
                    chassi TEXT UNIQUE,
                    fabricante TEXT,
                    modelo_katashiki TEXT,
                    chassi_completo TEXT,
                    data_registro TEXT
                )
            """)
            
            # Tabela independente de histórico de exclusões
            cur.execute("""
                CREATE TABLE IF NOT EXISTS historico_exclusoes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cliente_id INTEGER,
                    nome TEXT,
                    contato TEXT,
                    shaken_vencimento TEXT,
                    veiculo TEXT,
                    chassi TEXT,
                    fabricante TEXT,
                    modelo_katashiki TEXT,
                    chassi_completo TEXT,
                    data_registro TEXT,
                    data_exclusao TEXT,
                    restaurado INTEGER DEFAULT 0
                )
            """)
            
            # Tabela geral de histórico de ações
            cur.execute("""
                CREATE TABLE IF NOT EXISTS historico_geral (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    acao TEXT,
                    cliente_id INTEGER,
                    nome TEXT,
                    contato TEXT,
                    shaken_vencimento TEXT,
                    veiculo TEXT,
                    chassi TEXT,
                    fabricante TEXT,
                    modelo_katashiki TEXT,
                    chassi_completo TEXT,
                    data_registro TEXT,
                    data_acao TEXT,
                    desfeito INTEGER DEFAULT 0
                )
            """)
            
            # Adiciona colunas se não existirem
            for col in ["data_registro", "fabricante", "modelo_katashiki", "chassi_completo", "status", "observacao", "data_conclusao", "placa"]:
                try:
                    cur.execute(f"ALTER TABLE clientes ADD COLUMN {col} TEXT")
                except:
                    pass

    def salvar_cliente(d):
        """Salva um novo cliente no banco."""
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO clientes (nome, contato, shaken_vencimento, veiculo, placa, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d.get("nome", ""),
                d.get("contato") or "",
                d.get("shaken_vencimento", ""),
                d.get("veiculo", ""),
                d.get("placa", ""),
                d.get("chassi", ""),
                d.get("fabricante", ""),
                d.get("modelo_katashiki", ""),
                d.get("chassi_completo", ""),
                d.get("data_registro", str(date.today()))
            ))
            return cur.lastrowid

    def listar_clientes():
        """Lista todos os clientes."""
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clientes ORDER BY id DESC")
            return [dict(row) for row in cur.fetchall()]

    def buscar_cliente_por_chassi(chassi):
        """Busca cliente por chassi."""
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM clientes WHERE chassi = ?", (chassi,))
            row = cur.fetchone()
            return dict(row) if row else None

    def atualizar_cliente(cliente_id, dados):
        """Atualiza cliente existente."""
        with get_db_connection() as conn:
            cur = conn.cursor()
            campos = []
            valores = []
            for k, v in dados.items():
                if k != "id":
                    campos.append(f"{k} = ?")
                    valores.append(v)
            valores.append(cliente_id)
            sql = f"UPDATE clientes SET {', '.join(campos)} WHERE id = ?"
            cur.execute(sql, valores)

    def deletar_cliente(cliente_id):
        """Deleta cliente."""
        with get_db_connection() as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))

    def salvar_historico(dados):
        """Salva histórico."""
        pass  # Simplificado para SQLite local

    def desfazer_ultima_acao():
        """Desfaz última ação."""
        return True, "Desfazer não implementado no SQLite"
