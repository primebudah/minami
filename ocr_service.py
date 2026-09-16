# =========================================================
# OCR SERVICE - CENTRAL SHAKEN
# Leitura de documentos japoneses 自動車検査証記録事項
# =========================================================

import io
import base64
import json
import re
from datetime import date

from PIL import Image
import streamlit as st


# =========================================================
# OPENAI
# =========================================================

try:
    from openai import OpenAI

    api_key = st.secrets.get("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY não encontrada nos secrets.")

    client = OpenAI(
        api_key=api_key,
        timeout=120.0,
        max_retries=2,
    )

    OPENAI_AVAILABLE = True

    print(f"[DEBUG] OPENAI_API_KEY carregada: {api_key[:8]}...")

except Exception as e:
    client = None
    OPENAI_AVAILABLE = False
    print(f"[DEBUG] OpenAI indisponível: {e}")


# =========================================================
# TRADUÇÃO DE VEÍCULOS
# =========================================================

_VEICULO_TRADUCAO = {
    "普通乗用": "Passeio",
    "小型乗用": "Passeio",
    "軽乗用": "Kei",
    "軽自動車": "Kei",
    "普通貨物": "Carga",
    "小型貨物": "Carga",
    "軽貨物": "Kei Carga",
    "乗用": "Passeio",
    "貨物": "Carga",
    "特殊": "Especial",
    "大型特殊": "Especial",
    "二輪": "Motocicleta",
    "側車付二輪": "Motocicleta",
    "原付": "Ciclomotor",
    "小型二輪": "Motocicleta",
    "普通二輪": "Motocicleta",
}


def traduzir_veiculo(valor):
    if valor is None:
        return ""

    texto = str(valor).strip()

    if not texto:
        return ""

    for japones, portugues in _VEICULO_TRADUCAO.items():
        if japones in texto:
            return portugues

    return texto


# =========================================================
# NORMALIZAÇÃO
# =========================================================

def _limpar_texto(valor):
    if valor is None:
        return ""

    return str(valor).strip()


def _campo_nao_identificado(valor):
    if valor is None:
        return True

    texto = str(valor).strip().upper()

    return texto in {
        "",
        "NÃO IDENTIFICADO",
        "NAO IDENTIFICADO",
        "NÃO IDENTIFICADA",
        "NAO IDENTIFICADA",
        "VERIFICAR",
        "UNKNOWN",
        "N/A",
        "NULL",
        "NONE",
    }


def _normalizar_nao_identificado(valor):
    if _campo_nao_identificado(valor):
        return "VERIFICAR"

    return str(valor).strip()


# =========================================================
# ANOS JAPONESES
# =========================================================

def calcular_ano_reiwa(numero_ano_era):
    return 2018 + int(numero_ano_era)


def calcular_ano_heisei(numero_ano_era):
    return 1988 + int(numero_ano_era)


def calcular_ano_showa(numero_ano_era):
    return 1925 + int(numero_ano_era)


def calcular_ano_taisho(numero_ano_era):
    return 1911 + int(numero_ano_era)


def calcular_ano_meiji(numero_ano_era):
    return 1867 + int(numero_ano_era)


def _converter_numeros_japoneses(texto):
    if not texto:
        return ""

    return str(texto).translate(
        str.maketrans(
            "０１２３４５６７８９",
            "0123456789",
        )
    )


def extrair_ano_reiwa_regex(texto):
    if not texto:
        return None

    texto = _converter_numeros_japoneses(texto).upper().strip()

    padroes = [
        r"令和\s*([0-9]+)\s*年?",
        r"\bR\s*([0-9]+)\s*年?",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto)

        if match:
            try:
                return calcular_ano_reiwa(int(match.group(1)))
            except Exception:
                return None

    return None


# =========================================================
# DATAS
# =========================================================

def _data_valida_iso(ano, mes, dia):
    try:
        ano = int(ano)
        mes = int(mes)
        dia = int(dia)

        date(ano, mes, dia)

        return 1900 <= ano <= 2100

    except Exception:
        return False


def _formatar_data_iso(ano, mes, dia):
    if not _data_valida_iso(ano, mes, dia):
        return None

    return f"{int(ano):04d}-{int(mes):02d}-{int(dia):02d}"


def converter_data_japonesa(valor):
    """
    Converte somente datas completas e válidas.
    Não completa mês ou dia ausente com 01.
    """

    if valor is None:
        return None

    texto = str(valor).strip()

    if not texto or _campo_nao_identificado(texto):
        return None

    texto = _converter_numeros_japoneses(texto)

    # YYYY-MM-DD
    match = re.fullmatch(
        r"(\d{4})-(\d{1,2})-(\d{1,2})",
        texto,
    )

    if match:
        return _formatar_data_iso(
            match.group(1),
            match.group(2),
            match.group(3),
        )

    # YYYY/MM/DD, YYYY.MM.DD
    match = re.fullmatch(
        r"(\d{4})[\/.\-](\d{1,2})[\/.\-](\d{1,2})",
        texto,
    )

    if match:
        return _formatar_data_iso(
            match.group(1),
            match.group(2),
            match.group(3),
        )

    # DD/MM/YYYY
    match = re.fullmatch(
        r"(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{4})",
        texto,
    )

    if match:
        return _formatar_data_iso(
            match.group(3),
            match.group(2),
            match.group(1),
        )

    # YYYY年MM月DD日
    match = re.fullmatch(
        r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?",
        texto,
    )

    if match:
        return _formatar_data_iso(
            match.group(1),
            match.group(2),
            match.group(3),
        )

    # Reiwa
    if "令和" in texto or re.search(r"\bR\s*\d+", texto, re.I):
        ano = extrair_ano_reiwa_regex(texto)

        if ano is None:
            return None

        mes_match = re.search(r"(\d{1,2})\s*月", texto)
        dia_match = re.search(r"(\d{1,2})\s*日", texto)

        if mes_match and dia_match:
            return _formatar_data_iso(
                ano,
                mes_match.group(1),
                dia_match.group(1),
            )

        match_alt = re.search(
            r"(?:令和|R)\s*\d+\s*[\/.\-]\s*(\d{1,2})"
            r"\s*[\/.\-]\s*(\d{1,2})",
            texto,
            re.I,
        )

        if match_alt:
            return _formatar_data_iso(
                ano,
                match_alt.group(1),
                match_alt.group(2),
            )

        return None

    # Heisei
    if "平成" in texto or re.search(r"\bH\s*\d+", texto, re.I):
        match_ano = re.search(
            r"(?:平成|H)\s*([0-9]+)",
            texto,
            re.I,
        )

        if not match_ano:
            return None

        ano = calcular_ano_heisei(match_ano.group(1))

        mes_match = re.search(r"(\d{1,2})\s*月", texto)
        dia_match = re.search(r"(\d{1,2})\s*日", texto)

        if not mes_match or not dia_match:
            return None

        return _formatar_data_iso(
            ano,
            mes_match.group(1),
            dia_match.group(1),
        )

    # Showa
    if "昭和" in texto or re.search(r"\bS\s*\d+", texto, re.I):
        match_ano = re.search(
            r"(?:昭和|S)\s*([0-9]+)",
            texto,
            re.I,
        )

        if not match_ano:
            return None

        ano = calcular_ano_showa(match_ano.group(1))

        mes_match = re.search(r"(\d{1,2})\s*月", texto)
        dia_match = re.search(r"(\d{1,2})\s*日", texto)

        if not mes_match or not dia_match:
            return None

        return _formatar_data_iso(
            ano,
            mes_match.group(1),
            dia_match.group(1),
        )

    # Taisho
    if "大正" in texto or re.search(r"\bT\s*\d+", texto, re.I):
        match_ano = re.search(
            r"(?:大正|T)\s*([0-9]+)",
            texto,
            re.I,
        )

        if not match_ano:
            return None

        ano = calcular_ano_taisho(match_ano.group(1))

        mes_match = re.search(r"(\d{1,2})\s*月", texto)
        dia_match = re.search(r"(\d{1,2})\s*日", texto)

        if not mes_match or not dia_match:
            return None

        return _formatar_data_iso(
            ano,
            mes_match.group(1),
            dia_match.group(1),
        )

    # Meiji
    if "明治" in texto or re.search(r"\bM\s*\d+", texto, re.I):
        match_ano = re.search(
            r"(?:明治|M)\s*([0-9]+)",
            texto,
            re.I,
        )

        if not match_ano:
            return None

        ano = calcular_ano_meiji(match_ano.group(1))

        mes_match = re.search(r"(\d{1,2})\s*月", texto)
        dia_match = re.search(r"(\d{1,2})\s*日", texto)

        if not mes_match or not dia_match:
            return None

        return _formatar_data_iso(
            ano,
            mes_match.group(1),
            dia_match.group(1),
        )

    # YYYYMMDD
    numeros = re.sub(r"\D", "", texto)

    if len(numeros) == 8:
        if 1900 <= int(numeros[:4]) <= 2100:
            resultado = _formatar_data_iso(
                numeros[:4],
                numeros[4:6],
                numeros[6:8],
            )

            if resultado:
                return resultado

    return None


def validar_data_convertida(valor):
    if not valor:
        return False

    match = re.fullmatch(
        r"(\d{4})-(\d{2})-(\d{2})",
        str(valor).strip(),
    )

    if not match:
        return False

    return _data_valida_iso(
        match.group(1),
        match.group(2),
        match.group(3),
    )


# =========================================================
# PLACAS
# =========================================================

def _normalizar_placa_texto(texto):
    if not texto:
        return ""

    texto = str(texto).strip()
    texto = texto.replace("　", " ")
    texto = texto.replace("—", "-")
    texto = texto.replace("－", "-")
    texto = texto.replace("–", "-")
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def validar_placa_japonesa(placa):
    if not placa:
        return False

    texto = _normalizar_placa_texto(placa)

    if texto.upper() in {
        "VERIFICAR",
        "NÃO IDENTIFICADO",
        "NAO IDENTIFICADO",
    }:
        return False

    regiao = r"[一-龯々ヶ]{1,8}"
    classificacao = r"\d{3}"
    kana = r"[あ-んア-ンゑヱ]"
    numero = r"(?:\d{1,4}|\d{1,2}-\d{2})"

    padroes = [
        rf"^{regiao}\s+{classificacao}\s+{kana}\s+{numero}$",
        rf"^{regiao}\s*{classificacao}\s*{kana}\s*{numero}$",
    ]

    return any(
        re.fullmatch(padrao, texto)
        for padrao in padroes
    )


def extrair_placa(texto):
    if not texto:
        return "VERIFICAR"

    texto = _normalizar_placa_texto(texto)

    padroes = [
        r"([一-龯々ヶ]{1,8}\s+\d{3}\s+[あ-んア-ンゑヱ]\s+(?:\d{1,2}-\d{2}|\d{1,4}))",
        r"([一-龯々ヶ]{1,8}\s*\d{3}\s*[あ-んア-ンゑヱ]\s*(?:\d{1,2}-\d{2}|\d{1,4}))",
    ]

    for padrao in padroes:
        match = re.search(padrao, texto)

        if match:
            placa = _normalizar_placa_texto(match.group(1))

            if validar_placa_japonesa(placa):
                return placa

    tokens = texto.split()

    for i in range(len(tokens) - 3):
        candidata = " ".join(tokens[i:i + 4])

        if validar_placa_japonesa(candidata):
            return candidata

    return "VERIFICAR"


def normalizar_placa_final(valor):
    if _campo_nao_identificado(valor):
        return "VERIFICAR"

    placa = _normalizar_placa_texto(valor)

    if validar_placa_japonesa(placa):
        return placa

    placa_extraida = extrair_placa(placa)

    if validar_placa_japonesa(placa_extraida):
        return placa_extraida

    return "VERIFICAR"


# =========================================================
# PROMPTS
# =========================================================

SYSTEM_PROMPT = r"""
Você é especialista em leitura de documentos japoneses de veículos.

O documento normalmente é:
自動車検査証記録事項

Retorne somente JSON válido com estas chaves:

{
  "nome": "",
  "contato": "",
  "fabricante": "",
  "modelo": "",
  "veiculo": "",
  "chassi": "",
  "chassi_completo": "",
  "placa": "",
  "shaken_vencimento": "",
  "data_registro": ""
}

REGRAS:

FABRICANTE:
Use 車名.

MODELO:
Use 型式.

CHASSI:
Use 車台番号.
Não confunda com número de tipo, modelo ou placa.

PLACA:
Use exclusivamente 自動車登録番号又は車両番号.

A placa precisa conter quatro partes:
REGIÃO + CLASSIFICAÇÃO + KANA + NÚMERO

Exemplo:
浜松 581 す 4338

Outro:
名古屋 330 あ 12-34

Não retorne somente números.
Não remova a estrutura.
Não confunda chassi com placa.
Se qualquer parte estiver ilegível, retorne VERIFICAR.

DATA DE REGISTRO:
Use somente 交付年月日.

Não use 初度検査年月.
Não use 有効期間の満了する日.

VENCIMENTO DO SHAKEN:
Use somente 有効期間の満了する日.

DATAS:
Retorne exatamente como aparecem no documento.
Não invente mês ou dia.
Não complete datas incompletas.
Se não estiver completamente legível, retorne VERIFICAR.

NOME:
Extraia o proprietário quando estiver visível.

CONTATO:
Extraia telefone somente se estiver visível.

Para qualquer campo ilegível, use VERIFICAR.
"""


RETRY_PROMPT = r"""
Faça uma segunda conferência visual deste documento japonês.

Retorne somente JSON válido:

{
  "placa": "",
  "shaken_vencimento": "",
  "data_registro": ""
}

PLACA:
Leia somente 自動車登録番号又は車両番号.
A placa precisa ter:
região em kanji + classificação de 3 dígitos + kana + número.

Exemplo:
浜松 581 す 4338

Se faltar uma parte, retorne VERIFICAR.

DATA DE REGISTRO:
Leia somente 交付年月日.

VENCIMENTO:
Leia somente 有効期間の満了する日.

Não use 初度検査年月.
Não invente datas.
Não complete mês ou dia.
Se houver dúvida, retorne VERIFICAR.
"""


# =========================================================
# IMAGEM
# =========================================================

def _preparar_imagem(f):
    if hasattr(f, "seek"):
        f.seek(0)

    imagem = Image.open(f)

    if imagem.mode != "RGB":
        imagem = imagem.convert("RGB")

    imagem.thumbnail((3000, 3000))

    buffer = io.BytesIO()

    imagem.save(
        buffer,
        format="JPEG",
        quality=90,
        optimize=True,
    )

    return base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")


# =========================================================
# OPENAI CALL
# =========================================================

def _chamar_openai(imagem_b64, prompt_sistema):
    if not OPENAI_AVAILABLE or client is None:
        raise RuntimeError(
            "OpenAI não está disponível. "
            "Verifique OPENAI_API_KEY."
        )

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        response_format={
            "type": "json_object"
        },
        messages=[
            {
                "role": "system",
                "content": prompt_sistema,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Leia cuidadosamente a imagem "
                            "e retorne somente o JSON solicitado."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                "data:image/jpeg;base64,"
                                + imagem_b64
                            ),
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
    )

    conteudo = resposta.choices[0].message.content

    if not conteudo:
        raise RuntimeError(
            "A OpenAI retornou resposta vazia."
        )

    return json.loads(conteudo)


# =========================================================
# NORMALIZAÇÃO DOS DADOS
# =========================================================

def _normalizar_dados_ocr(dados):
    if not isinstance(dados, dict):
        dados = {}

    resultado = {
        "nome": _normalizar_nao_identificado(
            dados.get("nome", "")
        ),
        "contato": _normalizar_nao_identificado(
            dados.get("contato", "")
        ),
        "fabricante": _normalizar_nao_identificado(
            dados.get("fabricante", "")
        ),
        "modelo": _normalizar_nao_identificado(
            dados.get("modelo", "")
        ),
        "veiculo": _normalizar_nao_identificado(
            dados.get("veiculo", "")
        ),
        "chassi": _normalizar_nao_identificado(
            dados.get("chassi", "")
        ),
        "chassi_completo": _normalizar_nao_identificado(
            dados.get("chassi_completo", "")
        ),
        "placa": _normalizar_nao_identificado(
            dados.get("placa", "")
        ),
        "shaken_vencimento": _normalizar_nao_identificado(
            dados.get("shaken_vencimento", "")
        ),
        "data_registro": _normalizar_nao_identificado(
            dados.get("data_registro", "")
        ),
    }

    if resultado["veiculo"] != "VERIFICAR":
        resultado["veiculo"] = traduzir_veiculo(
            resultado["veiculo"]
        )

    resultado["placa"] = normalizar_placa_final(
        resultado["placa"]
    )

    for campo in ["chassi", "chassi_completo"]:
        if resultado[campo] != "VERIFICAR":
            resultado[campo] = re.sub(
                r"\s+",
                "",
                str(resultado[campo]),
            ).upper()

    return resultado


def _converter_datas_dados(dados):
    for campo in [
        "shaken_vencimento",
        "data_registro",
    ]:
        valor = dados.get(campo)

        if _campo_nao_identificado(valor):
            dados[campo] = "VERIFICAR"
            continue

        convertido = converter_data_japonesa(valor)

        if convertido and validar_data_convertida(convertido):
            dados[campo] = convertido
        else:
            dados[campo] = "VERIFICAR"

    return dados


# =========================================================
# RETRY
# =========================================================

def _dados_precisam_retry(dados):
    if not dados:
        return True

    if not validar_placa_japonesa(
        dados.get("placa", "")
    ):
        return True

    if not validar_data_convertida(
        dados.get("shaken_vencimento", "")
    ):
        return True

    if not validar_data_convertida(
        dados.get("data_registro", "")
    ):
        return True

    try:
        ano_shaken = int(
            str(dados["shaken_vencimento"])[:4]
        )

        ano_registro = int(
            str(dados["data_registro"])[:4]
        )

        if abs(ano_shaken - ano_registro) > 5:
            return True

    except Exception:
        return True

    return False


def _mesclar_retry(original, retry):
    if not isinstance(retry, dict):
        return original

    placa_retry = normalizar_placa_final(
        retry.get("placa", "")
    )

    if validar_placa_japonesa(placa_retry):
        original["placa"] = placa_retry

    shaken_retry = converter_data_japonesa(
        retry.get("shaken_vencimento", "")
    )

    if shaken_retry and validar_data_convertida(
        shaken_retry
    ):
        original["shaken_vencimento"] = shaken_retry

    registro_retry = converter_data_japonesa(
        retry.get("data_registro", "")
    )

    if registro_retry and validar_data_convertida(
        registro_retry
    ):
        original["data_registro"] = registro_retry

    return original


# =========================================================
# FUNÇÃO PRINCIPAL
# =========================================================

def extrair_dados_do_documento(f):
    if f is None:
        return None

    try:
        print(
            f"[OCR] Iniciando processamento: "
            f"{getattr(f, 'name', 'arquivo')}"
        )

        imagem_b64 = _preparar_imagem(f)

        dados_brutos = _chamar_openai(
            imagem_b64,
            SYSTEM_PROMPT,
        )

        print(
            "[OCR DEBUG] Resposta original:",
            json.dumps(
                dados_brutos,
                ensure_ascii=False,
                indent=2,
            ),
        )

        dados = _normalizar_dados_ocr(
            dados_brutos
        )

        dados = _converter_datas_dados(
            dados
        )

        print(
            "[OCR DEBUG] Dados normalizados:",
            json.dumps(
                dados,
                ensure_ascii=False,
                indent=2,
            ),
        )

        if _dados_precisam_retry(dados):
            print(
                "[OCR] Dados incompletos ou suspeitos. "
                "Executando segunda leitura."
            )

            try:
                dados_retry = _chamar_openai(
                    imagem_b64,
                    RETRY_PROMPT,
                )

                print(
                    "[OCR DEBUG] Segunda resposta:",
                    json.dumps(
                        dados_retry,
                        ensure_ascii=False,
                        indent=2,
                    ),
                )

                dados = _mesclar_retry(
                    dados,
                    dados_retry,
                )

            except Exception as erro_retry:
                print(
                    f"[OCR] Erro na segunda leitura: "
                    f"{erro_retry}"
                )

        dados["placa"] = normalizar_placa_final(
            dados.get("placa", "")
        )

        for campo in [
            "shaken_vencimento",
            "data_registro",
        ]:
            if not validar_data_convertida(
                dados.get(campo)
            ):
                dados[campo] = "VERIFICAR"

        if _campo_nao_identificado(
            dados.get("veiculo", "")
        ):
            dados["veiculo"] = "VERIFICAR"
        else:
            dados["veiculo"] = traduzir_veiculo(
                dados["veiculo"]
            )

        for campo in [
            "nome",
            "contato",
            "fabricante",
            "modelo",
            "chassi",
            "chassi_completo",
        ]:
            if _campo_nao_identificado(
                dados.get(campo, "")
            ):
                dados[campo] = ""

        print(
            "[OCR FINAL]",
            json.dumps(
                dados,
                ensure_ascii=False,
                indent=2,
            ),
        )

        return dados

    except json.JSONDecodeError as e:
        print(
            f"[OCR ERRO] JSON inválido retornado pela OpenAI: {e}"
        )

    except Exception as e:
        print(
            f"[OCR ERRO GERAL] {type(e).__name__}: {e}"
        )

    return {
        "nome": "",
        "contato": "",
        "fabricante": "",
        "modelo": "",
        "veiculo": "",
        "chassi": "",
        "chassi_completo": "",
        "placa": "VERIFICAR",
        "shaken_vencimento": "VERIFICAR",
        "data_registro": "VERIFICAR",
    }


ocr_service_corrigido.py
Exibindo ocr_service_corrigido.py.

