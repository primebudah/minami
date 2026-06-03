# =========================================================
# IMPORTS
# =========================================================

import io
import base64
import json
import re

from PIL import Image
import streamlit as st

from japanese_calendar import (
    convert_era_year,
    extract_reiwa_year_regex,
    convert_japanese_date,
)

# =========================================================
# OPENAI CLIENT (com proteção de import)
# =========================================================

try:
    from openai import OpenAI
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"], timeout=45.0, max_retries=1)
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    client = None
    OPENAI_AVAILABLE = False
    st.warning("⚠️ OpenAI não disponível. OCR desativado.")

# =========================================================
# TRADUÇÃO DE VEÍCULOS JAPONÊS → INGLÊS
# =========================================================

_VEICULO_TRADUCAO = {
    # Fabricantes
    "トヨタ": "Toyota",
    "ホンダ": "Honda",
    "日産": "Nissan",
    "ニッサン": "Nissan",
    "スズキ": "Suzuki",
    "ダイハツ": "Daihatsu",
    "マツダ": "Mazda",
    "スバル": "Subaru",
    "三菱": "Mitsubishi",
    "ミツビシ": "Mitsubishi",
    "レクサス": "Lexus",
    "いすゞ": "Isuzu",
    # Modelos
    "アルファード": "Alphard",
    "ヴェルファイア": "Vellfire",
    "プリウス": "Prius",
    "カローラ": "Corolla",
    "クラウン": "Crown",
    "ランドクルーザー": "Land Cruiser",
    "ランクル": "Land Cruiser",
    "ハイエース": "Hiace",
    "ハイラックス": "Hilux",
    "ノア": "Noah",
    "ヴォクシー": "Voxy",
    "エスティマ": "Estima",
    "セルシオ": "Celsior",
    "レクサス": "Lexus",
    "ハリアー": "Harrier",
    "ラヴ４": "RAV4",
    "ＲＡＶ４": "RAV4",
    "RAV4": "RAV4",
    "ヤリス": "Yaris",
    "アクア": "Aqua",
    "シエンタ": "Sienta",
    "フィット": "Fit",
    "ステップワゴン": "Stepwgn",
    "フリード": "Freed",
    "オデッセイ": "Odyssey",
    "ヴェゼル": "Vezel",
    "ＣＲ－Ｖ": "CR-V",
    "CR-V": "CR-V",
    "ジムニー": "Jimny",
    "スイフト": "Swift",
    "エブリイ": "Every",
    "ワゴンＲ": "Wagon R",
    "スペーシア": "Spacia",
    "タント": "Tanto",
    "ムーヴ": "Move",
    "ミラ": "Mira",
    "コペン": "Copen",
    "ロッキー": "Rocky",
    "ライズ": "Raize",
    "ルーミー": "Roomy",
    "トール": "Tall",
    "キャスト": "Cast",
    "ウェイク": "Wake",
    "ムーヴキャンバス": "Move Canbus",
    "エクストレイル": "X-Trail",
    "セレナ": "Serena",
    "エルグランド": "Elgrand",
    "リーフ": "Leaf",
    "ノート": "Note",
    "マーチ": "March",
    "キューブ": "Cube",
    "デイズ": "Dayz",
    "ルークス": "Roox",
    "スカイライン": "Skyline",
    "フェアレディＺ": "Fairlady Z",
    "ＧＴ－Ｒ": "GT-R",
    "GT-R": "GT-R",
    "シルビア": "Silvia",
    "インプレッサ": "Impreza",
    "レガシィ": "Legacy",
    "フォレスター": "Forester",
    "アウトバック": "Outback",
    "ＢＲＺ": "BRZ",
    "ＷＲＸ": "WRX",
    "レヴォーグ": "Levorg",
    "デミオ": "Demio",
    "アクセラ": "Axela",
    "アテンザ": "Atenza",
    "ＣＸ－５": "CX-5",
    "ＣＸ－３": "CX-3",
    "ロードスター": "Roadster",
    "ＲＸ－７": "RX-7",
    "ＲＸ－８": "RX-8",
    "コルト": "Colt",
    "アウトランダー": "Outlander",
    "エクリプスクロス": "Eclipse Cross",
    "デリカ": "Delica",
    "パジェロ": "Pajero",
}

def traduzir_veiculo(nome: str) -> str:
    if not nome:
        return nome
    s = str(nome).strip()
    for jp, en in _VEICULO_TRADUCAO.items():
        if jp in s:
            s = s.replace(jp, en)
    return s

# =========================================================
# DATA CLEANER (ANTI JAPAN FORMAT)
# =========================================================

def calcular_ano_reiwa(numero_ano_era):
    """Regra de ferro: Reiwa 1 = 2019. Logo, Reiwa N = 2018 + N"""
    return convert_era_year("\u4ee4\u548c", numero_ano_era)

def extrair_ano_reiwa_regex(texto):
    """
    Usa regex for\u00e7ada para capturar o n\u00famero ap\u00f3s '\u4ee4\u548c' (Reiwa).
    Retorna o ano gregoriano calculado ou None se n\u00e3o encontrar.
    """
    return extract_reiwa_year_regex(texto)

def extrair_placa(texto):
    """Extrai placa japonesa do texto OCR."""
    if not texto:
        return ""
    
    texto = str(texto).upper().strip()
    
    # Padrões de placa japonesa (mais abrangentes)
    padroes = [
        r'([A-Z]{1,3}\s*-?\s*\d{2,4})',  # Alfanumérico: ABC-123, ABC123
        r'([A-Z]{1,3}\d{2,4})',  # Sem hífen: ABC123
        r'(\d{2,4}\s*-?\s*[A-Z]{1,3})',  # Número primeiro: 123-ABC
        r'([あ-んア-ン一-龯]{1,3}\s*-?\s*\d{2,4})',  # Kanji/hiragana + número
        r'(\d{2,4}\s*-?\s*[あ-んア-ン一-龯]{1,3})',  # Número + kanji/hiragana
        r'([あ-んア-ン一-龯]\d{1,4}[あ-んア-ン一-龯]?\s*-?\s*\d{2,4})',  # Prefeitura + número
    ]
    
    for padrao in padroes:
        match = re.search(padrao, texto)
        if match:
            placa = match.group(1).replace(" ", "").replace("-", "")
            if len(placa) >= 4 and len(placa) <= 8:
                return placa
    
    return ""

def converter_data_japonesa(s):
    """Converte datas Nengo para YYYY-MM-DD. Delegates to japanese_calendar module."""
    return convert_japanese_date(s)


# =========================================================
# OCR SERVICE
# =========================================================

def extrair_dados_do_documento(f):
    """
    Extrai dados de documento usando OpenAI GPT-4o-mini.
    Retorna dicionário com: nome, veiculo, chassi, contato, shaken_vencimento, data_registro
    """
    if not OPENAI_AVAILABLE:
        st.warning("⚠️ OpenAI não disponível. OCR desativado.")
        return {}
    
    img = Image.open(f).convert("RGB")
    img.thumbnail((1600, 1600))

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=78, optimize=True)

    b64 = base64.b64encode(buf.getvalue()).decode()

    r = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """
EXTRAÇÃO SHAKEN JAPÃO - CAMPOS ESPECÍFICOS OBRIGATÓRIOS

CAMPOS A EXTRAIR (APENAS ESTES):
1. fabricante: Campo "車名" (Nome do veículo/montadora - NISSAN, DAIHATSU, SUZUKI, etc)
2. modelo_katashiki: Campo "型式" (Código alfanumérico - ex: GD-S200P, EBD-DA64V)
3. chassi_completo: Campo "車台番号" (Número de série - ex: S200P-0037449)
4. placa: Campo "ナンバープレート" ou "車両番号" (Placa do veículo - CAPTURE TODOS OS CARACTERES INCLUINDO KANJI/HIRAGANA ANTES DOS NÚMEROS - ex: 品川-500, とちぎ-XXX, 浜松480な9924 - NÃO CORTE NENHUM CARACTERE)
5. shaken_vencimento: Campo "有効期間の満了する日" (Validade) - RETORNE NO FORMATO BRUTO JAPONÊS (ex: "令和8年5月10日")
6. data_registro: Campo "記録年月日" (Registro) - RETORNE NO FORMATO BRUTO JAPONÊS (ex: "令和8年3月31日")

REGRAS ESTRICTAS PARA DATAS:
- SEMPRE retorne datas no FORMATO BRUTO JAPONÊS (não converta para gregoriano)
- Exemplo: "令和8年5月10日" (não "2026-05-10")
- Exemplo: "令和9年2月" (não "2027-02-01")
- NÃO tente converter para ano gregoriano
- NÃO invente anos se não tiver certeza
- Se não conseguir ler a data claramente, retorne "NÃO IDENTIFICADO"

NÃO EXTRAIA NÚMEROS DE OUTROS CAMPOS:
- Use EXCLUSIVAMENTE o campo "有効期間の満了する日" para shaken_vencimento
- Para data_registro, use EXCLUSIVAMENTE o campo "記録年月日" (Registro)
- Não extraia números aleatórios do documento como se fossem datas
- Não confunda "有効期間の満了する日" com outras datas do documento

ATENÇÃO ESPECIAL PARA shaken_vencimento:
- Leia ATENTAMENTE o ano da era Reiwa no campo "有効期間の満了する日"
- Se o documento mostrar "令和9", retorne "令和9年" (não "令和8年")
- Se o documento mostrar "令和10", retorne "令和10年" (não "令和8年")
- Não confunda os anos da era Reiwa

OUTROS CAMPOS:
- contato pode ser vazio ""
- Todos os campos são obrigatórios exceto contato

RETORNE APENAS JSON com estes campos:
{
  "nome": "string",
  "contato": "string (pode ser vazio)",
  "shaken_vencimento": "FORMATO BRUTO JAPONÊS (ex: 令和8年5月10日)",
  "veiculo": "string (formato: {fabricante} {modelo_katashiki})",
  "placa": "string (Campo ナンバープレート - ex: 品川-500, とちぎ-XXX, ou formato alfanumérico)",
  "chassi": "string (formato: {chassi_completo})",
  "fabricante": "string (Campo 車名 - NISSAN, DAIHATSU, SUZUKI, etc)",
  "modelo_katashiki": "string (Campo 型式 - ex: GD-S200P, EBD-DA64V)",
  "chassi_completo": "string (Campo 車台番号 - ex: S200P-0037449)",
  "data_registro": "FORMATO BRUTO JAPONÊS (ex: 令和8年3月31日)"
}
"""
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extrair dados do documento Shaken"},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}"
                    }}
                ]
            }
        ],
        response_format={"type": "json_object"}
    )

    d = json.loads(r.choices[0].message.content)

    # Debug: mostra dados brutos do OCR
    print(f"[DEBUG] Dados brutos do OCR: {d}")

    # Validação e conversão rígida de datas (STRICT VALIDATION)
    for campo in ["shaken_vencimento", "data_registro"]:
        if d.get(campo):
            data_bruta = d[campo]
            print(f"[DEBUG] Validando campo {campo}: {data_bruta}")
            
            # Se for "NÃO IDENTIFICADO", marca para verificação manual
            if "NÃO IDENTIFICADO" in data_bruta or data_bruta == "NÃO IDENTIFICADO":
                d[campo] = "VERIFICAR"
                continue
            
            # Aplica conversão rígida usando função calcular_ano_reiwa
            data_convertida = converter_data_japonesa(data_bruta)
            
            # Se a conversão foi bem-sucedida, usa a data convertida
            if data_convertida and re.match(r"^\d{4}-\d{2}-\d{2}$", data_convertida):
                d[campo] = data_convertida
                print(f"[DEBUG] Data convertida com sucesso: {data_convertida}")
            else:
                d[campo] = "VERIFICAR"
                print(f"[DEBUG] Data não pôde ser convertida, marcando para verificação manual")

    # Formata veículo como {fabricante} {modelo_katashiki}
    fabricante = d.get("fabricante", "")
    modelo_katashiki = d.get("modelo_katashiki", "")
    if fabricante and modelo_katashiki:
        d["veiculo"] = f"{fabricante} {modelo_katashiki}"
    d["veiculo"] = traduzir_veiculo(d.get("veiculo", ""))
    
    # Formata chassi como {chassi_completo}
    chassi_completo = d.get("chassi_completo", "")
    if chassi_completo:
        d["chassi"] = chassi_completo
    
    # Placa já foi extraída pelo GPT, limpa espaços extras
    if "placa" not in d:
        d["placa"] = ""
    else:
        # Remove espaços extras e normaliza
        d["placa"] = str(d["placa"]).strip().replace("  ", " ").replace("  ", " ")

    print(f"[DEBUG] Dados finais: {d}")
    return d
