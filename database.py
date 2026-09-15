# =========================================================
# DATABASE - Supabase (produção) / SQLite (desenvolvimento)
# v4 - FIX: não faz fallback silencioso para SQLite
# =========================================================

import os
import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Optional, Dict, Any

# =========================================================
# STREAMLIT
# =========================================================

try:
    import streamlit as st
except ImportError:
    st = None

# =========================================================
# DOTENV
# =========================================================

try:
    from dotenv import load_dotenv

    env_path = os.path.join(os.path.dirname(__file__), ".env.local")
    load_dotenv(env_path)

    print(f"[DB] Carregando .env.local de: {env_path}")

except ImportError:
    print("[DB] python-dotenv não instalado, usando variáveis de ambiente do sistema")


# =========================================================
# BACKUP / SINCRONIZAÇÃO LOCAL
# =========================================================

try:
    from database_local_sync import (
        backup_local_para_arquivo,
        _carregar_config_backup
    )

    SYNC_AVAILABLE = True

except ImportError:
    SYNC_AVAILABLE = False
    print("[DB] database_local_sync não disponível")


# =========================================================
# CONFIGURAÇÃO SUPABASE
# =========================================================

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


# ---------------------------------------------------------
# Tenta carregar secrets.toml apenas se não veio do .env
# ---------------------------------------------------------

if st is not None:

    try:

        if not SUPABASE_URL:
            SUPABASE_URL = st.secrets.get(
                "SUPABASE_URL",
                ""
            )

        if not SUPABASE_KEY:
            SUPABASE_KEY = st.secrets.get(
                "SUPABASE_KEY",
                ""
            )

    except Exception:
        pass


# =========================================================
# MODO DE BANCO
# =========================================================
#
# IMPORTANTE:
#
# Se SUPABASE_URL e SUPABASE_KEY existirem:
#     → usamos Supabase
#
# Se não existirem:
#     → usamos SQLite local
#
# Se Supabase estiver configurado mas estiver com erro:
#     → NÃO cai para SQLite silenciosamente.
#
# Isso evita que usuários diferentes gravem em bancos
# diferentes sem perceber.
# =========================================================

USE_SUPABASE = bool(
    SUPABASE_URL and SUPABASE_KEY
)


print(
    f"[DB] USE_SUPABASE = {USE_SUPABASE}"
)


# =========================================================
# SUPABASE
# =========================================================

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

        # -------------------------------------------------
        # Testa a criação do cliente Supabase
        # -------------------------------------------------

        try:

            get_supabase()

            print(
                "[DB] ✅ Usando Supabase (PostgreSQL)"
            )

        except Exception as e:

            # NÃO muda USE_SUPABASE para False.
            #
            # Antes:
            #     erro Supabase → SQLite
            #
            # Isso podia fazer a Kaori salvar em outro banco.
            #
            error_message = (
                f"Não foi possível conectar ao Supabase: {e}"
            )

            print(
                f"[DB] ❌ {error_message}"
            )

            if st is not None:

                st.error(
                    "❌ Banco de dados indisponível.\n\n"
                    "O sistema tentou conectar ao Supabase, "
                    "mas não conseguiu.\n\n"
                    f"Detalhes: {e}\n\n"
                    "Nenhum dado será gravado em um banco local."
                )

            # Não usamos SQLite.
            raise RuntimeError(error_message) from e

    except ImportError as e:

        error_message = (
            "Supabase está configurado, mas "
            f"database_supabase.py não pôde ser importado: {e}"
        )

        print(f"[DB] ❌ {error_message}")

        if st is not None:

            st.error(
                "❌ Erro no módulo do Supabase.\n\n"
                f"{e}"
            )

        raise RuntimeError(error_message) from e


# =========================================================
# SQLITE
# =========================================================
#
# SQLite só será usado quando o Supabase NÃO estiver
# configurado.
#
# Isso permite usar SQLite no desenvolvimento local sem
# misturar os bancos em produção.
# =========================================================

if not USE_SUPABASE:

    BASE_DIR = os.path.dirname(
        os.path.abspath(__file__)
    )

    DB_NAME = os.path.join(
        BASE_DIR,
        "minami_service.db"
    )

    print(
        f"[DB] ⚠️ Supabase não configurado."
        f" Usando SQLite local: {DB_NAME}"
    )


    # =====================================================
    # CONEXÃO SQLITE
    # =====================================================

    @contextmanager
    def get_db_connection():

        conn = sqlite3.connect(
            DB_NAME
        )

        conn.row_factory = sqlite3.Row

        try:

            yield conn

            conn.commit()

        except Exception:

            conn.rollback()

            raise

        finally:

            conn.close()


    # =====================================================
    # INICIALIZAR BANCO
    # =====================================================

    def inicializar_banco():

        with get_db_connection() as conn:

            cur = conn.cursor()


            # -------------------------------------------------
            # CLIENTES
            # -------------------------------------------------

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
                    data_registro TEXT,
                    status TEXT,
                    observacao TEXT,
                    data_conclusao TEXT
                )
            """)


            # -------------------------------------------------
            # HISTÓRICO DE EXCLUSÕES
            # -------------------------------------------------

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


            # -------------------------------------------------
            # HISTÓRICO GERAL
            # -------------------------------------------------

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


            # -------------------------------------------------
            # GARANTE COLUNAS EM BANCOS ANTIGOS
            # -------------------------------------------------

            colunas = [
                "data_registro",
                "fabricante",
                "modelo_katashiki",
                "chassi_completo",
                "status",
                "observacao",
                "data_conclusao",
                "placa"
            ]


            for col in colunas:

                try:

                    cur.execute(
                        f"ALTER TABLE clientes "
                        f"ADD COLUMN {col} TEXT"
                    )

                except sqlite3.OperationalError:

                    # Coluna já existe.
                    pass


    # =====================================================
    # SALVAR CLIENTE
    # =====================================================

    def salvar_cliente(
        dados: Dict[str, Any]
    ) -> bool:

        print(
            f"[DEBUG SQLite] salvar_cliente chamado: "
            f"{dados}"
        )

        try:

            with get_db_connection() as conn:

                cur = conn.cursor()


                # -------------------------------------------------
                # Normaliza chassi
                # -------------------------------------------------

                chassi = dados.get("chassi")

                if chassi:

                    chassi = str(
                        chassi
                    ).strip().upper()

                else:

                    chassi = ""


                # -------------------------------------------------
                # INSERT
                # -------------------------------------------------

                cur.execute("""
                    INSERT INTO clientes (
                        nome,
                        contato,
                        shaken_vencimento,
                        veiculo,
                        placa,
                        chassi,
                        fabricante,
                        modelo_katashiki,
                        chassi_completo,
                        data_registro,
                        status,
                        observacao,
                        data_conclusao
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (

                    dados.get("nome", ""),

                    dados.get("contato") or "",

                    dados.get(
                        "shaken_vencimento",
                        ""
                    ),

                    dados.get(
                        "veiculo",
                        ""
                    ),

                    dados.get(
                        "placa",
                        ""
                    ),

                    chassi,

                    dados.get(
                        "fabricante",
                        ""
                    ),

                    dados.get(
                        "modelo_katashiki",
                        ""
                    ),

                    dados.get(
                        "chassi_completo",
                        ""
                    ),

                    dados.get(
                        "data_registro",
                        str(date.today())
                    ),

                    dados.get(
                        "status",
                        "Pendente"
                    ),

                    dados.get(
                        "observacao",
                        ""
                    ),

                    dados.get(
                        "data_conclusao",
                        ""
                    )

                ))


                cliente_id = cur.lastrowid


                print(
                    f"[DEBUG SQLite] "
                    f"Cliente salvo com ID: {cliente_id}"
                )


            # -------------------------------------------------
            # BACKUP AUTOMÁTICO
            #
            # O backup NUNCA pode transformar uma gravação
            # bem-sucedida em uma gravação considerada falha.
            # -------------------------------------------------

            if SYNC_AVAILABLE:

                try:

                    config = (
                        _carregar_config_backup()
                    )

                    if config.get(
                        "auto_sync",
                        False
                    ):

                        df_clientes = (
                            listar_clientes()
                        )

                        backup_local_para_arquivo(
                            df_clientes
                        )

                except Exception as e:

                    print(
                        "[DEBUG SQLite] "
                        f"Erro no backup automático: {e}"
                    )


            # -------------------------------------------------
            # IMPORTANTE:
            # True = banco confirmou a gravação
            # -------------------------------------------------

            return True


        except sqlite3.IntegrityError as e:

            print(
                "[DEBUG SQLite] "
                f"Erro de integridade: {e}"
            )

            if st is not None:

                st.error(
                    f"❌ Não foi possível salvar o cliente: {e}"
                )

            return False


        except Exception as e:

            print(
                "[DEBUG SQLite] "
                f"Erro salvando cliente: {e}"
            )

            if st is not None:

                st.error(
                    f"❌ Erro salvando cliente: {e}"
                )

            return False


    # =====================================================
    # LISTAR CLIENTES
    # =====================================================

    def listar_clientes(
        where_clause=None,
        params=None
    ):

        import pandas as pd


        try:

            with get_db_connection() as conn:

                cur = conn.cursor()


                if where_clause and params:

                    sql = (
                        "SELECT * FROM clientes "
                        f"WHERE {where_clause} "
                        "ORDER BY id DESC"
                    )

                    cur.execute(
                        sql,
                        params
                    )

                else:

                    cur.execute(
                        "SELECT * FROM clientes "
                        "ORDER BY id DESC"
                    )


                data = [
                    dict(row)
                    for row in cur.fetchall()
                ]


                print(
                    f"[DEBUG SQLite] "
                    f"listar_clientes: {len(data)} registros"
                )


                return pd.DataFrame(
                    data
                )


        except Exception as e:

            print(
                "[DEBUG SQLite] "
                f"Erro listando clientes: {e}"
            )

            if st is not None:

                st.error(
                    f"❌ Erro ao listar clientes: {e}"
                )

            return pd.DataFrame()


    # =====================================================
    # BUSCAR POR CHASSI
    # =====================================================

    def buscar_cliente_por_chassi(
        chassi
    ):

        if chassi:

            chassi = str(
                chassi
            ).strip().upper()


        try:

            with get_db_connection() as conn:

                cur = conn.cursor()

                cur.execute(
                    """
                    SELECT *
                    FROM clientes
                    WHERE chassi = ?
                    """,
                    (chassi,)
                )

                row = cur.fetchone()

                return (
                    dict(row)
                    if row
                    else None
                )


        except Exception as e:

            print(
                "[DEBUG SQLite] "
                f"Erro buscando chassi: {e}"
            )

            return None


    # =====================================================
    # ATUALIZAR CLIENTE
    # =====================================================

    def atualizar_cliente(
        cliente_id,
        dados
    ):

        print(
            "[DEBUG SQLite] "
            f"atualizar_cliente: ID={cliente_id}"
        )


        try:

            with get_db_connection() as conn:

                cur = conn.cursor()

                campos = []
                valores = []


                for chave, valor in dados.items():

                    if chave == "id":
                        continue

                    # Evita tentar atualizar colunas
                    # que não existem ou campos internos.
                    if str(chave).startswith("_"):
                        continue

                    campos.append(
                        f"{chave} = ?"
                    )

                    valores.append(
                        valor
                    )


                if not campos:

                    return False


                valores.append(
                    cliente_id
                )


                sql = (
                    "UPDATE clientes SET "
                    + ", ".join(campos)
                    + " WHERE id = ?"
                )


                cur.execute(
                    sql,
                    valores
                )


                atualizado = (
                    cur.rowcount > 0
                )


                print(
                    "[DEBUG SQLite] "
                    f"UPDATE executado: {atualizado}"
                )


            # -------------------------------------------------
            # BACKUP
            # -------------------------------------------------

            if SYNC_AVAILABLE:

                try:

                    config = (
                        _carregar_config_backup()
                    )

                    if config.get(
                        "auto_sync",
                        False
                    ):

                        df_clientes = (
                            listar_clientes()
                        )

                        backup_local_para_arquivo(
                            df_clientes
                        )

                except Exception as e:

                    print(
                        "[DEBUG SQLite] "
                        f"Erro no backup: {e}"
                    )


            return atualizado


        except Exception as e:

            print(
                "[DEBUG SQLite] "
                f"Erro atualizando cliente: {e}"
            )

            if st is not None:

                st.error(
                    f"❌ Erro atualizando cliente: {e}"
                )

            return False


    # =====================================================
    # DELETAR CLIENTE
    # =====================================================

    def deletar_cliente(
        cliente_id
    ):

        try:

            with get_db_connection() as conn:

                cur = conn.cursor()

                cur.execute(
                    """
                    DELETE FROM clientes
                    WHERE id = ?
                    """,
                    (cliente_id,)
                )

                removido = (
                    cur.rowcount > 0
                )


                return removido


        except Exception as e:

            print(
                "[DEBUG SQLite] "
                f"Erro deletando cliente: {e}"
            )

            if st is not None:

                st.error(
                    f"❌ Erro deletando cliente: {e}"
                )

            return False


    # =====================================================
    # HISTÓRICO
    # =====================================================

    def salvar_historico(
        dados
    ):

        # Mantido por compatibilidade
        # com o restante do sistema.

        return True


    # =====================================================
    # DESFAZER
    # =====================================================

    def desfazer_ultima_acao():

        return (
            True,
            "Desfazer não implementado no SQLite"
        )
