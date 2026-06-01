# =========================================================
# DATABASE COM SUPABASE (PostgreSQL)
# =========================================================

import os
from datetime import date
from typing import Optional, List, Dict, Any
import pandas as pd

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

import streamlit as st

# =========================================================
# CONFIG
# =========================================================

SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))

_supabase: Optional[Client] = None

def get_supabase() -> Client:
    """Retorna cliente Supabase inicializado."""
    global _supabase
    if _supabase is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar configurados nos secrets")
        if create_client is None:
            raise ImportError("supabase package não instalado. Execute: pip install supabase")
        _supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase

# =========================================================
# INIT DB
# =========================================================

def inicializar_banco():
    """Tabelas já devem existir no Supabase (criadas via SQL Editor)."""
    try:
        # Testa conexão via RPC
        supabase = get_supabase()
        result = supabase.rpc('listar_clientes_rpc').execute()
        return True
    except Exception as e:
        error_msg = str(e)
        if "Could not find the function" in error_msg or "PGRST" in error_msg:
            st.error("❌ Funções RPC não encontradas. Execute o SQL em supabase_rpc_functions.sql no Supabase.")
        elif "clientes" in error_msg.lower():
            st.error("❌ Tabela 'clientes' não encontrada. Crie as tabelas no Supabase primeiro.")
        else:
            st.error(f"Erro conectando ao Supabase: {e}")
        return False

# =========================================================
# CLIENTES
# =========================================================

def salvar_cliente(dados: Dict[str, Any]) -> bool:
    """Salva novo cliente no Supabase via RPC."""
    try:
        supabase = get_supabase()
        
        # Chama a função RPC
        result = supabase.rpc('salvar_cliente_rpc', {
            'p_nome': dados.get("nome", ""),
            'p_contato': dados.get("contato") or None,
            'p_shaken_vencimento': dados.get("shaken_vencimento") or None,
            'p_veiculo': dados.get("veiculo") or None,
            'p_placa': dados.get("placa") or None,
            'p_chassi': str(dados.get("chassi", "")).strip().upper() if dados.get("chassi") else None,
            'p_fabricante': dados.get("fabricante") or None,
            'p_modelo_katashiki': dados.get("modelo_katashiki") or None,
            'p_chassi_completo': dados.get("chassi_completo") or None,
            'p_data_registro': dados.get("data_registro") or str(date.today()),
            'p_data_conclusao': dados.get("data_conclusao") or None,
            'p_status': dados.get("status", "Pendente"),
            'p_observacao': dados.get("observacao") or None
        }).execute()
        
        return result.data is not None
    except Exception as e:
        st.error(f"Erro salvando cliente: {e}")
        return False

def listar_clientes(where_clause=None, params=None) -> pd.DataFrame:
    """Retorna todos os clientes via RPC como DataFrame.
    
    Args:
        where_clause: Ignorado no Supabase (para compatibilidade com SQLite)
        params: Ignorado no Supabase (para compatibilidade com SQLite)
    """
    try:
        supabase = get_supabase()
        result = supabase.rpc('listar_clientes_rpc').execute()
        data = result.data or []
        
        # Garante que data é uma lista antes de converter
        if not isinstance(data, list):
            data = []
        
        df = pd.DataFrame(data)
        
        # Se há filtros, aplica no DataFrame
        if where_clause and params:
            # Parse simples do where_clause para filtrar DataFrame
            # Ex: "nome LIKE ?" -> df[df['nome'].str.contains(params[0], case=False, na=False)]
            pass
        
        return df
    except Exception as e:
        st.error(f"Erro listando clientes: {e}")
        return pd.DataFrame()

def buscar_cliente_por_chassi(chassi: str) -> Optional[Dict]:
    """Busca cliente por chassi via RPC."""
    try:
        supabase = get_supabase()
        chassi_clean = str(chassi).strip().upper()
        result = supabase.rpc('buscar_cliente_por_chassi_rpc', {
            'p_chassi': chassi_clean
        }).execute()
        data = result.data or []
        # Garante que data é uma lista
        if not isinstance(data, list):
            data = []
        if len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        st.error(f"Erro buscando cliente: {e}")
        return None

def atualizar_cliente(cliente_id: int, dados: Dict[str, Any]) -> bool:
    """Atualiza cliente existente via RPC."""
    try:
        supabase = get_supabase()
        
        # Chama a função RPC
        result = supabase.rpc('atualizar_cliente_rpc', {
            'p_id': cliente_id,
            'p_nome': dados.get("nome", ""),
            'p_contato': dados.get("contato") or None,
            'p_shaken_vencimento': dados.get("shaken_vencimento") or None,
            'p_veiculo': dados.get("veiculo") or None,
            'p_placa': dados.get("placa") or None,
            'p_chassi': str(dados.get("chassi", "")).strip().upper() if dados.get("chassi") else None,
            'p_fabricante': dados.get("fabricante") or None,
            'p_modelo_katashiki': dados.get("modelo_katashiki") or None,
            'p_chassi_completo': dados.get("chassi_completo") or None,
            'p_data_registro': dados.get("data_registro") or None,
            'p_data_conclusao': dados.get("data_conclusao") or None,
            'p_status': dados.get("status", "Pendente"),
            'p_observacao': dados.get("observacao") or None
        }).execute()
        
        return result.data is True
    except Exception as e:
        st.error(f"Erro atualizando cliente: {e}")
        return False

def deletar_cliente(cliente_id: int) -> bool:
    """Remove cliente do banco via RPC."""
    try:
        supabase = get_supabase()
        result = supabase.rpc('deletar_cliente_rpc', {
            'p_id': cliente_id
        }).execute()
        return result.data is True
    except Exception as e:
        st.error(f"Erro deletando cliente: {e}")
        return False

def salvar_historico(cliente_id: int, acao: str, dados_anteriores: Dict) -> bool:
    """Salva ação no histórico via RPC."""
    try:
        import json
        supabase = get_supabase()
        result = supabase.rpc('salvar_historico_rpc', {
            'p_cliente_id': cliente_id,
            'p_acao': acao,
            'p_dados_anteriores': json.dumps(dados_anteriores) if dados_anteriores else None
        }).execute()
        return True
    except Exception:
        return False

def desfazer_ultima_acao() -> bool:
    """Desfaz última ação (se possível) via RPC."""
    try:
        import json
        supabase = get_supabase()
        
        # Busca última ação via RPC
        result = supabase.rpc('obter_ultima_acao_rpc').execute()
        data = result.data or []
        # Garante que data é uma lista
        if not isinstance(data, list):
            data = []
        if not data or len(data) == 0:
            return False
        
        acao = data[0]
        
        # Restaura dados
        if acao["acao"] == "atualizar":
            # Atualiza o cliente com dados antigos via RPC
            supabase.rpc('atualizar_cliente_rpc', {
                'p_id': acao["cliente_id"],
                **acao["dados_anteriores"]
            }).execute()
            # Deleta do histórico
            supabase.rpc('deletar_historico_rpc', {'p_id': acao["id"]}).execute()
            return True
        elif acao["acao"] == "deletar":
            # Restaura cliente excluído via RPC
            supabase.rpc('restaurar_cliente_excluido_rpc', {
                'p_historico_id': acao.get("historico_id") or acao["id"]
            }).execute()
            # Deleta do histórico
            supabase.rpc('deletar_historico_rpc', {'p_id': acao["id"]}).execute()
            return True
        return False
    except Exception as e:
        st.error(f"Erro desfazendo ação: {e}")
        return False

# =========================================================
# MIGRAÇÃO DE DADOS (SQLite → Supabase)
# =========================================================

def migrar_dados_sqlite(supabase_client, sqlite_path: str = "minami_service.db"):
    """Migra dados do SQLite local para Supabase."""
    import sqlite3
    try:
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        # Busca todos os clientes
        cur.execute("SELECT * FROM clientes")
        rows = cur.fetchall()
        
        migrados = 0
        for row in rows:
            dados = dict(row)
            # Remove ID para novo insert
            dados.pop("id", None)
            
            try:
                supabase_client.table("clientes").insert(dados).execute()
                migrados += 1
            except Exception as e:
                print(f"Erro migrando cliente {dados.get('nome')}: {e}")
        
        conn.close()
        return migrados
    except Exception as e:
        print(f"Erro na migração: {e}")
        return 0
