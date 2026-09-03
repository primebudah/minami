# =========================================================
# SISTEMA DE SINCRONIZAÇÃO LOCAL - Backup Local + Nuvem
# =========================================================

import os
import json
import sqlite3
import shutil
from datetime import datetime
from typing import Optional, Dict, Any
import pandas as pd
import streamlit as st

# =========================================================
# CONFIGURAÇÃO DO BACKUP LOCAL
# =========================================================

_CONFIG_FILE = os.path.join(os.path.dirname(__file__), ".streamlit", "local_backup_config.json")
_DEFAULT_BACKUP_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "MinamiBackup")

def _carregar_config_backup():
    """Carrega configuração do backup local."""
    try:
        if os.path.exists(_CONFIG_FILE):
            with open(_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[DEBUG] Erro ao carregar config backup: {e}")
    return {"backup_dir": None, "ultima_sincronizacao": None}

def _salvar_config_backup(config):
    """Salva configuração do backup local."""
    try:
        with open(_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[DEBUG] Erro ao salvar config backup: {e}")

def _criar_diretorio_backup(path):
    """Cria diretório de backup se não existir."""
    try:
        if not os.path.exists(path):
            os.makedirs(path)
            return True
        return True
    except Exception as e:
        print(f"[DEBUG] Erro ao criar diretório backup: {e}")
        return False

def _obter_caminho_backup():
    """Obtém caminho do backup local, perguntando se necessário."""
    config = _carregar_config_backup()
    
    # Se já tem configuração e o diretório existe, usa ele
    if config.get("backup_dir") and os.path.exists(config["backup_dir"]):
        return config["backup_dir"]
    
    # Se não, pede para selecionar ou usar padrão
    return None

def _definir_caminho_backup(caminho):
    """Define o caminho do backup local."""
    if caminho and _criar_diretorio_backup(caminho):
        config = _carregar_config_backup()
        config["backup_dir"] = caminho
        config["ultima_sincronizacao"] = datetime.now().isoformat()
        _salvar_config_backup(config)
        return True
    return False

# =========================================================
# FUNÇÕES DE BACKUP LOCAL
# =========================================================

def backup_local_para_arquivo(df_clientes, backup_dir=None):
    """
    Salva backup local dos clientes em CSV e SQLite.
    
    Args:
        df_clientes: DataFrame com dados dos clientes
        backup_dir: Diretório de backup (opcional, usa configurado se não informado)
    
    Returns:
        tuple: (sucesso, mensagem, caminho_arquivo)
    """
    try:
        if df_clientes is None or df_clientes.empty:
            return False, "Não há dados para fazer backup", None
        
        # Usa diretório configurado ou padrão
        if not backup_dir:
            backup_dir = _obter_caminho_backup()
            if not backup_dir:
                backup_dir = _DEFAULT_BACKUP_DIR
        
        # Cria diretório se necessário
        if not _criar_diretorio_backup(backup_dir):
            return False, "Não foi possível criar diretório de backup", None
        
        # Nome do arquivo com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salva em CSV
        csv_file = os.path.join(backup_dir, f"minami_backup_{timestamp}.csv")
        df_clientes.to_csv(csv_file, index=False, encoding='utf-8-sig')
        
        # Salva em SQLite
        db_file = os.path.join(backup_dir, f"minami_backup_{timestamp}.db")
        conn = sqlite3.connect(db_file)
        df_clientes.to_sql('clientes', conn, if_exists='replace', index=False)
        conn.close()
        
        # Atualiza configuração
        _definir_caminho_backup(backup_dir)
        
        return True, f"Backup salvo em {backup_dir}", csv_file
        
    except Exception as e:
        return False, f"Erro ao fazer backup: {e}", None

def carregar_backup_local(arquivo_backup):
    """
    Carrega backup local de CSV ou SQLite.
    
    Args:
        arquivo_backup: Caminho do arquivo de backup
    
    Returns:
        DataFrame com dados do backup ou None se erro
    """
    try:
        if arquivo_backup.endswith('.csv'):
            return pd.read_csv(arquivo_backup)
        elif arquivo_backup.endswith('.db'):
            conn = sqlite3.connect(arquivo_backup)
            df = pd.read_sql('SELECT * FROM clientes', conn)
            conn.close()
            return df
        else:
            return None
    except Exception as e:
        print(f"[DEBUG] Erro ao carregar backup: {e}")
        return None

def listar_backups_locais(backup_dir=None):
    """
    Lista todos os backups locais disponíveis.
    
    Args:
        backup_dir: Diretório de backup (opcional)
    
    Returns:
        Lista de tuplas (caminho, data, tipo, tamanho)
    """
    try:
        if not backup_dir:
            backup_dir = _obter_caminho_backup()
            if not backup_dir:
                backup_dir = _DEFAULT_BACKUP_DIR
        
        if not os.path.exists(backup_dir):
            return []
        
        backups = []
        for arquivo in os.listdir(backup_dir):
            if arquivo.startswith('minami_backup_') and (arquivo.endswith('.csv') or arquivo.endswith('.db')):
                caminho_completo = os.path.join(backup_dir, arquivo)
                stats = os.stat(caminho_completo)
                data = datetime.fromtimestamp(stats.st_mtime)
                tipo = 'CSV' if arquivo.endswith('.csv') else 'SQLite'
                tamanho = stats.st_size
                backups.append((caminho_completo, data, tipo, tamanho))
        
        # Ordena por data (mais recente primeiro)
        backups.sort(key=lambda x: x[1], reverse=True)
        return backups
        
    except Exception as e:
        print(f"[DEBUG] Erro ao listar backups: {e}")
        return []

# =========================================================
# INTERFACE STREAMLIT PARA CONFIGURAÇÃO
# =========================================================

def interface_configuracao_backup_local():
    """Interface Streamlit para configurar backup local."""
    st.subheader("🗂️ Configuração de Backup Local")
    
    config = _carregar_config_backup()
    backup_dir_atual = config.get("backup_dir")
    
    # Mostra status atual
    if backup_dir_atual and os.path.exists(backup_dir_atual):
        st.success(f"✅ Backup configurado em: `{backup_dir_atual}`")
        st.caption(f"Última sincronização: {config.get('ultima_sincronizacao', 'Nunca')}")
        
        # Lista backups existentes
        backups = listar_backups_locais(backup_dir_atual)
        if backups:
            st.write(f"📋 **{len(backups)} backup(s) encontrado(s):**")
            for caminho, data, tipo, tamanho in backups[:5]:  # Mostra últimos 5
                data_fmt = data.strftime("%d/%m/%Y %H:%M")
                tamanho_fmt = f"{tamanho/1024:.1f} KB"
                st.caption(f"• {tipo} - {data_fmt} - {tamanho_fmt}")
            
            if len(backups) > 5:
                st.caption(f"... e mais {len(backups) - 5} backup(s)")
        else:
            st.info("📭 Nenhum backup encontrado neste diretório.")
    else:
        st.warning("⚠️ Backup local não configurado")
        st.info("Configure um diretório para salvar backups automáticos dos dados.")
    
    st.divider()
    
    # Opção de configurar novo diretório
    with st.expander("📁 Configurar novo diretório de backup", expanded=False):
        st.info("💡 **Para uso local (PC):** Escolha uma pasta no seu computador")
        st.info("💡 **Para uso na nuvem:** Use a opção de download abaixo")
        
        # Para uso local - input de caminho
        novo_path = st.text_input(
            "Caminho do diretório de backup",
            value=backup_dir_atual or _DEFAULT_BACKUP_DIR,
            placeholder="Ex: C:\\Users\\SeuNome\\Desktop\\MinamiBackup"
        )
        
        col_testar, col_salvar = st.columns([1, 1])
        
        with col_testar:
            if st.button("🧪 Testar diretório"):
                if novo_path and _criar_diretorio_backup(novo_path):
                    st.success(f"✅ Diretório válido: {novo_path}")
                else:
                    st.error("❌ Não foi possível criar/acessar este diretório")
        
        with col_salvar:
            if st.button("💾 Salvar configuração"):
                if novo_path and _definir_caminho_backup(novo_path):
                    st.success("✅ Configuração salva com sucesso!")
                    st.rerun()
                else:
                    st.error("❌ Erro ao salvar configuração")

def interface_download_backup_nuvem(df_clientes):
    """Interface para download de backup da nuvem."""
    st.subheader("☁️ Download de Backup da Nuvem")
    
    st.info("💡 Use esta opção para salvar uma cópia do banco de dados no seu computador")
    
    if df_clientes is not None and not df_clientes.empty:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        col_csv, col_excel = st.columns([1, 1])
        
        with col_csv:
            csv_data = df_clientes.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"minami_backup_{timestamp}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_excel:
            excel_data = df_clientes.to_excel(index=False, engine='openpyxl')
            st.download_button(
                label="📥 Download Excel",
                data=excel_data,
                file_name=f"minami_backup_{timestamp}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    else:
        st.warning("⚠️ Não há dados na nuvem para fazer backup")

def interface_sincronizacao_automatica(df_clientes):
    """Interface para controle de sincronização automática."""
    st.subheader("🔄 Sincronização Automática")
    
    config = _carregar_config_backup()
    backup_dir = config.get("backup_dir")
    
    col_auto, col_manual = st.columns([1, 1])
    
    with col_auto:
        auto_sync = st.checkbox(
            "Sincronização automática",
            value=config.get("auto_sync", False),
            help="Salva backup automaticamente após cada alteração"
        )
    
    with col_manual:
        if st.button("💾 Sincronizar agora", use_container_width=True):
            if backup_dir:
                sucesso, msg, caminho = backup_local_para_arquivo(df_clientes, backup_dir)
                if sucesso:
                    st.success(f"✅ {msg}")
                    config["ultima_sincronizacao"] = datetime.now().isoformat()
                    _salvar_config_backup(config)
                else:
                    st.error(f"❌ {msg}")
            else:
                st.warning("⚠️ Configure o diretório de backup primeiro")
    
    # Salva configuração de auto sync
    if auto_sync != config.get("auto_sync", False):
        config["auto_sync"] = auto_sync
        _salvar_config_backup(config)