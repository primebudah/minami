# =========================================================
# DATABASE COM SUPABASE (PostgreSQL)
# =========================================================

import os
from datetime import date
from typing import Optional, List, Dict, Any

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
        # Testa conexão
        supabase = get_supabase()
        supabase.table("clientes").select("count", count="exact").limit(1).execute()
        return True
    except Exception as e:
        st.error(f"Erro conectando ao Supabase: {e}")
        return False

# =========================================================
# CLIENTES
# =========================================================

def salvar_cliente(dados: Dict[str, Any]) -> bool:
    """Salva novo cliente no Supabase."""
    try:
        supabase = get_supabase()
        
        # Prepara dados
        registro = {
            "nome": dados.get("nome", ""),
            "contato": dados.get("contato", ""),
            "shaken_vencimento": dados.get("shaken_vencimento"),
            "veiculo": dados.get("veiculo", ""),
            "placa": dados.get("placa", ""),
            "chassi": str(dados.get("chassi", "")).strip().upper(),
            "data_registro": dados.get("data_registro", str(date.today())),
            "status": dados.get("status", "Pendente")
        }
        
        # Remove campos vazios
        registro = {k: v for k, v in registro.items() if v is not None and v != ""}
        
        result = supabase.table("clientes").insert(registro).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Erro salvando cliente: {e}")
        return False

def listar_clientes() -> List[Dict]:
    """Retorna todos os clientes."""
    try:
        supabase = get_supabase()
        result = supabase.table("clientes").select("*").order("criado_em", desc=True).execute()
        return result.data or []
    except Exception as e:
        st.error(f"Erro listando clientes: {e}")
        return []

def buscar_cliente_por_chassi(chassi: str) -> Optional[Dict]:
    """Busca cliente por chassi."""
    try:
        supabase = get_supabase()
        chassi_clean = str(chassi).strip().upper()
        result = supabase.table("clientes").select("*").eq("chassi", chassi_clean).execute()
        if result.data:
            return result.data[0]
        return None
    except Exception as e:
        st.error(f"Erro buscando cliente: {e}")
        return None

def atualizar_cliente(cliente_id: int, dados: Dict[str, Any]) -> bool:
    """Atualiza cliente existente."""
    try:
        supabase = get_supabase()
        
        # Prepara dados (remove id e campos internos)
        update_data = {
            k: v for k, v in dados.items() 
            if k not in ["id", "criado_em", "atualizado_em"] and v is not None
        }
        
        # Normaliza chassi
        if "chassi" in update_data:
            update_data["chassi"] = str(update_data["chassi"]).strip().upper()
        
        result = supabase.table("clientes").update(update_data).eq("id", cliente_id).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Erro atualizando cliente: {e}")
        return False

def deletar_cliente(cliente_id: int) -> bool:
    """Remove cliente do banco."""
    try:
        supabase = get_supabase()
        result = supabase.table("clientes").delete().eq("id", cliente_id).execute()
        return len(result.data) > 0
    except Exception as e:
        st.error(f"Erro deletando cliente: {e}")
        return False

def salvar_historico(cliente_id: int, acao: str, dados_anteriores: Dict) -> bool:
    """Salva ação no histórico."""
    try:
        supabase = get_supabase()
        registro = {
            "cliente_id": cliente_id,
            "acao": acao,
            "dados_anteriores": dados_anteriores
        }
        result = supabase.table("historico_acoes").insert(registro).execute()
        return len(result.data) > 0
    except Exception:
        return False

def desfazer_ultima_acao() -> bool:
    """Desfaz última ação (se possível)."""
    try:
        supabase = get_supabase()
        # Busca última ação
        result = supabase.table("historico_acoes").select("*").order("criado_em", desc=True).limit(1).execute()
        if not result.data:
            return False
        
        acao = result.data[0]
        
        # Restaura dados (implementação básica)
        if acao["acao"] == "atualizar":
            cliente_id = acao["cliente_id"]
            dados_old = acao["dados_anteriores"]
            supabase.table("clientes").update(dados_old).eq("id", cliente_id).execute()
            return True
        elif acao["acao"] == "deletar":
            # Recria registro deletado
            dados_old = acao["dados_anteriores"]
            supabase.table("clientes").insert(dados_old).execute()
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
