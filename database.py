# =========================================================
# DATABASE - Auto-detecta SQLite (local) ou Supabase (nuvem)
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
# SQLITE (fallback local)
# =========================================================

if not USE_SUPABASE:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_NAME = os.path.join(BASE_DIR, "minami_service.db")

# =========================================================
# SQLITE IMPLEMENTAÇÃO (apenas se não usar Supabase)
# =========================================================

if not USE_SUPABASE:

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

# =========================================================
# INIT DB
# =========================================================

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
        
        # Tabela geral de histórico de ações (INSERT/DELETE)
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

        # Popula data_conclusao retroativamente para concluídos sem data (usa data atual)
        from datetime import date as _date
        cur.execute("""
            UPDATE clientes
            SET data_conclusao = ?
            WHERE status = '🟢 Concluido'
            AND (data_conclusao IS NULL OR data_conclusao = '')
        """, (str(_date.today()),))

# =========================================================
# CRUD CLIENTES
# =========================================================

def salvar_cliente(d):
    """Salva um novo cliente no banco e registra no histórico geral."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO clientes (
                nome, contato, shaken_vencimento, veiculo, placa, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro
            )
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
            d.get("data_registro") or str(date.today())
        ))
        cliente_id = cur.lastrowid
        
        # Registra no histórico geral como INSERCAO
        cur.execute("""
            INSERT INTO historico_geral (
                acao, cliente_id, nome, contato, shaken_vencimento, veiculo, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro, data_acao
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "INSERCAO",
            cliente_id,
            d.get("nome", ""),
            d.get("contato") or "",
            d.get("shaken_vencimento", ""),
            d.get("veiculo", ""),
            d.get("chassi", ""),
            d.get("fabricante", ""),
            d.get("modelo_katashiki", ""),
            d.get("chassi_completo", ""),
            d.get("data_registro") or str(date.today()),
            str(date.today())
        ))
        
        return cliente_id

def listar_clientes(where=None, params=()):
    """Lista clientes com filtro opcional."""
    import pandas as pd
    
    with get_db_connection() as conn:
        query = """
            SELECT id, nome, contato, shaken_vencimento, veiculo, placa, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro, status, observacao, data_conclusao
            FROM clientes
        """
        
        if where:
            query += " WHERE " + where
        
        df = pd.read_sql_query(query, conn, params=params)
        return df

def atualizar_cliente(cliente_id, d):
    """Atualiza um cliente existente e salva snapshot no histórico."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Busca estado atual antes de atualizar (snapshot)
        cur.execute("""
            SELECT nome, contato, shaken_vencimento, veiculo, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro
            FROM clientes WHERE id=?
        """, (cliente_id,))
        
        cliente_atual = cur.fetchone()
        
        if cliente_atual:
            # Salva snapshot do estado anterior no histórico geral
            cur.execute("""
                INSERT INTO historico_geral (
                    acao, cliente_id, nome, contato, shaken_vencimento, veiculo, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro, data_acao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "EDICAO",
                cliente_id,
                cliente_atual["nome"],
                cliente_atual["contato"],
                cliente_atual["shaken_vencimento"],
                cliente_atual["veiculo"],
                cliente_atual["chassi"],
                cliente_atual["fabricante"],
                cliente_atual["modelo_katashiki"],
                cliente_atual["chassi_completo"],
                cliente_atual["data_registro"],
                str(date.today())
            ))
        
        # Normaliza status (remove quebras de linha/espaços extras)
        import re as _re
        if d.get("status"):
            d["status"] = _re.sub(r'\s+', ' ', str(d["status"]).strip())

        # Preenche data_conclusao se status virou concluído
        _data_conclusao = d.get("data_conclusao")
        if d.get("status", "") == "🟢 Concluido" and not _data_conclusao:
            _data_conclusao = str(date.today())
        elif d.get("status", "") != "🟢 Concluido":
            _data_conclusao = None

        # Realiza a atualização
        try:
         cur.execute("""
            UPDATE clientes
            SET nome=?, contato=?, shaken_vencimento=?, veiculo=?, placa=?, chassi=?, fabricante=?, modelo_katashiki=?, chassi_completo=?, data_registro=?, status=?, observacao=?, data_conclusao=?
            WHERE id=?
        """, (
            d.get("nome"),
            d.get("contato"),
            d.get("shaken_vencimento"),
            d.get("veiculo"),
            d.get("placa"),
            d.get("chassi"),
            d.get("fabricante"),
            d.get("modelo_katashiki"),
            d.get("chassi_completo"),
            d.get("data_registro"),
            d.get("status"),
            d.get("observacao", ""),
            _data_conclusao,
            cliente_id
        ))
        except Exception:
            pass

def deletar_cliente(cliente_id):
    """Deleta um cliente e salva no histórico geral."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Busca dados do cliente antes de deletar
        cur.execute("""
            SELECT nome, contato, shaken_vencimento, veiculo, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro
            FROM clientes WHERE id=?
        """, (cliente_id,))
        
        cliente = cur.fetchone()
        
        if cliente:
            # Salva no histórico de exclusões (mantendo compatibilidade)
            cur.execute("""
                INSERT INTO historico_exclusoes (
                    cliente_id, nome, contato, shaken_vencimento, veiculo, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro,
                    data_exclusao, restaurado
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            """, (
                cliente_id,
                cliente["nome"],
                cliente["contato"],
                cliente["shaken_vencimento"],
                cliente["veiculo"],
                cliente["chassi"],
                cliente["fabricante"],
                cliente["modelo_katashiki"],
                cliente["chassi_completo"],
                cliente["data_registro"],
                str(date.today())
            ))
            
            # Registra no histórico geral como EXCLUSAO
            cur.execute("""
                INSERT INTO historico_geral (
                    acao, cliente_id, nome, contato, shaken_vencimento, veiculo, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro, data_acao
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "EXCLUSAO",
                cliente_id,
                cliente["nome"],
                cliente["contato"],
                cliente["shaken_vencimento"],
                cliente["veiculo"],
                cliente["chassi"],
                cliente["fabricante"],
                cliente["modelo_katashiki"],
                cliente["chassi_completo"],
                cliente["data_registro"],
                str(date.today())
            ))
            
            # Deleta o cliente
            cur.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))

# =========================================================
# HISTÓRICO DE EXCLUSÕES
# =========================================================

def listar_historico_exclusoes():
    """Lista histórico de exclusões não restauradas."""
    import pandas as pd
    
    with get_db_connection() as conn:
        query = """
            SELECT id, cliente_id, nome, veiculo, chassi, contato,
                   shaken_vencimento, data_registro, data_cadastro,
                   data_exclusao, restaurado
            FROM historico_exclusoes
            WHERE restaurado = 0
            ORDER BY data_exclusao DESC
        """
        df = pd.read_sql_query(query, conn)
        return df

def restaurar_cliente(historico_id):
    """Restaura um cliente do histórico de exclusões."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Busca dados do histórico
        cur.execute("""
            SELECT cliente_id, nome, veiculo, chassi, contato,
                   shaken_vencimento, data_registro, data_cadastro
            FROM historico_exclusoes WHERE id=?
        """, (historico_id,))
        
        historico = cur.fetchone()
        
        if historico:
            # Restaura na tabela principal
            cur.execute("""
                INSERT INTO clientes (
                    nome, veiculo, chassi, contato,
                    shaken_vencimento, data_registro, data_cadastro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                historico["nome"],
                historico["veiculo"],
                historico["chassi"],
                historico["contato"],
                historico["shaken_vencimento"],
                historico["data_registro"],
                historico["data_cadastro"]
            ))
            
            # Marca como restaurado
            cur.execute("""
                UPDATE historico_exclusoes
                SET restaurado = 1
                WHERE id = ?
            """, (historico_id,))

def limpar_historico_restaurados():
    """Remove registros do histórico que já foram restaurados."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM historico_exclusoes WHERE restaurado = 1")

def desfazer_ultima_acao():
    """Desfaz a última ação registrada no histórico geral."""
    with get_db_connection() as conn:
        cur = conn.cursor()
        
        # Busca última ação não desfeita (apenas dos últimos 10 minutos)
        cur.execute("""
            SELECT id, acao, cliente_id, nome, veiculo, chassi, contato,
                   shaken_vencimento, data_registro, data_acao
            FROM historico_geral
            WHERE desfeito = 0
            ORDER BY id DESC
            LIMIT 1
        """)
        
        acao = cur.fetchone()
        
        if not acao:
            return False, "Nenhuma ação para desfazer"
        
        historico_id = acao["id"]
        tipo_acao = acao["acao"]
        
        print(f"[DEBUG] Desfazendo ação: {tipo_acao}, ID: {historico_id}, Cliente: {acao['nome']}")
        
        if tipo_acao == "EXCLUSAO":
            # Restaura o cliente deletado
            cur.execute("""
                INSERT INTO clientes (
                    nome, contato, shaken_vencimento, veiculo, chassi, fabricante, modelo_katashiki, chassi_completo, data_registro
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                acao["nome"],
                acao["contato"],
                acao["shaken_vencimento"],
                acao["veiculo"],
                acao["chassi"],
                acao["fabricante"],
                acao["modelo_katashiki"],
                acao["chassi_completo"],
                acao["data_registro"]
            ))
            
            # Marca como desfeito
            cur.execute("UPDATE historico_geral SET desfeito = 1 WHERE id = ?", (historico_id,))
            
        elif tipo_acao == "INSERCAO":
            # Remove o cliente inserido
            cur.execute("DELETE FROM clientes WHERE id = ?", (acao["cliente_id"],))
            
            # Marca como desfeito
            cur.execute("UPDATE historico_geral SET desfeito = 1 WHERE id = ?", (historico_id,))
            
        elif tipo_acao == "EDICAO":
            # Restaura o estado anterior da edição (UPDATE, não DELETE)
            cur.execute("""
                UPDATE clientes
                SET nome=?, contato=?, shaken_vencimento=?, veiculo=?, chassi=?, fabricante=?, modelo_katashiki=?, chassi_completo=?, data_registro=?
                WHERE id=?
            """, (
                acao["nome"],
                acao["contato"],
                acao["shaken_vencimento"],
                acao["veiculo"],
                acao["chassi"],
                acao["fabricante"],
                acao["modelo_katashiki"],
                acao["chassi_completo"],
                acao["data_registro"],
                acao["cliente_id"]
            ))
            
            # Marca como desfeito
            cur.execute("UPDATE historico_geral SET desfeito = 1 WHERE id = ?", (historico_id,))
        
        return True, f"Ação {tipo_acao} desfeita com sucesso"
