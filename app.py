# =========================================================
# IMPORTS
# =========================================================

import os
from datetime import date, timedelta
import re

import pandas as pd
import streamlit as st

import streamlit.components.v1 as _stc
from database import (
    inicializar_banco,
    salvar_cliente,
    listar_clientes,
    atualizar_cliente,
    deletar_cliente,
    desfazer_ultima_acao
)
from ocr_service import converter_data_japonesa, traduzir_veiculo
from ui_base import inject_base_css
from auth import require_login, can, logout_button, _load_config, _save_config

# =========================================================
# CONFIG
# =========================================================

# Carrega ícone da logo
_icon_path = os.path.join(os.path.dirname(__file__), ".streamlit", "icon_b64.txt")
_page_icon = "🚗"
try:
    with open(_icon_path, "r") as f:
        _icon_data = f.read().strip()
        if _icon_data:
            _page_icon = f"data:image/png;base64,{_icon_data}"
except:
    pass

st.set_page_config("Central Shaken", layout="wide", initial_sidebar_state="expanded", page_icon=_page_icon)
inject_base_css()

# Meta tags para PWA - melhor aparência ao salvar na área de trabalho
st.markdown(f"""
<meta name="application-name" content="Central Shaken">
<meta name="apple-mobile-web-app-title" content="Central Shaken">
<meta name="theme-color" content="#0d2a6e">
<link rel="shortcut icon" href="{_page_icon}" type="image/png">
""", unsafe_allow_html=True)

require_login()

# ── JS global: killMenu + openSidebar ──────────────────────────────────
st.markdown("""
<script>
(function(){
    // Função para esconder menus indesejados
    function killMenu(){
        document.querySelectorAll('[data-testid="stDataFrameColumnMenu"]').forEach(function(el){el.style.display='none';});
        document.querySelectorAll('[role="menu"]').forEach(function(el){
            var txt=el.innerText||"";
            if(txt.includes("Sort ascending")||txt.includes("Hide column")||txt.includes("Pin column")){el.style.display="none";}
        });
    }
    if(!window._killMenuObs){
        window._killMenuObs=new MutationObserver(killMenu);
        window._killMenuObs.observe(document.body,{childList:true,subtree:true});
    }
    
    // Função global para abrir sidebar (apenas clica no botão nativo)
    window.openSidebar = function(){
        var btn = document.querySelector('button[aria-label*="sidebar"], button[aria-label*="Open sidebar"]');
        if(btn){ btn.click(); }
    };

    // Remove botões Fork e GitHub do header por texto
    function removeGitHubButtons(){
        var buttons = document.querySelectorAll('button');
        buttons.forEach(function(btn){
            var text = btn.innerText || btn.textContent || '';
            var title = btn.getAttribute('title') || '';
            var ariaLabel = btn.getAttribute('aria-label') || '';

            // Preserva botão de abrir sidebar (»)
            if(ariaLabel.includes('Open sidebar') || ariaLabel.includes('sidebar') || text.includes('»') || text.includes('▶')){
                return;
            }

            // Remove apenas Fork e GitHub
            if(text.includes('Fork') || title.includes('Fork') || text.includes('GitHub') || title.includes('GitHub') || title.includes('git')){
                btn.remove();
            }
        });

        // Também procura links do GitHub
        var links = document.querySelectorAll('a');
        links.forEach(function(link){
            var href = link.getAttribute('href') || '';
            var text = link.innerText || link.textContent || '';
            if(href.includes('github.com') && (text.includes('Fork') || text.includes('GitHub'))){
                link.remove();
            }
        });
    }
    setInterval(removeGitHubButtons, 500);
})();
</script>
""", unsafe_allow_html=True)

# ── Fogos + Confetes + Som de Comemoração (novo iframe a cada celebração via counter) ──
if st.session_state.get("_celebrar") and st.session_state.get("_celebration_enabled", True):
    st.session_state._celebrar = False
    st.session_state._celebrar_count += 1
    _stc.html(f"""
    <!-- celebrar_{st.session_state._celebrar_count} -->
    <script>
    (function(){{
        // Sobe até o documento raiz (pode estar em iframe aninhado)
        var _root = window;
        try {{ while(_root.parent && _root.parent !== _root) _root = _root.parent; }} catch(e){{}}
        var doc = _root.document;

        // Injeta estilos
        var sid = 'cf-style-{st.session_state._celebrar_count}';
        if(!doc.getElementById(sid)){{
            var s=doc.createElement('style');
            s.id=sid;
            s.textContent=`
                @keyframes cf-rise{{0%{{transform:translateY(0) scale(1);opacity:1}}100%{{transform:translateY(-150px) scale(0.1);opacity:0}}}}
                @keyframes cf-fall{{0%{{transform:translateY(0) rotate(0deg);opacity:1}}100%{{transform:translateY(100vh) rotate(1080deg);opacity:0}}}}
                @keyframes burst{{0%{{transform:scale(0);opacity:1}}50%{{transform:scale(1.5);opacity:1}}100%{{transform:scale(2.5);opacity:0}}}}
                @keyframes twinkle{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:0.5;transform:scale(1.2)}}}}
                @keyframes float{{0%,100%{{transform:translateY(0) rotate(0deg)}}50%{{transform:translateY(-20px) rotate(180deg)}}}}
                .cf-p{{position:fixed;border-radius:3px;animation:cf-fall linear forwards;z-index:99999;pointer-events:none;}}
                .cf-spark{{position:fixed;border-radius:50%;animation:cf-rise ease-out forwards;z-index:99999;pointer-events:none;}}
                .cf-burst{{position:fixed;border-radius:50%;border:3px solid;animation:burst ease-out forwards;z-index:99999;pointer-events:none;}}
                .cf-star{{position:fixed;animation:twinkle 0.8s ease-in-out infinite,z-index:99999;pointer-events:none;}}
                .cf-heart{{position:fixed;animation:float 2s ease-in-out infinite,z-index:99999;pointer-events:none;}}
            `;
            doc.head.appendChild(s);
        }}

        var cores=['#ffd600','#ff4081','#00c853','#00bcd4','#aa00ff','#ff6d00','#ffffff','#1044b5','#ffeb3b','#ff9800','#e91e63','#9c27b0','#2196f3','#4caf50','#ff5722'];

        // Som de comemoração usando Web Audio API
        var audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        function playCelebrationSound(){{
            var duration = 3.0;
            var now = audioCtx.currentTime;
            
            // Melodia de comemoração (arpejo ascendente)
            var notes = [523.25, 659.25, 783.99, 1046.50, 783.99, 1046.50, 1318.51]; // C5, E5, G5, C6, G5, C6, E6
            var noteDuration = 0.15;
            
            notes.forEach(function(freq, i){{
                var osc = audioCtx.createOscillator();
                var gain = audioCtx.createGain();
                osc.type = 'sine';
                osc.frequency.value = freq;
                gain.gain.setValueAtTime(0.3, now + i * noteDuration);
                gain.gain.exponentialRampToValueAtTime(0.01, now + i * noteDuration + noteDuration - 0.05);
                osc.connect(gain);
                gain.connect(audioCtx.destination);
                osc.start(now + i * noteDuration);
                osc.stop(now + i * noteDuration + noteDuration);
            }});
            
            // Efeito de "ta-da" final
            setTimeout(function(){{
                var osc1 = audioCtx.createOscillator();
                var osc2 = audioCtx.createOscillator();
                var gain1 = audioCtx.createGain();
                var gain2 = audioCtx.createGain();
                osc1.type = 'triangle';
                osc2.type = 'sine';
                osc1.frequency.value = 523.25;
                osc2.frequency.value = 659.25;
                gain1.gain.setValueAtTime(0.4, audioCtx.currentTime);
                gain1.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.8);
                gain2.gain.setValueAtTime(0.4, audioCtx.currentTime);
                gain2.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.8);
                osc1.connect(gain1);
                osc2.connect(gain2);
                gain1.connect(audioCtx.destination);
                gain2.connect(audioCtx.destination);
                osc1.start();
                osc2.start();
                osc1.stop(audioCtx.currentTime + 0.8);
                osc2.stop(audioCtx.currentTime + 0.8);
            }}, notes.length * noteDuration * 1000);
        }}
        playCelebrationSound();

        // Localiza a sidebar no DOM pai e calcula centro
        var sidebar = doc.querySelector('[data-testid="stSidebar"]');
        var sbRect = sidebar ? sidebar.getBoundingClientRect() : null;
        var sbL   = sbRect ? sbRect.left   : 0;
        var sbW   = sbRect ? sbRect.width  : Math.min(320, window.parent.innerWidth * 0.21);
        var sbT   = sbRect ? sbRect.top    : 0;
        var sbH   = sbRect ? sbRect.height : window.parent.innerHeight;
        var sbCX  = sbL + sbW / 2;
        var sbCY  = sbT + sbH / 2;

        // 8 fogos espalhados pela sidebar
        var origens = [
            {{x: sbCX,          y: sbCY}},
            {{x: sbL + sbW*0.25, y: sbT + sbH*0.25}},
            {{x: sbL + sbW*0.75, y: sbT + sbH*0.25}},
            {{x: sbL + sbW*0.25, y: sbT + sbH*0.75}},
            {{x: sbL + sbW*0.75, y: sbT + sbH*0.75}},
            {{x: sbL + sbW*0.5, y: sbT + sbH*0.2}},
            {{x: sbL + sbW*0.5, y: sbT + sbH*0.8}},
            {{x: sbL + sbW*0.1, y: sbT + sbH*0.5}}
        ];

        origens.forEach(function(orig, fi){{
            setTimeout(function(){{
                var cor = cores[fi % cores.length];
                // Trilha ascendente (foguete subindo)
                var trail = doc.createElement('div');
                trail.style.cssText = `position:fixed;left:${{orig.x}}px;top:${{orig.y+80}}px;
                    width:4px;height:${{40+Math.random()*40}}px;
                    background:linear-gradient(${{cor}},transparent);
                    z-index:99999;pointer-events:none;
                    transition:transform 0.4s ease-in,opacity 0.4s;opacity:1;
                    box-shadow:0 0 8px ${{cor}};`;
                doc.body.appendChild(trail);
                setTimeout(function(){{
                    trail.style.transform='translateY(-80px)';
                    trail.style.opacity='0';
                }},20);
                setTimeout(function(){{trail.remove();}},500);

                // Explosão: partículas em todas as direções
                setTimeout(function(){{
                    for(var p=0;p<40;p++){{
                        (function(pi){{
                            var spark=doc.createElement('div');
                            var ang=(pi/40)*2*Math.PI;
                            var dist=60+Math.random()*120;
                            var tx=Math.cos(ang)*dist;
                            var ty=Math.sin(ang)*dist;
                            var c=cores[(fi*3+pi)%cores.length];
                            spark.style.cssText=`position:fixed;
                                left:${{orig.x}}px;top:${{orig.y}}px;
                                width:${{4+Math.random()*6}}px;height:${{4+Math.random()*6}}px;
                                background:${{c}};border-radius:50%;
                                z-index:99999;pointer-events:none;
                                box-shadow:0 0 6px ${{c}},0 0 12px ${{c}};
                                transition:transform ${{0.6+Math.random()*0.6}}s ease-out,opacity ${{0.6+Math.random()*0.5}}s ease-out;
                                opacity:1;`;
                            doc.body.appendChild(spark);
                            requestAnimationFrame(function(){{requestAnimationFrame(function(){{
                                spark.style.transform=`translate(${{tx}}px,${{ty}}px)`;
                                spark.style.opacity='0';
                            }});}});
                            setTimeout(function(){{spark.remove();}},1400);
                        }})(p);
                    }}
                    // Anel de onda
                    var ring=doc.createElement('div');
                    ring.style.cssText=`position:fixed;
                        left:${{orig.x-8}}px;top:${{orig.y-8}}px;
                        width:16px;height:16px;
                        border:4px solid ${{cor}};border-radius:50%;
                        z-index:99999;pointer-events:none;
                        transition:transform 0.6s ease-out,opacity 0.6s ease-out;opacity:1;
                        box-shadow:0 0 10px ${{cor}};`;
                    doc.body.appendChild(ring);
                    requestAnimationFrame(function(){{requestAnimationFrame(function(){{
                        ring.style.transform='scale(18)';
                        ring.style.opacity='0';
                    }});}});
                    setTimeout(function(){{ring.remove();}},700);
                    
                    // Segundo anel
                    var ring2=doc.createElement('div');
                    ring2.style.cssText=`position:fixed;
                        left:${{orig.x-6}}px;top:${{orig.y-6}}px;
                        width:12px;height:12px;
                        border:3px solid ${{cores[(fi+1)%cores.length]}};border-radius:50%;
                        z-index:99999;pointer-events:none;
                        transition:transform 0.8s ease-out,opacity 0.8s ease-out;opacity:1;`;
                    doc.body.appendChild(ring2);
                    requestAnimationFrame(function(){{requestAnimationFrame(function(){{
                        ring2.style.transform='scale(22)';
                        ring2.style.opacity='0';
                    }});}});
                    setTimeout(function(){{ring2.remove();}},900);
                }},350);
            }}, fi*250);
        }});

        // Confetes caindo do topo (aumentado para 250)
        setTimeout(function(){{
            for(var i=0;i<250;i++){{
                (function(idx){{
                    setTimeout(function(){{
                        var el=doc.createElement('div');
                        el.className='cf-p';
                        el.style.left=(Math.random()*100)+'vw';
                        el.style.top='-30px';
                        el.style.background=cores[idx%cores.length];
                        el.style.width=(8+Math.random()*12)+'px';
                        el.style.height=(12+Math.random()*18)+'px';
                        el.style.animationDuration=(1.8+Math.random()*3.2)+'s';
                        el.style.boxShadow='0 0 4px '+cores[idx%cores.length];
                        doc.body.appendChild(el);
                        setTimeout(function(){{el.remove();}},6000);
                    }}, idx*8);
                }})(i);
            }}
        }}, 500);
        
        // Estrelas brilhantes espalhadas
        setTimeout(function(){{
            for(var i=0;i<30;i++){{
                (function(idx){{
                    var star=doc.createElement('div');
                    star.className='cf-star';
                    star.style.left=(Math.random()*100)+'vw';
                    star.style.top=(Math.random()*100)+'vh';
                    star.style.width=(10+Math.random()*15)+'px';
                    star.style.height=(10+Math.random()*15)+'px';
                    star.style.background=cores[idx%cores.length];
                    star.style.clipPath='polygon(50% 0%, 61% 35%, 98% 35%, 68% 57%, 79% 91%, 50% 70%, 21% 91%, 32% 57%, 2% 35%, 39% 35%)';
                    star.style.animationDelay=(Math.random()*2)+'s';
                    doc.body.appendChild(star);
                    setTimeout(function(){{star.remove();}},4000);
                }})(i);
            }}
        }}, 600);

    }})();
    </script>
    """, height=0)


# =========================================================
# INIT
# =========================================================

try:
    inicializar_banco()
except NameError:
    # Supabase ativo - não precisa inicializar SQLite
    pass

if "delete_mode" not in st.session_state:
    st.session_state.delete_mode = False

if "_aviso_exclusao" not in st.session_state:
    st.session_state._aviso_exclusao = []

if "_aviso_data_conc" not in st.session_state:
    st.session_state._aviso_data_conc = False

if "_aviso_formato" not in st.session_state:
    st.session_state._aviso_formato = None
    # estrutura: {"msg": str, "pode_salvar": bool, "row_dict": dict, "cliente_id": int, "col": str, "val": str}

if "_editor_v" not in st.session_state:
    st.session_state._editor_v = 0  # incrementado para forçar recriação do editor

if "_celebrar" not in st.session_state:
    st.session_state._celebrar = False

if "_celebrar_count" not in st.session_state:
    st.session_state._celebrar_count = 0

if "cliente_selecionado" not in st.session_state:
    st.session_state.cliente_selecionado = None

# Sistema de desfazer exclusão de clientes
if "linhas_excluidas" not in st.session_state:
    st.session_state.linhas_excluidas = []

# Sistema de desfazer última edição (plain text - 1 edição = 1 desfazer)
if "ultima_edicao" not in st.session_state:
    st.session_state.ultima_edicao = None

if "sort_col" not in st.session_state:
    st.session_state.sort_col = None
    st.session_state.sort_dir = 0  # 0=original, 1=asc, 2=desc

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = 0

PAGE_SIZE = 50

def carregar_clientes():
    df = listar_clientes()
    if "veiculo" in df.columns:
        df["veiculo"] = df["veiculo"].apply(traduzir_veiculo)
    return df


def _fmt_contato_wa(numero):
    """Converte número japonês para link WhatsApp clicável."""
    if not numero or pd.isna(numero):
        return ""
    # Remove espaços, hífens, parênteses
    clean = re.sub(r"[\s\-\(\)]", "", str(numero))
    # Remove 0 inicial e adiciona 81 (código do Japão)
    if clean.startswith("0") and len(clean) >= 10:
        intl = "81" + clean[1:]
        wa_url = f"https://wa.me/{intl}"
        return f'<a href="{wa_url}" target="_blank">{numero}</a>'
    return numero


def _get_wa_url(numero):
    """Retorna URL do WhatsApp ou None se inválido."""
    if not numero or pd.isna(numero):
        return None
    clean = re.sub(r"[\s\-\(\)]", "", str(numero))
    if clean.startswith("0") and len(clean) >= 10:
        return f"https://wa.me/81{clean[1:]}"
    return None

if "df" not in st.session_state:
    st.session_state.df = carregar_clientes()

# Recarrega se a coluna status não estiver presente (banco foi atualizado)
if "status" not in st.session_state.df.columns:
    st.session_state.df = carregar_clientes()

# Garante tradução de veículos já em memória
if "veiculo" in st.session_state.df.columns:
    st.session_state.df["veiculo"] = st.session_state.df["veiculo"].apply(traduzir_veiculo)

# =========================================================
# SIDEBAR
# =========================================================

# Processa configurações via query param
if st.query_params.get("config") == "1":
    st.query_params.clear()
    st.session_state._show_config = True

# Session states para configurações
if "_show_config" not in st.session_state:
    st.session_state._show_config = False
if "_dark_mode" not in st.session_state:
    # Carrega configurações salvas
    config = _load_config()
    st.session_state._dark_mode = config.get("dark_mode", False)
if "_celebration_enabled" not in st.session_state:
    # Carrega configurações salvas
    config = _load_config()
    st.session_state._celebration_enabled = config.get("celebration_enabled", True)

logout_button()

# Download banco de dados (apenas para Kaori)
if st.session_state.get("usuario") == "Kaori":
    with st.sidebar:
        st.markdown("---")
        st.markdown("<div style='font-size:0.75rem;color:#666;'>Backup BD</div>", unsafe_allow_html=True)
        try:
            with open("minami_service.db", "rb") as f:
                db_bytes = f.read()
            st.download_button(
                label="💾 Download BD",
                data=db_bytes,
                file_name=f"minami_service_backup_{date.today().strftime('%Y%m%d')}.db",
                mime="application/octet-stream",
                use_container_width=True
            )
        except Exception as e:
            st.sidebar.caption("BD não disponível")

# Modal de configurações
if st.session_state._show_config:
    with st.sidebar:
        st.markdown("---")
        st.subheader("⚙️ Configurações")
        
        # Modo escuro/claro
        dark_mode = st.toggle(
            "🌙 Modo Escuro",
            value=st.session_state._dark_mode,
            key="config_dark_mode"
        )
        st.session_state._dark_mode = dark_mode
        
        # Animar conclusão
        celebration = st.toggle(
            "🎉 Animar Conclusão",
            value=st.session_state._celebration_enabled,
            key="config_celebration"
        )
        st.session_state._celebration_enabled = celebration
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Salvar", use_container_width=True):
                _save_config(st.session_state._dark_mode, st.session_state._celebration_enabled)
                st.session_state._show_config = False
                st.rerun()
        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state._show_config = False
                st.rerun()
        
        st.markdown("---")

# Aplica CSS para modo escuro (sidebar continua azul)
if st.session_state._dark_mode:
    st.markdown("""
    <style>
    /* Modo escuro - apenas conteúdo principal, sidebar continua azul */
    .stApp {
        background-color: #1a1a2e !important;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #1a1a2e !important;
    }
    [data-testid="stMain"] {
        background-color: #1a1a2e !important;
    }
    /* Tabelas em modo escuro */
    .stDataFrame {
        background-color: #16213e !important;
        color: #eaeaea !important;
    }
    .stDataFrame [data-testid="stDataFrame"] {
        background-color: #16213e !important;
    }
    .stDataFrame [data-testid="stDataFrame"] thead th {
        background-color: #0f3460 !important;
        color: #eaeaea !important;
        border-bottom: 2px solid #e94560 !important;
    }
    .stDataFrame [data-testid="stDataFrame"] tbody tr {
        background-color: #16213e !important;
        color: #eaeaea !important;
        border-bottom: 1px solid #0f3460 !important;
    }
    .stDataFrame [data-testid="stDataFrame"] tbody tr:hover {
        background-color: #1a1a2e !important;
    }
    /* Inputs e campos de texto */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background-color: #87ceeb !important;
        color: #1a1a2e !important;
    }
    /* Botões */
    .stButton > button {
        background-color: #1044b5 !important;
        color: #ffffff !important;
    }
    .stButton > button:hover {
        background-color: #0d2a6e !important;
    }
    /* Expander */
    .streamlit-expanderHeader {
        background-color: #0f3460 !important;
        color: #eaeaea !important;
    }
    /* Texto geral */
    h1, h2, h3, h4, h5, h6, p, span, div {
        color: #eaeaea !important;
    }
    /* Sidebar mantém azul (sobrescreve modo escuro) */
    [data-testid="stSidebar"] {
        background-color: #1044b5 !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        background-color: #1044b5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

df_all = carregar_clientes()
hoje = pd.to_datetime(date.today())

if not df_all.empty and "shaken_vencimento" in df_all.columns:
    df_all["dt"] = pd.to_datetime(df_all["shaken_vencimento"], errors="coerce")

    total_clientes = len(df_all)

    prox_30 = df_all[
        (df_all["dt"] >= hoje) &
        (df_all["dt"] <= hoje + pd.Timedelta(days=30))
    ]
    prox_60 = df_all[
        (df_all["dt"] > hoje + pd.Timedelta(days=30)) &
        (df_all["dt"] <= hoje + pd.Timedelta(days=60))
    ]
    prox_mais = df_all[
        df_all["dt"] > hoje + pd.Timedelta(days=60)
    ].dropna(subset=["dt"]).sort_values("dt").head(5)

    def normalizar_status_sidebar(v):
        if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "⚪"):
            return "⚪"
        elif "processamento" in str(v).lower() or v == "🔵 Em processamento":
            return "🔵 Em processamento"
        elif "concluido" in str(v).lower() or v == "🟢 Concluido":
            return "🟢 Concluido"
        return "⚪"

    df_all["status_norm"] = df_all["status"].apply(normalizar_status_sidebar)
    total_processamento = (df_all["status_norm"] == "🔵 Em processamento").sum()
    total_concluido = (df_all["status_norm"] == "🟢 Concluido").sum()

    top5 = prox_mais.dropna(subset=["dt"]).sort_values("dt").head(5)

    st.sidebar.markdown("""
    <style>
    /* Ocultar navegação de páginas da sidebar */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(160deg, #0d2a6e 0%, #1044b5 60%, #0a1f5c 100%) !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    /* Expanders na sidebar — fundo fixo azul, sem mudar ao hover/focus */
    [data-testid="stSidebar"] details summary {
        background: rgba(255,255,255,0.08) !important;
        border-radius: 8px !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] details summary:hover,
    [data-testid="stSidebar"] details summary:focus,
    [data-testid="stSidebar"] details[open] summary {
        background: rgba(255,255,255,0.08) !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] details > div {
        background: rgba(255,255,255,0.04) !important;
        border-radius: 0 0 8px 8px !important;
    }
    /* Botões dentro da sidebar — cor fixa, sem hover branco */
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] button {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        color: #FFFFFF !important;
        border-radius: 6px !important;
        white-space: nowrap !important;
        padding: 0.25rem 1.5rem !important;
        text-align: left !important;
    }
    [data-testid="stSidebar"] button:hover,
    [data-testid="stSidebar"] button:focus,
    [data-testid="stSidebar"] button:active {
        background: rgba(255,255,255,0.12) !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        color: #FFFFFF !important;
        white-space: nowrap !important;
        padding: 0.25rem 1.5rem !important;
        text-align: left !important;
    }
    .sb-title {
        font-size: 1.25rem;
        font-weight: 800;
        color: #FFFFFF !important;
        letter-spacing: 0.04em;
        margin-bottom: 0.2rem;
    }
    .sb-divider {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.2);
        margin: 0.75rem 0;
    }
    .sb-section {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: rgba(255,255,255,0.5) !important;
        margin: 0.9rem 0 0.35rem 0;
    }
    .sb-card {
        background: rgba(255,255,255,0.09);
        border-radius: 10px;
        padding: 0.55rem 0.9rem;
        margin-bottom: 0.45rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .sb-card-label { font-size: 0.88rem; color: rgba(255,255,255,0.9) !important; }
    .sb-card-value { font-size: 1.35rem; font-weight: 800; color: #FFFFFF !important; }
    .sb-card-warn  { border-left: 3px solid #FF4B4B; }
    .sb-card-amber { border-left: 3px solid #FFA500; }
    .sb-card-blue  { border-left: 3px solid #FFFFFF; }
    .sb-card-green { border-left: 3px solid #2ECC71; }
    .sb-card-total { border-left: 3px solid rgba(255,255,255,0.35); }
    /* Bolinha azul com contorno branco */
    .dot-blue {
        display: inline-block;
        width: 13px; height: 13px;
        border-radius: 50%;
        background: #4B9EFF;
        border: 2px solid #FFFFFF;
        vertical-align: middle;
        margin-right: 6px;
    }
    .dot-green {
        display: inline-block;
        width: 13px; height: 13px;
        border-radius: 50%;
        background: #2ECC71;
        border: 2px solid #FFFFFF;
        vertical-align: middle;
        margin-right: 6px;
    }
    /* Cliente row nos expanders */
    .cli-name { font-size: 0.92rem; font-weight: 700; color: #FFFFFF !important; }
    .cli-date { font-size: 0.8rem; color: rgba(255,255,255,0.65) !important; margin-top: 1px; }
    .cli-detail { font-size: 0.82rem; color: rgba(255,255,255,0.8) !important; margin-top: 3px; }
    </style>
    """, unsafe_allow_html=True)

    # Total de clientes
    st.sidebar.markdown('<div class="sb-section">Clientes</div>', unsafe_allow_html=True)
    st.sidebar.markdown(f"""
    <div class="sb-card sb-card-total">
        <span class="sb-card-label">👥 Total de clientes</span>
        <span class="sb-card-value">{total_clientes}</span>
    </div>
    <div class="sb-card sb-card-green">
        <span class="sb-card-label"><span class="dot-green"></span>Concluídos</span>
        <span class="sb-card-value">{total_concluido}</span>
    </div>
    """, unsafe_allow_html=True)

    # Shaken vencendo
    st.sidebar.markdown('<div class="sb-section">Shaken Vencendo</div>', unsafe_allow_html=True)

    def render_grupo_clientes(grupo_df):
        if grupo_df.empty:
            st.write("Nenhum cliente")
            return
        for _, r in grupo_df.sort_values("dt").iterrows():
            data_fmt = r["dt"].strftime("%d/%m/%Y") if pd.notna(r["dt"]) else "—"
            with st.expander(f"{r['nome']}  ·  {data_fmt}"):
                st.write(f"**Veículo:** {r['veiculo'] or '—'}")
                contato = r['contato'] or '—'
                wa_url = _get_wa_url(contato)
                if wa_url:
                    st.markdown(f"**Contato:** {contato} [💬 WhatsApp]({wa_url})")
                else:
                    st.write(f"**Contato:** {contato}")
                st.write(f"**Chassi:** {r['chassi'] or '—'}")

    with st.sidebar.expander(f"\U0001f534 Em 30 dias  ({len(prox_30)})"):
        render_grupo_clientes(prox_30)

    with st.sidebar.expander(f"🟠 Em 60 dias  ({len(prox_60)})"):
        render_grupo_clientes(prox_60)

    with st.sidebar.expander(f"📆 Próximos vencimentos  ({len(prox_mais)})"):
        render_grupo_clientes(top5)

    # Status
    st.sidebar.markdown('<hr class="sb-divider">', unsafe_allow_html=True)
    st.sidebar.markdown('<div class="sb-section">Status</div>', unsafe_allow_html=True)

    df_processamento = df_all[df_all["status_norm"] == "🔵 Em processamento"]
    df_concluido = df_all[df_all["status_norm"] == "🟢 Concluido"]

    with st.sidebar.expander(f"🔵 Em processamento  ({total_processamento})"):
        if df_processamento.empty:
            st.write("Nenhum cliente")
        else:
            for _, r in df_processamento.iterrows():
                col_nome, col_btn = st.columns([1, 1.5])
                with col_nome:
                    st.write(f"**{r['nome']}**")
                with col_btn:
                    if st.button("✅ Concluir", key=f"concluir_{r['id']}"):
                        row_dict = r.drop(["dt", "status_norm"], errors='ignore').to_dict()
                        row_dict["status"] = "🟢 Concluido"
                        # Preenche data_conclusao automaticamente
                        row_dict["data_conclusao"] = str(date.today())
                        st.success(f"Data de conclusão definida: {row_dict['data_conclusao']}")
                        atualizar_cliente(r["id"], row_dict)
                        st.session_state.df = carregar_clientes()
                        st.session_state._celebrar = True
                        st.session_state._sb_scroll = "concluidos"
                        st.session_state._editor_v += 1  # força tabela mostrar data_conclusao imediatamente
                        st.rerun()

    with st.sidebar.expander(f"🟢 Concluídos  ({total_concluido})"):
        if df_concluido.empty:
            st.write("Nenhum cliente")
        else:
            periodo_conc = st.radio(
                "Período",
                ["Este mês", "Este ano", "Total"],
                horizontal=True,
                key="periodo_concluidos",
                label_visibility="collapsed"
            )

            df_concluido_dt = df_concluido.copy()
            # Usa data_conclusao; se NULL (registros antigos), usa data_registro como fallback
            if "data_conclusao" in df_concluido_dt.columns:
                df_concluido_dt["dt_conc"] = pd.to_datetime(df_concluido_dt["data_conclusao"], errors="coerce")
                if "data_registro" in df_concluido_dt.columns:
                    _fallback = pd.to_datetime(df_concluido_dt["data_registro"], errors="coerce")
                    df_concluido_dt["dt_conc"] = df_concluido_dt["dt_conc"].fillna(_fallback)
            elif "data_registro" in df_concluido_dt.columns:
                df_concluido_dt["dt_conc"] = pd.to_datetime(df_concluido_dt["data_registro"], errors="coerce")
            else:
                df_concluido_dt["dt_conc"] = pd.NaT

            if periodo_conc == "Este mês":
                df_conc_filtrado = df_concluido_dt[
                    (df_concluido_dt["dt_conc"].dt.year == hoje.year) &
                    (df_concluido_dt["dt_conc"].dt.month == hoje.month)
                ]
            elif periodo_conc == "Este ano":
                df_conc_filtrado = df_concluido_dt[
                    df_concluido_dt["dt_conc"].dt.year == hoje.year
                ]
            else:
                df_conc_filtrado = df_concluido_dt

            if df_conc_filtrado.empty:
                st.write(f"Nenhum concluído neste período.")
            else:
                st.caption(f"{len(df_conc_filtrado)} cliente(s)")
                for _, r in df_conc_filtrado.sort_values("dt_conc", ascending=False).iterrows():
                    _dt_fmt = r["dt_conc"].strftime("%d/%m/%Y") if pd.notna(r["dt_conc"]) else "—"
                    col_nome, col_btn = st.columns([1, 1.5])
                    with col_nome:
                        st.markdown(f"**{r['nome']}**  \n<span style='font-size:0.78rem;color:rgba(255,255,255,0.55)'>Concluído: {_dt_fmt}</span>", unsafe_allow_html=True)
                    with col_btn:
                        if st.button("🔵 Reabrir", key=f"reabrir_{r['id']}"):
                            row_dict = r.drop(["dt", "status_norm", "dt_conc"], errors='ignore').to_dict()
                            row_dict["status"] = "🔵 Em processamento"
                            atualizar_cliente(r["id"], row_dict)
                            st.session_state.df = carregar_clientes()
                            st.session_state._sb_scroll = "processamento"
                            st.session_state._editor_v += 1
                            # Marca ciclo: próxima conclusão mostra ↺ em azul
                            if "_conc_ciclos" not in st.session_state:
                                st.session_state._conc_ciclos = set()
                            st.session_state._conc_ciclos.add(r["id"])
                            st.rerun()

else:
    pass

# ── Scroll automático da sidebar após ação ───────────────
if st.session_state.get("_sb_scroll"):
    _target = st.session_state.pop("_sb_scroll")
    _kw = "Concluídos" if _target == "concluidos" else "processamento"
    st.markdown(f"""
    <script>
    (function(){{
        var _root = window;
        try{{ while(_root.parent && _root.parent !== _root) _root = _root.parent; }}catch(e){{}}
        var doc = _root.document;
        function scrollToTarget(){{
            var sb = doc.querySelector('[data-testid="stSidebar"] [data-testid="stVerticalBlock"]');
            if(!sb) return;
            var details = Array.from(sb.querySelectorAll('details,summary,[data-testid="stExpander"]'));
            var target = null;
            details.forEach(function(el){{
                if(el.innerText && el.innerText.includes("{_kw}")) target = el;
            }});
            if(target){{
                target.scrollIntoView({{behavior:'smooth', block:'center'}});
            }} else {{
                // fallback: rola para o final da sidebar
                sb.scrollTop = sb.scrollHeight;
            }}
        }}
        setTimeout(scrollToTarget, 350);
    }})();
    </script>
    """, unsafe_allow_html=True)

# =========================================================
# HEADER / NAV
# =========================================================

st.markdown("""
<style>
.nav-container {
    display: flex;
    justify-content: center;
    gap: 16px;
    margin-bottom: 1.2rem;
    margin-top: 0.2rem;
}
.nav-btn-active {
    background: linear-gradient(135deg, #1044b5, #0d2a6e) !important;
    color: #FFFFFF !important;
    box-shadow: 0 4px 14px rgba(16,68,181,0.35) !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 36px !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    cursor: default !important;
}
/* Botão nav_home — aparência ativa, sem cursor bloqueado */
[data-testid="element-container"]:has(button[kind="secondary"]) button[kind="secondary"] {
    cursor: pointer !important;
}
div[data-testid="stColumns"] > div:nth-child(2) button {
    background: linear-gradient(135deg, #1044b5, #0d2a6e) !important;
    color: #FFFFFF !important;
    border: none !important;
    cursor: default !important;
}
/* Campos de input — fundo branco */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-baseweb="input"] input {
    background-color: #FFFFFF !important;
    color: #000000 !important;
}
[data-testid="stDateInput"] > div,
[data-testid="stDateInput"] div[data-baseweb="input"] {
    background-color: #FFFFFF !important;
}
</style>
""", unsafe_allow_html=True)

_nav_cols = st.columns([1, 0.5, 0.5, 1]) if can("registrar") else st.columns([1, 0.7, 1])
with _nav_cols[1]:
    st.button("🔍 Central Shaken", key="nav_home", use_container_width=True, disabled=True)
if can("registrar"):
    with _nav_cols[2]:
        if st.button("📋 Registrar", key="nav_reg", use_container_width=True):
            st.switch_page("pages/1_Registros.py")


# =========================================================
# SEARCH
# =========================================================

if st.session_state.get("_limpar_busca"):
    st.session_state._limpar_busca = False
    st.session_state.busca = ""
    st.rerun()

col_busca, col_limpar = st.columns([6, 1])
with col_busca:
    q = st.text_input("Buscar", key="busca", label_visibility="collapsed", placeholder="🔍 Buscar por nome, chassi, veículo, contato...", autocomplete="off")
with col_limpar:
    if q:
        if st.button("✕", use_container_width=True, help="Limpar busca"):
            st.session_state._limpar_busca = True
            st.rerun()

if q:
    t = f"%{q}%"
    # Busca partes da placa separadas por hífen (ex: "品川-500" busca "品川" e "500")
    partes_placa = q.replace("-", " ").split()
    where_clauses = [
        "nome LIKE ?",
        "chassi LIKE ?",
        "veiculo LIKE ?",
        "placa LIKE ?",
        "contato LIKE ?",
        "chassi_completo LIKE ?",
        "fabricante LIKE ?",
        "modelo_katashiki LIKE ?",
        "shaken_vencimento LIKE ?",
        "data_registro LIKE ?"
    ]
    params = [t] * len(where_clauses)
    
    # Adiciona busca por partes da placa
    for parte in partes_placa:
        if len(parte) >= 2:
            where_clauses.append("placa LIKE ?")
            params.append(f"%{parte}%")
    
    df = listar_clientes(" OR ".join(where_clauses), tuple(params))
    df["veiculo"] = df["veiculo"].apply(traduzir_veiculo)
    st.caption(f"{len(df)} resultado(s) para **{q}**")
else:
    df = st.session_state.df.copy()

# Limpeza e formatação de datas
def formatar_data_exibicao(s):
    s = converter_data_japonesa(s)
    if s and re.match(r"\d{4}-\d{2}-\d{2}", str(s)):
        partes = str(s).split("-")
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return s

# Verifica se as colunas existem antes de acessá-las
if "shaken_vencimento" in df.columns:
    df["shaken_vencimento"] = df["shaken_vencimento"].apply(formatar_data_exibicao)
if "data_registro" in df.columns:
    df["data_registro"] = df["data_registro"].apply(formatar_data_exibicao)

# =========================================================
# BARRA DE AÇÃO (colapsável)
# =========================================================

st.divider()

if can("excluir") or can("desfazer"):
    if "acoes_expandido" not in st.session_state:
        st.session_state.acoes_expandido = False

    seta = "▶ Ações" if not st.session_state.acoes_expandido else "▼ Ações"
    if st.button(seta, key="toggle_acoes"):
        st.session_state.acoes_expandido = not st.session_state.acoes_expandido
        st.rerun()

if st.session_state.get("acoes_expandido") and (can("excluir") or can("desfazer")):
    col_action1, col_action2 = st.columns([1, 1])

    with col_action1:
        if can("excluir"):
            if st.button("🗑️ Modo Exclusão"):
                st.session_state.delete_mode = not st.session_state.delete_mode
                st.rerun()
            if st.session_state.delete_mode:
                st.session_state._excluir_btn = st.button("❌ Excluir Selecionados", type="primary")

    with col_action2:
        if can("desfazer"):
            if st.button("↩️ Desfazer Excluir Cliente"):
                if st.session_state.linhas_excluidas:
                    linhas_a_restaurar = st.session_state.linhas_excluidas.pop()
                    for linha in linhas_a_restaurar:
                        salvar_cliente(linha)
                    st.success(f"{len(linhas_a_restaurar)} cliente(s) restaurado(s)")
                    st.session_state.df = carregar_clientes()
                    st.rerun()
                else:
                    st.warning("Nenhuma exclusão para desfazer")

        if can("desfazer") and st.button("↩️ Desfazer Última Edição"):
            if st.session_state.ultima_edicao:
                info = st.session_state.ultima_edicao
                cliente_id = info["cliente_id"]
                col = info["coluna"]
                valor_antigo = info["valor_antigo"]
                mask = st.session_state.df["id"] == cliente_id
                if mask.any():
                    row_dict = st.session_state.df[mask].iloc[0].to_dict()
                    row_dict[col] = valor_antigo
                    atualizar_cliente(cliente_id, row_dict)
                    st.session_state.ultima_edicao = None
                    st.session_state.df = carregar_clientes()
                    st.success("Última edição desfeita")
                    st.rerun()
                else:
                    st.warning("Cliente não encontrado")
            else:
                st.warning("Nenhuma edição para desfazer")

# ── Aviso de exclusão recente ─────────────────────────────
if st.session_state._aviso_exclusao:
    _exc = st.session_state._aviso_exclusao
    _msgs_exc = "".join(
        f"<li><b>{r.get('nome','—')}</b> — chassi <b>{r.get('chassi','—')}</b></li>"
        for r in _exc
    )
    _ea1, _ea2 = st.columns([10, 1])
    with _ea1:
        st.markdown(f"""
        <div style='padding:9px 14px;background:#fff3cd;border-left:4px solid #dc7800;
                    border-radius:8px;font-size:0.85rem;color:#7a4500;'>
          <b>🗑️ {len(_exc)} registro(s) excluído(s):</b>
          <ul style='margin:4px 0 0 0;padding-left:18px;color:#7a4500'>{_msgs_exc}</ul>
        </div>""", unsafe_allow_html=True)
    with _ea2:
        if st.button("OK", key="ok_excluido"):
            st.session_state._aviso_exclusao = []
            st.rerun()

# ── Aviso: formato inválido (com opção de salvar mesmo assim) ──
if st.session_state.get("_aviso_formato"):
    _af = st.session_state._aviso_formato
    _af1, _af2, _af3 = st.columns([7, 1, 2]) if _af.get("pode_salvar") else st.columns([9, 1, 0.01])
    with _af1:
        st.markdown(f"""
        <div style='padding:9px 14px;background:#fff3cd;border-left:4px solid #dc7800;
                    border-radius:8px;font-size:0.85rem;color:#333333;'>
          <b>⚠️ {_af['msg']}</b>
        </div>""", unsafe_allow_html=True)
    with _af2:
        if st.button("OK", key="ok_fmt"):
            st.session_state._aviso_formato = None
            st.session_state._editor_v += 1
            if "editor" in st.session_state:
                del st.session_state["editor"]
            st.rerun()
    if _af.get("pode_salvar"):
        with _af3:
            st.markdown("""
            <style>
            div[data-testid="stButton"]:has(button[kind="secondary"]#salvar_fmt) button,
            div[data-testid="column"]:last-child div[data-testid="stButton"] button {
                background: #dc7800 !important;
                color: #fff !important;
                border: none !important;
                border-radius: 8px !important;
                font-weight: 600 !important;
                font-size: 0.82rem !important;
                padding: 6px 10px !important;
                white-space: normal !important;
                line-height: 1.3 !important;
                height: auto !important;
            }
            </style>
            """, unsafe_allow_html=True)
            if st.button("💾 Salvar\nmesmo assim", key="salvar_fmt"):
                _rd = _af["row_dict"]
                _rd[_af["col"]] = _af["val"]
                try:
                    atualizar_cliente(_af["cliente_id"], _rd)
                    st.session_state.df = carregar_clientes()
                    st.session_state._aviso_formato = None
                    if "editor" in st.session_state:
                        del st.session_state["editor"]
                    st.rerun()
                except Exception as _e:
                    st.session_state._aviso_formato = {
                        "msg": f"Não foi possível salvar: {_e}",
                        "pode_salvar": False,
                        "row_dict": _rd, "cliente_id": _af["cliente_id"],
                        "col": _af["col"], "val": _af["val"]
                    }
                    st.rerun()

# ── Aviso: data_conclusao inserida sem status concluído ──
if st.session_state.get("_aviso_data_conc"):
    _adc1, _adc2 = st.columns([10, 1])
    with _adc1:
        st.markdown("""
        <div style='padding:9px 14px;background:#fff3cd;border-left:4px solid #dc7800;
                    border-radius:8px;font-size:0.85rem;color:#7a4500;'>
          <b>⚠️ Data de conclusão inserida mas status não está como 🟢 Concluido.</b><br>
          <span style='font-size:0.8rem;'>Altere o status para Concluido primeiro para registrar a data de conclusão.</span>
        </div>""", unsafe_allow_html=True)
    with _adc2:
        if st.button("OK", key="ok_aviso_data_conc"):
            st.session_state._aviso_data_conc = False
            st.session_state._editor_v += 1
            if "editor" in st.session_state:
                del st.session_state["editor"]
            st.rerun()

# =========================================================
# AVISOS DO SISTEMA
# =========================================================

if "avisos_expandido" not in st.session_state:
    st.session_state.avisos_expandido = False

_av_tem = len(st.session_state.get("_avisos_lista", [])) > 0
_av_s = "▶ Avisos" if not st.session_state.avisos_expandido else "▼ Avisos"
if _av_tem:
    st.markdown("<style>button[data-testid='toggle_avisos']{background:#c0392b!important;}</style>", unsafe_allow_html=True)
if st.button(_av_s, key="toggle_avisos"):
    st.session_state.avisos_expandido = not st.session_state.avisos_expandido
    st.rerun()

if st.session_state.avisos_expandido:
    _df_av = st.session_state.df.copy()
    _avisos = []

    if not _df_av.empty:
        _hoje = date.today()

        # 1. Chassi duplicado
        _chassi_dup = _df_av[_df_av["chassi"].notna() & (_df_av["chassi"] != "")]
        _chassi_dup = _chassi_dup[_chassi_dup.duplicated(subset=["chassi"], keep=False)]
        for _, _row in _chassi_dup.iterrows():
            _avisos.append(("🔴", "Chassi duplicado",
                f"Chassi <b>{_row['chassi']}</b> aparece em mais de um registro (cliente: <b>{_row['nome']}</b>)"))

        # 2. Nome + veículo duplicado
        _nv = _df_av[_df_av["nome"].notna() & _df_av["veiculo"].notna() & (_df_av["nome"] != "") & (_df_av["veiculo"] != "")]
        _nv_dup = _nv[_nv.duplicated(subset=["nome", "veiculo"], keep=False)]
        _nv_seen = set()
        for _, _row in _nv_dup.iterrows():
            _key = (_row["nome"].strip().lower(), _row["veiculo"].strip().lower())
            if _key not in _nv_seen:
                _nv_seen.add(_key)
                _avisos.append(("🔴", "Nome + Veículo duplicado",
                    f"<b>{_row['nome']}</b> com veículo <b>{_row['veiculo']}</b> aparece em mais de um registro"))

        # 3. Contato duplicado (ignorando vazio)
        if "contato" in _df_av.columns:
            _cont = _df_av[_df_av["contato"].notna() & (_df_av["contato"].astype(str).str.strip() != "")]
            _cont_dup = _cont[_cont.duplicated(subset=["contato"], keep=False)]
            _cont_seen = set()
            for _, _row in _cont_dup.iterrows():
                _c = str(_row["contato"]).strip()
                if _c not in _cont_seen:
                    _cont_seen.add(_c)
                    _nomes = _cont[_cont["contato"].astype(str).str.strip() == _c]["nome"].tolist()
                    _avisos.append(("🟡", "Contato duplicado",
                        f"Contato <b>{_c}</b> está associado a: {', '.join(f'<b>{n}</b>' for n in _nomes)}"))

        # 4. Campos críticos vazios
        for _, _row in _df_av.iterrows():
            _missing = []
            if not str(_row.get("nome","") or "").strip(): _missing.append("Nome")
            if not str(_row.get("chassi","") or "").strip(): _missing.append("Chassi")
            if not str(_row.get("veiculo","") or "").strip(): _missing.append("Veículo")
            if _missing:
                _nome_ref = str(_row.get("nome","")) or f"ID {_row.get('id','?')}"
                _avisos.append(("🟠", "Campo obrigatório vazio",
                    f"<b>{_nome_ref}</b> — faltam: <b>{', '.join(_missing)}</b>"))


    # Salva no session_state para o botão saber a cor no próximo render
    st.session_state._avisos_lista = _avisos

    # Exibe avisos
    if not _avisos:
        st.markdown("<div style='padding:8px 12px;background:rgba(0,180,80,0.25);border-left:3px solid #00b450;border-radius:6px;font-size:0.85rem;color:#0a3a1a;font-weight:600'>✅ Nenhum aviso. Banco de dados íntegro.</div>", unsafe_allow_html=True)
    else:
        _cores  = {"🔴": "rgba(220,40,40,0.25)",  "🟡": "rgba(220,180,0,0.25)",  "🟠": "rgba(220,120,0,0.25)"}
        _bordas = {"🔴": "#dc2828", "🟡": "#dcb400", "🟠": "#dc7800"}
        _txt    = {"🔴": "#5a0000", "🟡": "#4a3800", "🟠": "#4a2000"}
        for _icone, _titulo, _detalhe in _avisos:
            st.markdown(f"""
            <div style='padding:7px 12px;margin-bottom:5px;background:{_cores.get(_icone,"rgba(100,100,100,0.15)")};
                        border-left:3px solid {_bordas.get(_icone,"#888")};border-radius:6px;font-size:0.82rem;
                        color:{_txt.get(_icone,"#222")};'>
              <b>{_icone} {_titulo}</b><br><span>{_detalhe}</span>
            </div>""", unsafe_allow_html=True)

st.divider()

# =========================================================
# TABLE + DELETE
# =========================================================

df = df if q else carregar_clientes()  # sempre carrega do banco para garantir dados atualizados
st.session_state.df = df  # mantém session_state sincronizado

# ── Ordenação global do df ────────────────────────────────
_SORT_LABEL = {
    "nome": "Nome", "chassi": "Chassi", "veiculo": "Veículo",
    "contato": "Contato", "shaken_vencimento": "Shaken",
    "data_registro": "Inspeção", "data_conclusao": "Conclusão", "status": "Status"
}
if st.session_state.sort_col and st.session_state.sort_dir > 0:
    _asc = st.session_state.sort_dir == 1
    _sc = st.session_state.sort_col
    if _sc in df.columns:
        df = df.sort_values(_sc, ascending=_asc, na_position="last").reset_index(drop=True)

# ── Paginação ─────────────────────────────────────────────
# (botões de ordenação só aparecem no modo Colunas — ver abaixo)
_total = len(df)
_n_pages = max(1, (_total + PAGE_SIZE - 1) // PAGE_SIZE)
# Reseta página se busca mudou ou df encolheu
if st.session_state.pagina_atual >= _n_pages:
    st.session_state.pagina_atual = max(0, _n_pages - 1)
_pag = st.session_state.pagina_atual
_start = _pag * PAGE_SIZE
_end = min(_start + PAGE_SIZE, _total)
df_page = df.iloc[_start:_end].reset_index(drop=True)

# Controles de navegação (só mostra se há mais de uma página)
if _n_pages > 1:
    _pc1, _pc2, _pc3 = st.columns([1, 3, 1])
    with _pc1:
        if st.button("◀", key="pag_prev", disabled=(_pag == 0)):
            st.session_state.pagina_atual -= 1
            st.rerun()
    with _pc2:
        st.markdown(
            f"<div style='text-align:center;font-size:0.82rem;color:rgba(255,255,255,0.6);padding-top:6px'>"
            f"registros {_start+1}–{_end} de {_total}</div>",
            unsafe_allow_html=True
        )
    with _pc3:
        if st.button("▶", key="pag_next", disabled=(_pag >= _n_pages - 1)):
            st.session_state.pagina_atual += 1
            st.rerun()

# Toggle modo de visualização
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "tabela"

_vm_cols = st.columns([1, 0.55, 0.55, 1])
with _vm_cols[1]:
    if st.button("📊 Tabela", key="btn_tabela", use_container_width=True,
                 disabled=(st.session_state.view_mode == "tabela")):
        st.session_state.view_mode = "tabela"
        st.rerun()
with _vm_cols[2]:
    if st.button("📱 Colunas", key="btn_colunas", use_container_width=True,
                 disabled=(st.session_state.view_mode == "colunas")):
        st.session_state.view_mode = "colunas"
        st.rerun()

_df_display = df_page if _n_pages > 1 else df  # usa página se há paginação

if not df.empty:
    ids = _df_display["id"].tolist()
    original = _df_display.copy()

    # Monta df_view para exibir na tabela
    _drop_cols = [c for c in ["id", "fabricante", "modelo_katashiki", "chassi_completo", "observacao", "criado_em", "atualizado_em"] if c in _df_display.columns]
    df_view = _df_display.drop(columns=_drop_cols).copy()
    df_view.insert(0, "observacao", _df_display["observacao"].fillna("").values)
    df_view.index = range(1, len(df_view) + 1)
    
    # Adiciona coluna de seleção WhatsApp (✅ quando tem número válido)
    if "contato" in df_view.columns:
        df_view["✅"] = _df_display["contato"].apply(lambda x: "�" if _get_wa_url(x) else "")

    # data_conclusao: inclui no df_view, marcando ciclos com prefixo especial
    if "data_conclusao" not in df_view.columns:
        df_view["data_conclusao"] = ""
    # Flag _conc_reaberto: True se cliente já foi concluído, reaberto, e concluído de novo
    # Detectamos pela presença de data_conclusao preenchida + status atual concluído já salvo antes
    # Usamos um marcador ★ na frente para indicar ciclo (exibimos em azul via column_config)
    # Rastreia ciclos: se data_conclusao já existia antes de ser reaberto
    # usamos session_state para guardar quais IDs já passaram por ciclo
    if "_conc_ciclos" not in st.session_state:
        st.session_state._conc_ciclos = set()

    def _fmt_conc(row):
        raw = row.get("data_conclusao") if "data_conclusao" in row.index else None
        # Descarta NaN, None, string vazia, "nan", "None"
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            return ""
        v = str(raw).strip()
        if not v or v.lower() in ("none", "nan"):
            return ""
        rid = row.get("id")
        if rid in st.session_state._conc_ciclos:
            return f"↺ {v}"
        return v
    df_view["data_conclusao"] = _df_display.apply(_fmt_conc, axis=1)

    # Normaliza status
    def normalizar_status(v):
        if v is None or (isinstance(v, float) and pd.isna(v)) or v == "":
            return "⚪"
        elif v in ("🔵 Em processamento", "🔵", "processamento"):
            return "🔵"
        elif v in ("🟢 Concluido", "🟢", "concluido"):
            return "🟢"
        return "⚪"

    if "status" in df_view.columns:
        status_col = df_view.pop("status").apply(normalizar_status)
        df_view.insert(0, "status", status_col)
    else:
        df_view.insert(0, "status", "⚪")

    # Calcula largura por conteúdo: ~8px por caractere + padding, mínimo 80px
    _COL_LABELS = {
        "chassi": "Chassi", "nome": "Nome", "veiculo": "Veículo",
        "contato": "Contato", "shaken_vencimento": "Shaken",
        "data_registro": "Inspeção", "data_conclusao": "Conclusão"
    }
    def _col_width(col, label):
        try:
            if col in df_view.columns and not df_view.empty:
                lengths = df_view[col].dropna().astype(str).str.len()
                max_data = int(lengths.max()) if not lengths.empty else 0
            else:
                max_data = 0
        except Exception:
            max_data = 0
        return max(50, int(max(max_data, len(label)) * 7) + 16)

    column_config = {
        "status": st.column_config.SelectboxColumn(
            "Status",
            options=["⚪", "🔵", "🟢"],
            required=True,
            default="⚪",
            width=_col_width("", "Status")
        ),
        "chassi": st.column_config.TextColumn("Chassi", width=_col_width("chassi", "Chassi")),
        "nome": st.column_config.TextColumn("Nome", width=_col_width("nome", "Nome")),
        "veiculo": st.column_config.TextColumn("Veículo", width=_col_width("veiculo", "Veículo")),
        "placa": st.column_config.TextColumn("Placa", width=_col_width("placa", "Placa")),
        "contato": st.column_config.TextColumn("Contato", width=_col_width("contato", "Contato")),
        "shaken_vencimento": st.column_config.TextColumn("Shaken", width=_col_width("shaken_vencimento", "Shaken")),
        "observacao": st.column_config.TextColumn("Obs", width=_col_width("", "Obs")),

    }

    # Modo exclusão: adiciona coluna checkbox
    if st.session_state.delete_mode:
        df_view.insert(0, "Apagar", [False] * len(df_view))
        column_config["Apagar"] = st.column_config.CheckboxColumn("🗑️", default=False)

    # Adiciona colunas de data condicionalmente se existirem
    if "data_registro" in df_view.columns:
        column_config["data_registro"] = st.column_config.TextColumn("Inspeção", width=_col_width("data_registro", "Inspeção"))
    if "data_conclusao" in df_view.columns:
        column_config["data_conclusao"] = st.column_config.TextColumn("Conclusão", width=_col_width("data_conclusao", "Conclusão"))
    
    # Adiciona coluna WhatsApp com URL clicável ao lado de contato
    if "contato" in df_view.columns:
        df_view["📱"] = df_view["contato"].apply(_get_wa_url)
        # Reordena: coloca 📱 logo após contato
        _cols = list(df_view.columns)
        if "📱" in _cols and "contato" in _cols:
            _cols.remove("📱")
            _idx = _cols.index("contato") + 1
            _cols.insert(_idx, "📱")
            df_view = df_view[_cols]
        column_config["📱"] = st.column_config.LinkColumn("💬", width=60, help="Abrir WhatsApp")

    # ── Modo Colunas (mobile) ─────────────────────────────
    if st.session_state.view_mode == "colunas":
        _COL_NAMES = {
            "status": "Status", "nome": "Nome", "veiculo": "Veículo",
            "placa": "Placa", "chassi": "Chassi", "contato": "Contato",
            "shaken_vencimento": "Shaken", "data_registro": "Registro",
            "data_conclusao": "Conclusão",
        }
        _cols_all = [c for c in df_view.columns if c in _COL_NAMES]

        # Seletor de colunas visíveis
        if "col_visible" not in st.session_state:
            st.session_state.col_visible = {c: c in ("status", "nome", "veiculo") for c in _cols_all}

        st.markdown("""
        <style>
        [data-testid^="stButton"] button[kind="primary"] {
            background: linear-gradient(135deg,#1044b5,#0d2a6e) !important;
            color: #fff !important; border: none !important;
        }
        </style>
        <div style='margin-bottom:6px;font-size:0.8rem;color:rgba(255,255,255,0.5);'>Exibir colunas:</div>
        """, unsafe_allow_html=True)
        _btn_cols = st.columns(len(_cols_all))
        for idx, c in enumerate(_cols_all):
            with _btn_cols[idx]:
                _active = st.session_state.col_visible.get(c, True)
                if st.button(_COL_NAMES[c], key=f"colbtn_{c}",
                             type="primary" if _active else "secondary",
                             use_container_width=True):
                    st.session_state.col_visible[c] = not _active
                    st.rerun()

        _cols_display = [c for c in _cols_all if st.session_state.col_visible.get(c, True)]

        if not _cols_display:
            st.info("Selecione ao menos uma coluna acima.")
        else:
            # Botões de ação (mesmo padrão da aba Tabela)
            if can("excluir") or can("desfazer"):
                if "acoes_col_exp" not in st.session_state:
                    st.session_state.acoes_col_exp = False
                _seta_col = "▶ Ações" if not st.session_state.acoes_col_exp else "▼ Ações"
                if st.button(_seta_col, key="toggle_acoes_col"):
                    st.session_state.acoes_col_exp = not st.session_state.acoes_col_exp
                    st.rerun()

            if st.session_state.get("acoes_col_exp") and (can("excluir") or can("desfazer")):
                _ca1, _ca2 = st.columns([1, 1])
                with _ca1:
                    if can("excluir"):
                        if st.button("🗑️ Modo Exclusão", key="col_del_mode"):
                            st.session_state.delete_mode = not st.session_state.delete_mode
                            st.rerun()
                        if st.session_state.delete_mode:
                            st.session_state._excluir_btn = st.button("❌ Excluir Selecionados", key="col_excluir_btn", type="primary")
                with _ca2:
                    if can("desfazer"):
                        if st.button("↩️ Desfazer Excluir Cliente", key="col_undo_del"):
                            if st.session_state.linhas_excluidas:
                                for linha in st.session_state.linhas_excluidas.pop():
                                    salvar_cliente(linha)
                                st.session_state.df = carregar_clientes()
                                st.rerun()
                            else:
                                st.warning("Nenhuma exclusão para desfazer")
                        if st.button("↩️ Desfazer Última Edição", key="col_undo_edit"):
                            if st.session_state.ultima_edicao:
                                info = st.session_state.ultima_edicao
                                mask = st.session_state.df["id"] == info["cliente_id"]
                                if mask.any():
                                    row_dict = st.session_state.df[mask].iloc[0].to_dict()
                                    row_dict[info["coluna"]] = info["valor_antigo"]
                                    atualizar_cliente(info["cliente_id"], row_dict)
                                    st.session_state.ultima_edicao = None
                                    st.session_state.df = carregar_clientes()
                                    st.success("Última edição desfeita")
                                    st.rerun()
                            else:
                                st.warning("Nenhuma edição para desfazer")

            # data_editor com só as colunas visíveis
            _cols_dados_col = [c for c in _cols_display if c not in ("status", "Apagar")]
            _disabled_col = [c for c in _cols_dados_col if c != "observacao"] if not can("editar") else False

            if st.session_state.delete_mode:
                _df_col = df_view[_cols_display].copy()
                _df_col.insert(0, "Apagar", [False] * len(_df_col))
                _col_cfg_col = {c: column_config[c] for c in _cols_display if c in column_config}
                _col_cfg_col["Apagar"] = st.column_config.CheckboxColumn("🗑️", default=False)
            else:
                _df_col = df_view[_cols_display].copy()
                _col_cfg_col = {c: column_config[c] for c in _cols_display if c in column_config}

            editor_col = st.data_editor(
                _df_col,
                use_container_width=True,
                num_rows="fixed",
                key=f"editor_col_{st.session_state._editor_v}",
                column_config=_col_cfg_col,
                disabled=_disabled_col,
            )

            # Salva edições — mesmas validações do modo Tabela
            if st.session_state.get("_aviso_formato") or st.session_state.get("_aviso_data_conc"):
                pass  # aviso ativo: pausa detecção para user ler o aviso
            else:
                _df_col_orig = df_view[_cols_display].copy()
                _edit_found = False
                for col in _cols_display:
                    if col == "Apagar" or _edit_found: break
                    _old_s = _df_col_orig[col].fillna("").astype(str)
                    _new_s = editor_col[col].fillna("").astype(str)
                    _diff_mask = _old_s != _new_s
                    if _diff_mask.any():
                        i = int(_diff_mask.idxmax())
                        v_old, v_new = _old_s.iloc[i], _new_s.iloc[i]
                        if col != "status":
                            st.session_state.ultima_edicao = {"cliente_id": ids[i], "coluna": col, "valor_antigo": v_old}
                        row_dict = _df_display.iloc[i].to_dict()
                        # busca row_dict completo do banco
                        _mask_full = st.session_state.df["id"] == ids[i]
                        if _mask_full.any():
                            row_dict = st.session_state.df[_mask_full].iloc[0].to_dict()
                        val_salvar = v_new
                        _rejeitar = False

                        def _rejeitar_aviso_col(msg, pode_salvar=False):
                            st.session_state._aviso_formato = {
                                "msg": msg, "pode_salvar": pode_salvar,
                                "row_dict": row_dict, "cliente_id": ids[i],
                                "col": col, "val": val_salvar
                            }

                        # ── Validação datas ──
                        if col in ("shaken_vencimento", "data_registro", "data_conclusao"):
                            _lbl = {"shaken_vencimento": "Shaken", "data_registro": "Inspeção", "data_conclusao": "Conclusão"}[col]
                            _v = val_salvar.strip()
                            if _v:
                                _raw = _v.replace("-","").replace("/","")
                                if len(_raw) == 8 and _raw.isdigit():
                                    val_salvar = f"{_raw[:4]}-{_raw[4:6]}-{_raw[6:8]}"
                                elif re.match(r"^\d{4}-\d{2}-\d{2}$", _v):
                                    pass
                                else:
                                    _rejeitar_aviso_col(f"<b>{_lbl}</b>: '{_v}' não é uma data válida. Use DD/MM/AAAA ou AAAAMMDD.")
                                    _rejeitar = True


                        # ── Chassi ──
                        if col == "chassi" and not _rejeitar:
                            _v = val_salvar.strip()
                            _ok_chassi = bool(re.match(r"^[A-Za-z0-9\-]{5,}$", _v)) if _v else True
                            if _v and not _ok_chassi:
                                _rejeitar_aviso_col(
                                    f"<b>Chassi</b>: '{_v}' está fora do padrão esperado (letras, números e hífen). Verifique o documento.",
                                    pode_salvar=True
                                )
                                _rejeitar = True

                        # ── Contato ──
                        if col == "contato" and not _rejeitar:
                            _v = val_salvar.strip()
                            _v_digits = re.sub(r"[\s\-]", "", _v)
                            _ok_cel  = bool(re.match(r"^0[789]0\d{8}$", _v_digits))
                            _ok_fixo = bool(re.match(r"^0\d{9,10}$", _v_digits))
                            if _v and not (_ok_cel or _ok_fixo):
                                _rejeitar_aviso_col(
                                    f"<b>Contato</b>: '{_v}' não segue o padrão japonês.<br>"
                                    "<span style='font-size:0.78rem'>Celular: 090-XXXX-XXXX | Fixo: 0X-XXXX-XXXX</span>",
                                    pode_salvar=True
                                )
                                _rejeitar = True

                        if _rejeitar:
                            st.rerun()
                            st.stop()

                        if col == "veiculo": val_salvar = traduzir_veiculo(val_salvar)
                        if col == "status":
                            val_salvar = {"🔵":"🔵 Em processamento","🟢":"🟢 Concluido","⚪":"⚪"}.get(val_salvar, val_salvar)
                            if val_salvar == "🟢 Concluido":
                                st.session_state._celebrar = True
                                # Preenche data_conclusao automaticamente
                                row_dict["data_conclusao"] = str(date.today())
                            elif val_salvar == "🔵 Em processamento":
                                _status_anterior = str(row_dict.get("status",""))
                                if "Concluido" in _status_anterior:
                                    if "_conc_ciclos" not in st.session_state:
                                        st.session_state._conc_ciclos = set()
                                    st.session_state._conc_ciclos.add(ids[i])
                        row_dict[col] = val_salvar
                        atualizar_cliente(ids[i], row_dict)
                        st.session_state.df = carregar_clientes()
                        st.session_state._editor_v += 1
                        _edit_found = True
                        st.rerun()

            # Processa exclusão
            if st.session_state.delete_mode and st.session_state.get("_excluir_btn"):
                linhas_para_excluir = []
                for i in range(len(editor_col)):
                    if i < len(df) and editor_col.iloc[i].get("Apagar", False):
                        linhas_para_excluir.append(df.iloc[i].to_dict())
                if linhas_para_excluir:
                    st.session_state.linhas_excluidas.append(linhas_para_excluir)
                for i in range(len(editor_col)):
                    if i < len(df) and editor_col.iloc[i].get("Apagar", False):
                        deletar_cliente(ids[i])
                st.session_state._excluir_btn = False
                st.session_state.df = carregar_clientes()
                st.rerun()

    else:
        # ── Modo Tabela (padrão) ─────────────────────────
        # Operador pode editar status; colunas de dados só admin/secretaria
        _cols_dados = [c for c in df_view.columns if c not in ("status", "Apagar")]
        _disabled = [c for c in _cols_dados if c != "observacao"] if not can("editar") else False

        # ── st.data_editor (edição principal) ────────────
        _order = ["observacao", "status"] + [c for c in df_view.columns if c not in ("status", "observacao", "data_conclusao")] + ["data_conclusao"]
        editor = st.data_editor(
            df_view,
            use_container_width=True,
            num_rows="fixed",
            key=f"editor_{st.session_state._editor_v}",
            column_config=column_config,
            disabled=_disabled,
            column_order=_order
        )


        # ── Botão WhatsApp para selecionados (ANTES do editor) ────
        _tem_wa_col = "📱" in df_view.columns
        
        # Botão aparece aqui em cima, antes do data_editor
        if _tem_wa_col:
            # Pega estado atual das seleções do df_view (não do editor ainda)
            _selecionados = [i for i in range(len(df_view)) if df_view.iloc[i].get("📱", False)]

        
        # ── Detecção de mudanças e salvamento ─────────────
        def _frames_iguais(a, b):
            if a.shape != b.shape:
                return False
            for col in a.columns:
                if col == "Apagar":
                    continue
                for i in range(len(a)):
                    v1 = a.iloc[i][col]; v2 = b.iloc[i][col]
                    if v1 is None or (isinstance(v1, float) and pd.isna(v1)): v1 = ""
                    if v2 is None or (isinstance(v2, float) and pd.isna(v2)): v2 = ""
                    if str(v1) != str(v2):
                        return False
            return True

        # Se há aviso ativo, não processa mudanças (evita loop enquanto user lê o aviso)
        if st.session_state.get("_aviso_formato") or st.session_state.get("_aviso_data_conc"):
            pass
        elif not _frames_iguais(df_view, editor):
            celula_mudou = False
            for col in df_view.columns:
                if col == "Apagar":
                    continue
                for i in range(len(df_view)):
                    v_old = df_view.iloc[i][col]; v_new = editor.iloc[i][col]
                    if v_old is None or (isinstance(v_old, float) and pd.isna(v_old)): v_old = ""
                    if v_new is None or (isinstance(v_new, float) and pd.isna(v_new)): v_new = ""
                    if str(v_old) != str(v_new):
                        if i >= len(ids):
                            continue  # evita erro out of range
                        if col != "status":
                            st.session_state.ultima_edicao = {"cliente_id": ids[i], "coluna": col, "valor_antigo": str(v_old)}
                        if col in st.session_state.df.columns:
                            row_dict = st.session_state.df.iloc[i].to_dict()
                            val_salvar = str(v_new)
                            _rejeitar = False  # se True: não salva, reseta editor

                            # ── Helper: rejeita e exibe aviso (sem salvar) ──
                            def _rejeitar_aviso(msg, pode_salvar=False):
                                st.session_state._aviso_formato = {
                                    "msg": msg, "pode_salvar": pode_salvar,
                                    "row_dict": row_dict, "cliente_id": ids[i],
                                    "col": col, "val": val_salvar
                                }
                                # Não reseta editor aqui — user precisa ver o valor errado
                                # O reset acontece ao clicar OK

                            # ── Normaliza/valida datas ──
                            if col in ("shaken_vencimento", "data_registro", "data_conclusao"):
                                _lbl = {"shaken_vencimento": "Shaken", "data_registro": "Inspeção", "data_conclusao": "Conclusão"}[col]
                                _v = val_salvar.strip()
                                if _v == "":
                                    pass  # vazio: aceita
                                else:
                                    _raw = _v.replace("-","").replace("/","")
                                    if len(_raw) == 8 and _raw.isdigit():
                                        val_salvar = f"{_raw[:4]}-{_raw[4:6]}-{_raw[6:8]}"
                                    elif re.match(r"^\d{4}-\d{2}-\d{2}$", _v):
                                        pass  # já no formato correto
                                    else:
                                        _rejeitar_aviso(f"<b>{_lbl}</b>: '{_v}' não é uma data válida. Use DD/MM/AAAA ou AAAAMMDD.")
                                        _rejeitar = True


                            # ── Chassi: padrão japonês (letras+hífen+números) ──
                            if col == "chassi" and not _rejeitar:
                                _v = val_salvar.strip()
                                # Padrão JP: ex. ZZT231-0123456, GD1-1234567, 3AA-1234567
                                # VIN internacional: 17 alfanuméricos
                                # Aceita: alfanum + hífen, mín 5 chars
                                _ok_chassi = bool(re.match(r"^[A-Za-z0-9\-]{5,}$", _v)) if _v else True
                                if _v and not _ok_chassi:
                                    _rejeitar_aviso(
                                        f"<b>Chassi</b>: '{_v}' está fora do padrão esperado (letras, números e hífen). Verifique o documento.",
                                        pode_salvar=True
                                    )
                                    _rejeitar = True

                            # ── Contato: padrão japonês ──
                            if col == "contato" and not _rejeitar:
                                _v = val_salvar.strip()
                                # Celular JP: 070/080/090-XXXX-XXXX
                                # Fixo JP: 0X-XXXX-XXXX ou 0XX-XXX-XXXX
                                # Aceita com ou sem hífens/espaços
                                _v_digits = re.sub(r"[\s\-]", "", _v)
                                _ok_cel = bool(re.match(r"^0[789]0\d{8}$", _v_digits))
                                _ok_fixo = bool(re.match(r"^0\d{9,10}$", _v_digits))
                                if _v and not (_ok_cel or _ok_fixo):
                                    _rejeitar_aviso(
                                        f"<b>Contato</b>: '{_v}' não segue o padrão japonês.<br>"
                                        "<span style='font-size:0.78rem'>Celular: 090-XXXX-XXXX | Fixo: 0X-XXXX-XXXX</span>",
                                        pode_salvar=True
                                    )
                                    _rejeitar = True

                            if _rejeitar:
                                st.rerun()
                                st.stop()

                            if col == "veiculo":
                                val_salvar = traduzir_veiculo(val_salvar)
                            if col == "status":
                                val_salvar = {"🔵":"🔵 Em processamento","🟢":"🟢 Concluido","⚪":"⚪"}.get(val_salvar, val_salvar)
                                if val_salvar == "🟢 Concluido":
                                    st.session_state._celebrar = True
                                elif val_salvar == "🔵 Em processamento":
                                    _status_anterior = str(row_dict.get("status",""))
                                    if "Concluido" in _status_anterior:
                                        if "_conc_ciclos" not in st.session_state:
                                            st.session_state._conc_ciclos = set()
                                        st.session_state._conc_ciclos.add(ids[i])
                            row_dict[col] = val_salvar
                            atualizar_cliente(ids[i], row_dict)
                        celula_mudou = True
                        break
                if celula_mudou:
                    break
            if celula_mudou:
                st.session_state.df = carregar_clientes()
                st.session_state._editor_v += 1  # força recriação do editor com dados atualizados
                st.rerun()

        if st.session_state.delete_mode and st.session_state.get("_excluir_btn"):
            linhas_para_excluir = []
            for i in range(len(editor)):
                if i < len(df) and editor.iloc[i].get("Apagar", False):
                    linhas_para_excluir.append(df.iloc[i].to_dict())
            if linhas_para_excluir:
                st.session_state.linhas_excluidas.append(linhas_para_excluir)
                st.session_state._aviso_exclusao = linhas_para_excluir
            for i in range(len(editor)):
                if i < len(df) and editor.iloc[i].get("Apagar", False):
                    deletar_cliente(ids[i])
            st.session_state._excluir_btn = False
            st.session_state.df = carregar_clientes()
            st.rerun()




else:
    st.info("Sem dados")
