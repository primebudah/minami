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

# Importa sistema de sincronização local
try:
    from database_local_sync import backup_local_para_arquivo, _carregar_config_backup
    SYNC_AVAILABLE = True
    print(f"[DEBUG] SYNC_AVAILABLE = True - sistema de backup local carregado")
except ImportError as e:
    SYNC_AVAILABLE = False
    print(f"[DEBUG] SYNC_AVAILABLE = False - erro ao importar: {e}")

# Sistema de logs visível no app
backup_logs = []

def add_log(message):
    """Adiciona log ao sistema visível"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    backup_logs.append(f"[{timestamp}] {message}")
    # Mantém apenas os últimos 20 logs
    if len(backup_logs) > 20:
        backup_logs.pop(0)
    print(f"[DEBUG] {message}")

# =========================================================
# CONFIG
# =========================================================

# Tenta carregar de st.secrets se disponivel, senha usa variaveis de ambiente
try:
    SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL", ""))
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY", ""))
except:
    # Se st.secrets não estiver disponivel (fora do contexto Streamlit)
    SUPABASE_URL = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

_supabase: Optional[Client] = None

# Colunas reais da tabela clientes (usado para filtrar payloads)
_CAMPOS_CLIENTE = {
    "nome", "contato", "shaken_vencimento", "veiculo", "placa", "chassi",
    "fabricante", "modelo_katashiki", "chassi_completo", "data_registro",
    "data_conclusao", "status", "observacao",
}

# Mapeia coluna -> nome do parâmetro da RPC atualizar_cliente_rpc
_MAPA_PARAMS_RPC = {
    "nome": "p_nome",
    "contato": "p_contato",
    "shaken_vencimento": "p_shaken_vencimento",
    "veiculo": "p_veiculo",
    "placa": "p_placa",
    "chassi": "p_chassi",
    "fabricante": "p_fabricante",
    "modelo_katashiki": "p_modelo_katashiki",
    "chassi_completo": "p_chassi_completo",
    "data_registro": "p_data_registro",
    "data_conclusao": "p_data_conclusao",
    "status": "p_status",
    "observacao": "p_observacao",
}

# Arquivo de snapshot local automático (proteção contra perda de dados)
_SNAPSHOT_FILE = os.path.join(os.path.dirname(__file__), ".streamlit", "ultimo_snapshot_clientes.json")


def _salvar_snapshot_local(df_clientes):
    """Grava snapshot local da tabela após cada escrita bem-sucedida.

    Nunca pode transformar uma gravação bem-sucedida em falha.
    """
    try:
        if df_clientes is None or df_clientes.empty:
            return
        os.makedirs(os.path.dirname(_SNAPSHOT_FILE), exist_ok=True)
        df_clientes.to_json(_SNAPSHOT_FILE, orient="records", force_ascii=False, date_format="iso")
        add_log(f"Snapshot local salvo: {_SNAPSHOT_FILE}")
    except Exception as e:
        add_log(f"Erro ao salvar snapshot local: {e}")


def _backup_automatico():
    """Snapshot local + backup em arquivo após cada gravação.

    O snapshot JSON local é SEMPRE gravado (proteção contra perda de
    dados). O backup em CSV/SQLite só roda se auto_sync estiver
    configurado. Nunca pode afetar o resultado da gravação.
    """
    try:
        df_clientes = listar_clientes()
        _salvar_snapshot_local(df_clientes)
        if SYNC_AVAILABLE:
            config = _carregar_config_backup()
            if config.get("auto_sync", False):
                sucesso, msg, caminho = backup_local_para_arquivo(df_clientes)
                if sucesso:
                    add_log(f"Backup automático: {msg}")
                else:
                    add_log(f"Backup automático falhou: {msg}")
    except Exception as e:
        add_log(f"Erro no backup automático: {e}")


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

def rpc_df(name: str, params: Optional[Dict] = None) -> pd.DataFrame:
    """Wrapper para chamadas RPC que sempre retorna DataFrame.
    
    Args:
        name: Nome da função RPC
        params: Parâmetros para a função RPC (opcional)
    
    Returns:
        DataFrame com os resultados da RPC (vazio se erro ou sem dados)
    """
    try:
        supabase = get_supabase()
        result = supabase.rpc(name, params or {}).execute()
        data = result.data or []
        # Garante que data é uma lista antes de converter
        if not isinstance(data, list):
            data = []
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro na RPC {name}: {e}")
        return pd.DataFrame()

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
    """Salva novo cliente no Supabase via RPC com tratamento de erro robusto."""
    print(f"[DEBUG Supabase] salvar_cliente chamado com dados: {dados}")
    try:
        supabase = get_supabase()
        
        # Validação: verificar se chassi já existe antes de tentar inserir
        chassi = str(dados.get("chassi", "")).strip().upper() if dados.get("chassi") else None
        if chassi:
            try:
                existente = buscar_cliente_por_chassi(chassi)
                if existente:
                    st.error(f"❌ Erro: Chassi '{chassi}' já existe no banco (cliente: {existente.get('nome', 'desconhecido')}).")
                    add_log(f"ERRO: Tentativa de duplicar chassi {chassi}")
                    return False
            except Exception as e:
                print(f"[DEBUG] Erro ao verificar duplicidade de chassi: {e}")
        
        # Chama a função RPC
        result = supabase.rpc('salvar_cliente_rpc', {
            'p_nome': dados.get("nome", ""),
            'p_contato': dados.get("contato") or None,
            'p_shaken_vencimento': dados.get("shaken_vencimento") or None,
            'p_veiculo': dados.get("veiculo") or None,
            'p_placa': dados.get("placa") or None,
            'p_chassi': chassi,
            'p_fabricante': dados.get("fabricante") or None,
            'p_modelo_katashiki': dados.get("modelo_katashiki") or None,
            'p_chassi_completo': dados.get("chassi_completo") or None,
            'p_data_registro': dados.get("data_registro") or str(date.today()),
            'p_data_conclusao': dados.get("data_conclusao") or None,
            'p_status': dados.get("status", "Pendente"),
            'p_observacao': dados.get("observacao") or None
        }).execute()
        print(f"[DEBUG Supabase] Resultado salvar_cliente: {result.data}")
        
        # Backup automático + snapshot local (nunca afeta o resultado do save)
        if result.data is not None:
            _backup_automatico()

        return result.data is not None
    except Exception as e:
        st.error(f"Erro salvando cliente: {e}")
        return False

def listar_clientes(where_clause=None, params=None) -> pd.DataFrame:
    """Retorna todos os clientes via query direta (fallback se RPC falhar).
    
    Args:
        where_clause: Ignorado no Supabase (para compatibilidade com SQLite)
        params: Ignorado no Supabase (para compatibilidade com SQLite)
    """
    print(f"[DEBUG Supabase] listar_clientes chamado")
    try:
        # Tenta RPC primeiro
        df = rpc_df('listar_clientes_rpc')
        if not df.empty:
            print(f"[DEBUG Supabase] listar_clientes retornou {len(df)} registros via RPC")
            return df
    except Exception as e:
        print(f"[DEBUG] RPC falhou, usando query direta: {e}")
    
    # Fallback: query direta se RPC falhar
    try:
        supabase = get_supabase()
        result = supabase.table('clientes').select('*').order('id', desc=True).execute()
        data = result.data or []
        if not isinstance(data, list):
            data = []
        print(f"[DEBUG Supabase] listar_clientes retornou {len(data)} registros via query direta")
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao listar clientes: {e}")
        print(f"[DEBUG Supabase] Erro ao listar clientes: {e}")
        return pd.DataFrame()

def buscar_cliente_por_id(cliente_id: int) -> Optional[Dict]:
    """Busca cliente por ID via RPC."""
    try:
        supabase = get_supabase()
        result = supabase.rpc('buscar_cliente_por_id_rpc', {
            'p_id': int(cliente_id)
        }).execute()
        data = result.data or []
        if not isinstance(data, list):
            data = []
        if len(data) > 0:
            return data[0]
        return None
    except Exception as e:
        print(f"[DEBUG] Erro buscando cliente por ID: {e}")
        return None

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
    """Atualiza cliente existente via RPC com tratamento de erro robusto.

    SEGURANÇA MULTI-DISPOSITIVO: a RPC atualizar_cliente_rpc regrava
    todas as colunas. Por isso este método faz MERGE com o registro
    atual do banco: somente os campos presentes em `dados` são
    alterados; todos os demais são preservados com os valores atuais
    do Supabase. Isso impede que uma sessão desatualizada (outro
    dispositivo, cache, planilha formatada) apague ou altere campos
    que o usuário não editou.
    """
    try:
        supabase = get_supabase()

        # Função auxiliar para converter NaN para None
        def clean_value(v):
            if isinstance(v, float) and pd.isna(v):
                return None
            if v is None or str(v).strip() == "":
                return None
            return v

        # Filtra apenas colunas reais da tabela
        alteracoes = {}
        for chave, valor in dados.items():
            if chave in _CAMPOS_CLIENTE:
                alteracoes[chave] = clean_value(valor)

        if not alteracoes:
            print("[DEBUG Supabase] atualizar_cliente: nenhum campo válido para atualizar")
            return False

        # Busca o registro atual no banco para mesclar
        atual = buscar_cliente_por_id(cliente_id)
        if atual is None:
            st.error(f"❌ Cliente ID {cliente_id} não encontrado no banco. Nenhuma alteração foi feita.")
            add_log(f"ERRO: atualizar_cliente ID={cliente_id} - registro não encontrado")
            return False

        # Validação: verificar se chassi já existe em OUTRO cliente (somente se chassi mudou)
        chassi_novo = alteracoes.get("chassi")
        if chassi_novo:
            chassi_novo = str(chassi_novo).strip().upper()
            alteracoes["chassi"] = chassi_novo
            try:
                existente = buscar_cliente_por_chassi(chassi_novo)
                if existente and existente.get('id') != cliente_id:
                    st.error(f"❌ Erro: Chassi '{chassi_novo}' já existe no banco (cliente: {existente.get('nome', 'desconhecido')}). Não é possível duplicar chassi.")
                    add_log(f"ERRO: Tentativa de atualizar cliente {cliente_id} com chassi duplicado {chassi_novo}")
                    return False
            except Exception as e:
                print(f"[DEBUG] Erro ao verificar duplicidade de chassi: {e}")

        # Monta payload completo: campos alterados + valores atuais do banco
        payload = {}
        for campo, param in _MAPA_PARAMS_RPC.items():
            if campo in alteracoes:
                payload[param] = alteracoes[campo]
            elif campo in atual:
                # Preserva valor atual exatamente como está no banco
                payload[param] = atual.get(campo)

        # Log para debug
        print(f"DEBUG atualizar_cliente: campos alterados = {list(alteracoes.keys())}")

        # Chama a função RPC
        result = supabase.rpc('atualizar_cliente_rpc', {
            'p_id': cliente_id,
            **payload
        }).execute()

        # Backup automático + snapshot local (nunca afeta o resultado)
        if result.data is True:
            _backup_automatico()

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
        if result.data is True:
            _backup_automatico()
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
            # dados_anteriores é JSONB com nomes de coluna; filtra e
            # delega para atualizar_cliente (que faz merge seguro)
            dados = {
                k: v for k, v in (acao.get("dados_anteriores") or {}).items()
                if k in _CAMPOS_CLIENTE
            }
            if dados:
                atualizar_cliente(acao["cliente_id"], dados)
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
