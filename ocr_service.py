# =========================================================
# OCR SERVICE - CENTRAL SHAKEN
# Leitura de documentos japoneses 自動車検査証記録事項
# =========================================================

import io
import base64
import json
import re
import os
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


def traduzir_veiculo(valor):
    if not valor:
        return "VERIFICAR"

    texto = str(valor).strip()

    fabricantes = {
        "スズキ": "Suzuki",
        "トヨタ": "Toyota",
        "ホンダ": "Honda",
        "日産": "Nissan",
        "ニッサン": "Nissan",
        "ダイハツ": "Daihatsu",
        "マツダ": "Mazda",
        "三菱": "Mitsubishi",
        "スバル": "Subaru",
        "いすゞ": "Isuzu",
        "日野": "Hino",
    }

    return fabricantes.get(texto, texto)


def traduzir_modelo(texto):
    """Traduz códigos de modelo para nomes comerciais em português."""
    if not texto:
        return texto
    
    texto = str(texto).strip().upper()
    
    # Dicionário de modelos por fabricante (códigos mais comuns)
    modelos = {
        # Suzuki
        "CBA-HA36S": "Wagon R", "MH23S": "Wagon R", "MH21S": "Wagon R", "CBA-MH21S": "Wagon R", "CBA-MH23S": "Wagon R",
        "CBA-HA25S": "Alto", "HA25S": "Alto", "MA15S": "Alto", "CBA-MA15S": "Alto", "AB15S": "Alto", "CBA-AB15S": "Alto",
        "JB23W": "Jimny", "JB33W": "Jimny", "JB43W": "Jimny", "JB64W": "Jimny", "CBA-JB64W": "Jimny",
        "GH6S": "Spacia", "CBA-GH6S": "Spacia", "GH7S": "Spacia Custom", "CBA-GH7S": "Spacia Custom",
        "MR90S": "Solio", "CBA-MR90S": "Solio", "MR92S": "Solio Bandit", "CBA-MR92S": "Solio Bandit",
        "HE33S": "Hustler", "CBA-HE33S": "Hustler", "HE21S": "Hustler", "CBA-HE21S": "Hustler",
        "XG32S": "Xbee", "CBA-XG32S": "Xbee", "WB32S": "Wagon R Smile", "CBA-WB32S": "Wagon R Smile",
        
        # Toyota
        "NHP130": "Prius", "ZVW30": "Prius", "ZVW50": "Prius", "CBA-NHP130": "Prius", "CBA-ZVW30": "Prius", "CBA-ZVW50": "Prius",
        "MNH10": "Aqua", "MNH20": "Aqua", "MNH30": "Aqua", "CBA-MNH10": "Aqua", "CBA-MNH20": "Aqua", "CBA-MNH30": "Aqua",
        "NCP100": "Vitz", "NCP120": "Vitz", "NCP130": "Vitz", "NCP150": "Vitz", "CBA-NCP100": "Vitz", "CBA-NCP130": "Vitz",
        "KSP130": "Porte", "KSP210": "Porte", "NSP130": "Porte", "NSP210": "Porte", "DBA-KSP210": "Porte", "DBA-NSP210": "Porte",
        "TRH200": "Hiace", "TRH290": "Hiace", "KDH200": "Hiace", "KDH290": "Hiace", "CBA-TRH200": "Hiace", "CBA-KDH200": "Hiace",
        "NZE141": "Corolla", "NZE144": "Corolla", "ZRE142": "Corolla", "CBA-NZE141": "Corolla",
        "AZP60": "Crown", "AZP61": "Crown", "CBA-AZP60": "Crown",
        "ACA31": "Harrier", "ACA36": "Harrier", "CBA-ACA31": "Harrier",
        "AAV60": "RAV4", "AAV64": "RAV4", "CBA-AAV60": "RAV4",
        "MCA36": "Sienta", "CBA-MCA36": "Sienta",
        "NMP210": "Noah", "NMP220": "Noah", "CBA-NMP210": "Noah",
        "NRP210": "Voxy", "NRP220": "Voxy", "CBA-NRP210": "Voxy",
        
        # Honda
        "DBA-JF1": "N-BOX", "JF1": "N-BOX", "JF2": "N-BOX", "DBA-JF2": "N-BOX",
        "DBA-JF3": "N-BOX Custom", "JF3": "N-BOX Custom", "DBA-JF4": "N-BOX Custom", "JF4": "N-BOX Custom",
        "DBA-GK5": "Fit", "GK5": "Fit", "GK3": "Fit", "DBA-GK3": "Fit",
        "DBA-GP5": "Fit", "GP5": "Fit", "GP3": "Fit", "DBA-GP3": "Fit",
        "DBA-GB5": "Fit", "GB5": "Fit", "GB3": "Fit", "DBA-GB3": "Fit",
        "DBA-GR9": "Freed", "GR9": "Freed", "DBA-GB7": "Freed", "GB7": "Freed",
        "DBA-GG3": "Stepwgn", "GG3": "Stepwgn", "DBA-GG4": "Stepwgn", "GG4": "Stepwgn",
        "DBA-RU1": "Vezel", "RU1": "Vezel", "DBA-RU2": "Vezel", "RU2": "Vezel",
        
        # Nissan
        "DBA-C26": "Serena", "C26": "Serena", "DBA-C25": "Serena", "C25": "Serena", "DBA-C27": "Serena", "C27": "Serena",
        "DBA-NV200": "NV200", "NV200": "NV200",
        "DBA-E25": "Note", "E25": "Note", "DBA-E12": "Note", "E12": "Note",
        "DBA-HG35": "Dayz", "HG35": "Dayz", "DBA-HG36": "Dayz", "HG36": "Dayz",
        
        # Daihatsu
        "DBA-L575S": "Tanto", "L575S": "Tanto", "DBA-L585S": "Tanto", "L585S": "Tanto",
        "DBA-L590S": "Tanto Custom", "L590S": "Tanto Custom", "DBA-L600S": "Tanto Custom", "L600S": "Tanto Custom",
        "DBA-LA600S": "Tanto Custom", "LA600S": "Tanto Custom", "DBA-LA590S": "Tanto Custom", "LA590S": "Tanto Custom",
        "DBA-LA585S": "Tanto", "LA585S": "Tanto", "DBA-LA575S": "Tanto", "LA575S": "Tanto",
        "DBA-M400S": "Move", "M400S": "Move", "DBA-M401S": "Move", "M401S": "Move",
        "DBA-L700S": "Move", "L700S": "Move", "DBA-L710S": "Move", "L710S": "Move",
        "DBA-L750S": "Move Conte", "L750S": "Move Conte", "DBA-L760S": "Move Conte", "L760S": "Move Conte",
        "ABA-S321G": "Tanto", "S321G": "Tanto", "ABA-S321E": "Tanto", "S321E": "Tanto", "ABA-S321F": "Tanto", "S321F": "Tanto",
        "DBA-LB800S": "Copen", "LB800S": "Copen", "DBA-LB900S": "Copen", "LB900S": "Copen",
        "S200P": "Sonica", "CBA-S200P": "Sonica",
        
        # Mazda
        "DBA-DK5AW": "Demio", "DK5AW": "Demio", "DBA-DK3AW": "Demio", "DK3AW": "Demio",
        "DBA-DK5FW": "Demio", "DK5FW": "Demio", "DBA-DK3FW": "Demio", "DK3FW": "Demio",
        "DBA-CB5AW": "Axela", "CB5AW": "Axela", "DBA-CB3AW": "Axela", "CB3AW": "Axela",
        "DBA-CB5FW": "Axela", "CB5FW": "Axela", "DBA-CB3FW": "Axela", "CB3FW": "Axela",
        "DBA-CY5AW": "CX-5", "CY5AW": "CX-5", "DBA-CY5FW": "CX-5", "CY5FW": "CX-5",
        "DBA-KF5AW": "CX-3", "KF5AW": "CX-3", "DBA-KF5FW": "CX-3", "KF5FW": "CX-3",
        "DBA-KE5AW": "CX-30", "KE5AW": "CX-30", "DBA-KE5FW": "CX-30", "KE5FW": "CX-30",
        "DBA-CM5AW": "CX-8", "CM5AW": "CX-8", "DBA-CM5FW": "CX-8", "CM5FW": "CX-8",
        "DBA-CA5AW": "Mazda2", "CA5AW": "Mazda2", "DBA-CA5FW": "Mazda2", "CA5FW": "Mazda2",
        "DBA-CC5AW": "Mazda3", "CC5AW": "Mazda3", "DBA-CC5FW": "Mazda3", "CC5FW": "Mazda3",
        "DBA-CG5AW": "Mazda6", "CG5AW": "Mazda6", "DBA-CG5FW": "Mazda6", "CG5FW": "Mazda6",
        "DBA-CH5AW": "Mazda CX-9", "CH5AW": "Mazda CX-9", "DBA-CH5FW": "Mazda CX-9", "CH5FW": "Mazda CX-9",
        
        # Mitsubishi
        "DBA-A000W": "eK", "A000W": "eK", "DBA-A001W": "eK", "A001W": "eK",
        "DBA-A002W": "eK", "A002W": "eK", "DBA-A003W": "eK", "A003W": "eK",
        "DBA-A100W": "eK", "A100W": "eK", "DBA-A101W": "eK", "A101W": "eK",
        "DBA-A102W": "eK", "A102W": "eK", "DBA-A103W": "eK", "A103W": "eK",
        
        # Subaru
        "DBA-A1A": "Stella", "A1A": "Stella", "DBA-A2A": "Stella", "A2A": "Stella",
        "DBA-A3A": "Stella", "A3A": "Stella", "DBA-A4A": "Stella", "A4A": "Stella",
        "DBA-A5A": "Stella", "A5A": "Stella",
    }
    
    return modelos.get(texto, texto)


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
                numero = int(match.group(1))

                # Reiwa válida: anos 1 em diante
                if numero < 1:
                    return None

                return calcular_ano_reiwa(numero)

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

    match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", texto)
    if match:
        resultado = _formatar_data_iso(
            match.group(1), match.group(2), match.group(3)
        )
        return resultado

    match = re.fullmatch(
        r"(\d{4})[\/.\-](\d{1,2})[\/.\-](\d{1,2})",
        texto,
    )
    if match:
        resultado = _formatar_data_iso(
            match.group(1), match.group(2), match.group(3)
        )
        return resultado

    match = re.fullmatch(
        r"(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{4})",
        texto,
    )
    if match:
        resultado = _formatar_data_iso(
            match.group(3), match.group(2), match.group(1)
        )
        return resultado

    # REMOVIDO: Este match aceita "2013年6月2日" sem verificar era
    # Deve verificar eras japonesas primeiro antes de aceitar formato com "年"
    # match = re.fullmatch(
    #     r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日?",
    #     texto,
    # )
    # if match:
    #     resultado = _formatar_data_iso(
    #         match.group(1), match.group(2), match.group(3)
    #     )
    #     return resultado

    if "令和" in texto or re.search(r"\bR\s*\d+", texto, re.I):
        ano = extrair_ano_reiwa_regex(texto)
        if ano is None:
            return None

        mes_match = re.search(r"(\d{1,2})\s*月", texto)
        dia_match = re.search(r"(\d{1,2})\s*日", texto)

        if mes_match and dia_match:
            resultado = _formatar_data_iso(
                ano, mes_match.group(1), dia_match.group(1)
            )
            return resultado

        match_alt = re.search(
            r"(?:令和|R)\s*\d+\s*[\/.\-]\s*(\d{1,2})"
            r"\s*[\/.\-]\s*(\d{1,2})",
            texto,
            re.I,
        )
        if match_alt:
            resultado = _formatar_data_iso(
                ano, match_alt.group(1), match_alt.group(2)
            )
            return resultado

        return None

    for era, regex, conversor in [
        ("平成", r"(?:平成|H)\s*([0-9]+)", calcular_ano_heisei),
        ("昭和", r"(?:昭和|S)\s*([0-9]+)", calcular_ano_showa),
        ("大正", r"(?:大正|T)\s*([0-9]+)", calcular_ano_taisho),
        ("明治", r"(?:明治|M)\s*([0-9]+)", calcular_ano_meiji),
    ]:
        if era in texto or re.search(regex, texto, re.I):
            match_ano = re.search(regex, texto, re.I)
            if not match_ano:
                return None

            ano = conversor(match_ano.group(1))
            mes_match = re.search(r"(\d{1,2})\s*月", texto)
            dia_match = re.search(r"(\d{1,2})\s*日", texto)

            if not mes_match or not dia_match:
                return None

            resultado = _formatar_data_iso(
                ano, mes_match.group(1), dia_match.group(1)
            )
            return resultado

    numeros = re.sub(r"\D", "", texto)
    if len(numeros) == 8 and 1900 <= int(numeros[:4]) <= 2100:
        resultado = _formatar_data_iso(
            numeros[:4], numeros[4:6], numeros[6:8]
        )
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
        match.group(1), match.group(2), match.group(3)
    )


# =========================================================
# PROMPTS
# =========================================================

SYSTEM_PROMPT = r"""
Você é especialista em leitura de documentos japoneses de veículos.

O documento normalmente é:
自動車検査証記録事項

Analise visualmente a foto inteira do documento e retorne somente JSON válido
com exatamente estas chaves:

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

=========================================================
IDENTIFICAÇÃO DO VEÍCULO
=========================================================

FABRICANTE:
Extraia o fabricante/marca real do veículo usando principalmente o campo:
車名

Exemplos de fabricantes:
スズキ = Suzuki
トヨタ = Toyota
ホンダ = Honda
日産 / ニッサン = Nissan
ダイハツ = Daihatsu
マツダ = Mazda
三菱 = Mitsubishi
スバル = Subaru

Não confunda fabricante com categoria do veículo.

MODELO:
Extraia o modelo real do veículo quando estiver claramente visível
na foto do documento.

Procure o nome/modelo comercial do carro no documento.
Exemplos:
Wagon R
Alto
Jimny
Prius
Aqua
N-BOX
Tanto
Move
Serena
Hiace

Não invente o modelo.
Se o modelo comercial não estiver claramente legível, use VERIFICAR.

VEICULO:
Este campo deve conter o FABRICANTE + MODELO REAL do veículo,
quando ambos estiverem identificáveis na foto.

Exemplos corretos:
Suzuki Wagon R
Toyota Prius
Honda N-BOX
Daihatsu Tanto
Nissan Serena
Suzuki Alto

Se somente o fabricante estiver claramente identificado:
Suzuki
Toyota
Honda
Nissan

NUNCA preencher "veiculo" com categorias ou classificações como:
Kei
Carga
Passageiro
Caminhão
Ônibus
Veículo leve
軽
軽自動車
貨物
乗用
乗合

Essas palavras são categorias/classificações do veículo e NÃO são
o fabricante nem o modelo.

O campo 車名 normalmente identifica o fabricante.
O modelo deve ser extraído somente quando estiver realmente visível
ou claramente identificável na foto.

=========================================================
CHASSI
=========================================================

CHASSI:
Use exclusivamente o campo:
車台番号

Não confunda com:
- 型式
- número de tipo
- número de classificação
- placa
- número de registro

CHASSI_COMPLETO:
Retorne o número completo do chassi exatamente como aparece.

=========================================================
PLACA — LEITURA CRÍTICA DOS KANJIS
=========================================================

PLACA:
Use EXCLUSIVAMENTE o campo:
自動車登録番号又は車両番号

A estrutura OBRIGATÓRIA é:
[REGIÃO EM KANJI] [CLASSIFICAÇÃO 3 DÍGITOS] [KANA] [NÚMERO]

=========================================================
REGRA CRÍTICA: NÃO SUBSTITUIR KANJIS
=========================================================

Os dois primeiros kanjis da região DEVEM ser lidos EXATAMENTE
como aparecem na fotografia.

É PROIBIDO:
- Substituir kanjis por cidades conhecidas
- Trocar 豊橋 por 浜松
- Trocar 豊 por 浜
- Trocar 橋 por 松
- Trocar 名古屋 por 浜松
- Trocar 豊田 por 浜松
- Presumir a cidade com base em probabilidade

Se os kanjis não estiverem 100% claros:
retorne VERIFICAR para a placa inteira

=========================================================
KANJIS QUE FREQUENTEMENTE SÃO CONFUNDIDOS
=========================================================

豊 (yutaka) ≠ 浜 (hama)
橋 (hashi) ≠ 松 (matsu)
名 (na) ≠ 浜 (hama)
古 (furui) ≠ 松 (matsu)
屋 (ya) ≠ 浜 (hama)

Leia CADA kanji individualmente, observando:
- Número de traços
- Posição dos traços
- Forma exata do caractere

=========================================================
EXEMPLOS DE PLACAS CORRETAS
=========================================================

Se a foto mostrar claramente:
豊橋 581 り 6940
→ Retorne: 豊橋 581 り 6940

Se a foto mostrar claramente:
浜松 581 す 4338
→ Retorne: 浜松 581 す 4338

Se a foto mostrar claramente:
名古屋 330 あ 1234
→ Retorne: 名古屋 330 あ 1234

NUNCA retorne:
浜松 581 り 6940 (kanji da região incorreto)
豊橋 581 す 4338 (kanji da região incorreto)

=========================================================
REGRAS FINAIS
=========================================================

- Não retorne somente os números
- Não remova os kanjis da região
- Não traduza a cidade para português
- Não corrija a placa baseado em suposição
- Se houver DÚVIDA sobre qualquer kanji: retorne VERIFICAR

=========================================================
VENCIMENTO DO SHAKEN - PRIORIDADE MÁXIMA
=========================================================

VENCIMENTO DO SHAKEN:
Use EXCLUSIVAMENTE o campo:
有効期間の満了する日

INSTRUÇÃO CRÍTICA - LEIA COM ATENÇÃO:
1. O rótulo 有効期間の満了する日 significa "Data de Expiração do Shaken"
2. NUNCA confunda com outros rótulos de data
3. shaken_vencimento DEVE vir de 有効期間の満了する日
4. shaken_vencimento NUNCA deve vir de 初度検査年月
5. shaken_vencimento NUNCA deve vir de 交付年月日

PROCEDIMENTO OBRIGATÓRIO:
1. Procure VISUALMENTE o rótulo 有効期間の満了する日 no documento
2. Leia SOMENTE a data que está IMEDIATAMENTE ao lado/abaixo de 有効期間の満了する日
3. IGNORE completamente 初度検査年月 e 交付年月日 para o campo shaken_vencimento
4. Se 有効期間の満了する日 não estiver visível ou legível, retorne VERIFICAR

IMPORTANTE - POSIÇÃO ESPACIAL:
- Cada rótulo tem sua própria data ao lado
- NÃO use datas de outras partes do documento
- A data de 有効期間の満了する日 está IMEDIATAMENTE ao lado do rótulo 有効期間の満了する日
- NÃO troque as datas entre os rótulos

EXEMPLO CRÍTICO:
Se o documento mostrar:
交付年月日 = 令和6年3月19日 (data_registro)
有効期間の満了する日 = 令和8年3月18日 (shaken_vencimento)
初度検査年月 = 平成28年7月27日 (NÃO USAR)

Resultado OBRIGATÓRIO:
data_registro = 令和6年3月19日
shaken_vencimento = 令和8年3月18日

NUNCA retorne:
shaken_vencimento = 平成28年7月27日 (ERRADO - é 初度検査年月)
shaken_vencimento = 令和6年3月19日 (ERRADO - é 交付年月日)

=========================================================
DATA DE REGISTRO
=========================================================

DATA DE REGISTRO:
Use EXCLUSIVAMENTE o campo:
交付年月日

INSTRUÇÃO CRÍTICA - LEIA COM ATENÇÃO:
1. O rótulo 交付年月日 significa "Data de Entrega/Registro"
2. O rótulo 初度検査年月 significa "Data da Primeira Inspeção"
3. NUNCA confunda estes dois rótulos
4. data_registro DEVE vir de 交付年月日
5. data_registro NUNCA deve vir de 初度検査年月

PROCEDIMENTO OBRIGATÓRIO:
1. Procure VISUALMENTE o rótulo 交付年月日 no documento
2. Leia SOMENTE a data que está IMEDIATAMENTE ao lado/abaixo de 交付年月日
3. IGNORE completamente 初度検査年月 para o campo data_registro
4. Se 交付年月日 não estiver visível ou legível, retorne VERIFICAR

IMPORTANTE - POSIÇÃO ESPACIAL (ESQUERDA/DIREITA):
- No documento, há múltiplas datas dispostas horizontalmente
- data_registro deve usar a data da ESQUERDA (ano mais recente)
- shaken_vencimento deve usar a data da DIREITA (ano mais recente)
- A data do MEIO (ano antigo como 平成28年) NUNCA deve ser usada
- NÃO troque as datas entre as posições

EXEMPLO CRÍTICO:
Se o documento mostrar 3 datas horizontalmente:
Data ESQUERDA = 令和6年3月19日 (data_registro)
Data MEIO = 平成28年7月27日 (NÃO USAR)
Data DIREITA = 令和8年3月18日 (shaken_vencimento)

Resultado OBRIGATÓRIO:
data_registro = 令和6年3月19日 (data da ESQUERDA)
shaken_vencimento = 令和8年3月18日 (data da DIREITA)

NUNCA retorne:
data_registro = 平成28年7月27日 (ERRADO - é data do MEIO)
shaken_vencimento = 平成28年7月27日 (ERRADO - é data do MEIO)

=========================================================
CONVERSÃO DE ERAS JAPONESAS
=========================================================

É CRÍTICO identificar corretamente a ERA japonesa:

令和 (Reiwa): Começou em 2019
令和元年 = 2019
令和8年 = 2026
令和10年 = 2028

平成 (Heisei): 1988 até 2019
平成元年 = 1989
平成8年 = 1996
平成10年 = 1998
平成25年 = 2013

昭和 (Showa): 1926 até 1989
昭和元年 = 1926
昭和63年 = 1988

NUNCA confunda:
平成8年 (1996) com 令和8年 (2026)
平成10年 (1998) com 令和10年 (2028)
平成25年 (2013) com 令和5年 (2023)

Leia o caractere da ERA com atenção:
令 = Reiwa
平 = Heisei
昭 = Showa
明 = Meiji
大 = Taisho

=========================================================
REGRA CRÍTICA: INCLUA SEMPRE A ERA
=========================================================

NUNCA retorne somente o número do ano.
NUNCA retorne "8" ou "10" sozinhos.

SEMPRE retorne a data COMPLETA com a ERA:
- 平成8年
- 令和10年
- 昭和63年

Se o documento mostrar apenas o número SEM a era:
retorne VERIFICAR para a data inteira

Não invente a era.
Não presuma a era com base no ano.
Não complete datas incompletas.
Se a data não estiver completamente legível:
retorne VERIFICAR.

=========================================================
VENCIMENTO DO SHAKEN
=========================================================

VENCIMENTO DO SHAKEN:
Use EXCLUSIVAMENTE o campo:
有効期間の満了する日

INSTRUÇÃO CRÍTICA - LEIA COM ATENÇÃO:
1. O rótulo 有効期間の満了する日 significa "Data de Expiração do Shaken"
2. NUNCA confunda com outros rótulos de data
3. shaken_vencimento DEVE vir de 有効期間の満了する日
4. shaken_vencimento NUNCA deve vir de 初度検査年月
5. shaken_vencimento NUNCA deve vir de 交付年月日

PROCEDIMENTO OBRIGATÓRIO:
1. Procure VISUALMENTE o rótulo 有効期間の満了する日 no documento
2. Leia SOMENTE a data que está IMEDIATAMENTE ao lado/abaixo de 有効期間の満了する日
3. IGNORE completamente 初度検査年月 e 交付年月日 para o campo shaken_vencimento
4. Se 有効期間の満了する日 não estiver visível ou legível, retorne VERIFICAR

IMPORTANTE - POSIÇÃO ESPACIAL:
- Cada rótulo tem sua própria data ao lado
- NÃO use datas de outras partes do documento
- A data de 有効期間の満了する日 está IMEDIATAMENTE ao lado do rótulo 有効期間の満了する日
- NÃO troque as datas entre os rótulos

EXEMPLO CRÍTICO:
Se o documento mostrar:
交付年月日 = 令和6年3月19日 (data_registro)
有効期間の満了する日 = 令和8年3月18日 (shaken_vencimento)
初度検査年月 = 平成28年7月27日 (NÃO USAR)

Resultado OBRIGATÓRIO:
data_registro = 令和6年3月19日
shaken_vencimento = 令和8年3月18日

NUNCA retorne:
shaken_vencimento = 平成28年7月27日 (ERRADO - é 初度検査年月)
shaken_vencimento = 令和6年3月19日 (ERRADO - é 交付年月日)

=========================================================
NOME E CONTATO
=========================================================

NOME:
Extraia o nome do proprietário somente quando estiver visível.

CONTATO:
Extraia telefone somente quando estiver visível.

=========================================================
REGRAS GERAIS
=========================================================

- Retorne somente JSON válido.
- Não escreva explicações fora do JSON.
- Não invente informações.
- Não faça suposições.
- Para qualquer campo ilegível, ausente ou duvidoso, use VERIFICAR.
- Preserve os dados exatamente como aparecem no documento.
- Diferencie cuidadosamente fabricante, modelo, classificação, placa,
  chassi, data de registro e vencimento do shaken.
"""

RETRY_PROMPT = r"""

Faça uma segunda conferência visual deste documento japonês.

Retorne somente JSON válido:

{
  "placa": "",
  "shaken_vencimento": "",
  "data_registro": ""
}

=========================================================
PLACA — LEITURA CRÍTICA DOS KANJIS
=========================================================

PLACA:
Leia EXCLUSIVAMENTE o campo:
自動車登録番号又は車両番号

A estrutura OBRIGATÓRIA é:
[REGIÃO EM KANJI] [CLASSIFICAÇÃO 3 DÍGITOS] [KANA] [NÚMERO]

=========================================================
REGRA CRÍTICA: NÃO SUBSTITUIR KANJIS
=========================================================

Os dois primeiros kanjis da região DEVEM ser lidos EXATAMENTE
como aparecem na fotografia.

É PROIBIDO:
- Substituir kanjis por cidades conhecidas
- Trocar 豊橋 por 浜松
- Trocar 豊 por 浜
- Trocar 橋 por 松
- Trocar 名古屋 por 浜松
- Trocar 豊田 por 浜松
- Presumir a cidade com base em probabilidade

Se os kanjis não estiverem 100% claros:
retorne VERIFICAR para a placa inteira

=========================================================
KANJIS QUE FREQUENTEMENTE SÃO CONFUNDIDOS
=========================================================

豊 (yutaka) ≠ 浜 (hama)
橋 (hashi) ≠ 松 (matsu)
名 (na) ≠ 浜 (hama)
古 (furui) ≠ 松 (matsu)
屋 (ya) ≠ 浜 (hama)

Leia CADA kanji individualmente, observando:
- Número de traços
- Posição dos traços
- Forma exata do caractere

=========================================================
EXEMPLOS DE PLACAS CORRETAS
=========================================================

Se a foto mostrar claramente:
豊橋 581 り 6940
→ Retorne: 豊橋 581 り 6940

Se a foto mostrar claramente:
浜松 581 す 4338
→ Retorne: 浜松 581 す 4338

Se a foto mostrar claramente:
名古屋 330 あ 1234
→ Retorne: 名古屋 330 あ 1234

NUNCA retorne:
浜松 581 り 6940 (kanji da região incorreto)
豊橋 581 す 4338 (kanji da região incorreto)

Se faltar qualquer parte da placa ou houver dúvida:
retorne VERIFICAR

=========================================================
VENCIMENTO DO SHAKEN - PRIORIDADE MÁXIMA
=========================================================

VENCIMENTO DO SHAKEN:
Use EXCLUSIVAMENTE o campo:
有効期間の満了する日

INSTRUÇÃO CRÍTICA - LEIA COM ATENÇÃO:
1. O rótulo 有効期間の満了する日 significa "Data de Expiração do Shaken"
2. NUNCA confunda com outros rótulos de data
3. shaken_vencimento DEVE vir de 有効期間の満了する日
4. shaken_vencimento NUNCA deve vir de 初度検査年月
5. shaken_vencimento NUNCA deve vir de 交付年月日

PROCEDIMENTO OBRIGATÓRIO:
1. Procure VISUALMENTE o rótulo 有効期間の満了する日 no documento
2. Leia SOMENTE a data que está IMEDIATAMENTE ao lado/abaixo de 有効期間の満了する日
3. IGNORE completamente 初度検査年月 e 交付年月日 para o campo shaken_vencimento
4. Se 有効期間の満了する日 não estiver visível ou legível, retorne VERIFICAR

IMPORTANTE - POSIÇÃO ESPACIAL:
- Cada rótulo tem sua própria data ao lado
- NÃO use datas de outras partes do documento
- A data de 有効期間の満了する日 está IMEDIATAMENTE ao lado do rótulo 有効期間の満了する日
- NÃO troque as datas entre os rótulos

EXEMPLO CRÍTICO:
Se o documento mostrar:
交付年月日 = 令和6年3月19日 (data_registro)
有効期間の満了する日 = 令和8年3月18日 (shaken_vencimento)
初度検査年月 = 平成28年7月27日 (NÃO USAR)

Resultado OBRIGATÓRIO:
data_registro = 令和6年3月19日
shaken_vencimento = 令和8年3月18日

NUNCA retorne:
shaken_vencimento = 平成28年7月27日 (ERRADO - é 初度検査年月)
shaken_vencimento = 令和6年3月19日 (ERRADO - é 交付年月日)

=========================================================
DATA DE REGISTRO
=========================================================

DATA DE REGISTRO:
Use EXCLUSIVAMENTE o campo:
交付年月日

INSTRUÇÃO CRÍTICA - LEIA COM ATENÇÃO:
1. O rótulo 交付年月日 significa "Data de Entrega/Registro"
2. O rótulo 初度検査年月 significa "Data da Primeira Inspeção"
3. NUNCA confunda estes dois rótulos
4. data_registro DEVE vir de 交付年月日
5. data_registro NUNCA deve vir de 初度検査年月

PROCEDIMENTO OBRIGATÓRIO:
1. Procure VISUALMENTE o rótulo 交付年月日 no documento
2. Leia SOMENTE a data que está IMEDIATAMENTE ao lado/abaixo de 交付年月日
3. IGNORE completamente 初度検査年月 para o campo data_registro
4. Se 交付年月日 não estiver visível ou legível, retorne VERIFICAR

IMPORTANTE - POSIÇÃO ESPACIAL (ESQUERDA/DIREITA):
- No documento, há múltiplas datas dispostas horizontalmente
- data_registro deve usar a data da ESQUERDA (ano mais recente)
- shaken_vencimento deve usar a data da DIREITA (ano mais recente)
- A data do MEIO (ano antigo como 平成28年) NUNCA deve ser usada
- NÃO troque as datas entre as posições

EXEMPLO CRÍTICO:
Se o documento mostrar 3 datas horizontalmente:
Data ESQUERDA = 令和6年3月19日 (data_registro)
Data MEIO = 平成28年7月27日 (NÃO USAR)
Data DIREITA = 令和8年3月18日 (shaken_vencimento)

Resultado OBRIGATÓRIO:
data_registro = 令和6年3月19日 (data da ESQUERDA)
shaken_vencimento = 令和8年3月18日 (data da DIREITA)

NUNCA retorne:
data_registro = 平成28年7月27日 (ERRADO - é data do MEIO)
shaken_vencimento = 平成28年7月27日 (ERRADO - é data do MEIO)

=========================================================
CONVERSÃO DE ERAS JAPONESAS
=========================================================

É CRÍTICO identificar corretamente a ERA japonesa:

令和 (Reiwa): Começou em 2019
令和元年 = 2019
令和8年 = 2026
令和10年 = 2028

平成 (Heisei): 1988 até 2019
平成元年 = 1989
平成8年 = 1996
平成10年 = 1998
平成25年 = 2013

昭和 (Showa): 1926 até 1989
昭和元年 = 1926
昭和63年 = 1988

NUNCA confunda:
平成8年 (1996) com 令和8年 (2026)
平成10年 (1998) com 令和10年 (2028)
平成25年 (2013) com 令和5年 (2023)

Leia o caractere da ERA com atenção:
令 = Reiwa
平 = Heisei
昭 = Showa

=========================================================
REGRA CRÍTICA: INCLUA SEMPRE A ERA
=========================================================

NUNCA retorne somente o número do ano.
NUNCA retorne "8" ou "10" sozinhos.

SEMPRE retorne a data COMPLETA com a ERA:
- 平成8年
- 令和10年
- 昭和63年

Se o documento mostrar apenas o número SEM a era:
retorne VERIFICAR para a data inteira

Não invente a era.
Não presuma a era com base no ano.
Não complete datas incompletas.
Se houver dúvida, retorne VERIFICAR

VENCIMENTO DO SHAKEN:
Use EXCLUSIVAMENTE o campo:
有効期間の満了する日

INSTRUÇÃO CRÍTICA - LEIA COM ATENÇÃO:
1. O rótulo 有効期間の満了する日 significa "Data de Expiração do Shaken"
2. NUNCA confunda com outros rótulos de data
3. shaken_vencimento DEVE vir de 有効期間の満了する日
4. shaken_vencimento NUNCA deve vir de 初度検査年月
5. shaken_vencimento NUNCA deve vir de 交付年月日

PROCEDIMENTO OBRIGATÓRIO:
1. Procure VISUALMENTE o rótulo 有効期間の満了する日 no documento
2. Leia SOMENTE a data que está IMEDIATAMENTE ao lado/abaixo de 有効期間の満了する日
3. IGNORE completamente 初度検査年月 e 交付年月日 para o campo shaken_vencimento
4. Se 有効期間の満了する日 não estiver visível ou legível, retorne VERIFICAR

IMPORTANTE - POSIÇÃO ESPACIAL:
- Cada rótulo tem sua própria data ao lado
- NÃO use datas de outras partes do documento
- A data de 有効期間の満了する日 está IMEDIATAMENTE ao lado do rótulo 有効期間の満了する日
- NÃO troque as datas entre os rótulos

EXEMPLO CRÍTICO:
Se o documento mostrar:
交付年月日 = 令和6年3月19日 (data_registro)
有効期間の満了する日 = 令和8年3月18日 (shaken_vencimento)
初度検査年月 = 平成28年7月27日 (NÃO USAR)

Resultado OBRIGATÓRIO:
data_registro = 令和6年3月19日
shaken_vencimento = 令和8年3月18日

NUNCA retorne:
shaken_vencimento = 平成28年7月27日 (ERRADO - é 初度検査年月)
shaken_vencimento = 令和6年3月19日 (ERRADO - é 交付年月日)
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
    imagem.save(buffer, format="JPEG", quality=90, optimize=True)

    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# =========================================================
# OPENAI CALL
# =========================================================

def _chamar_openai(imagem_b64, prompt_sistema):
    if not OPENAI_AVAILABLE or client is None:
        raise RuntimeError(
            "OpenAI não está disponível. Verifique OPENAI_API_KEY."
        )

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt_sistema},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Leia cuidadosamente a imagem e retorne somente o JSON solicitado.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/jpeg;base64," + imagem_b64,
                            "detail": "high",
                        },
                    },
                ],
            },
        ],
    )

    conteudo = resposta.choices[0].message.content
    if not conteudo:
        raise RuntimeError("A OpenAI retornou resposta vazia.")

    return json.loads(conteudo)


# =========================================================
# NORMALIZAÇÃO DOS DADOS
# =========================================================

def _normalizar_dados_ocr(dados):
    if not isinstance(dados, dict):
        dados = {}

    resultado = {
        "nome": _normalizar_nao_identificado(dados.get("nome", "")),
        "contato": _normalizar_nao_identificado(dados.get("contato", "")),
        "fabricante": _normalizar_nao_identificado(dados.get("fabricante", "")),
        "modelo": _normalizar_nao_identificado(dados.get("modelo", "")),
        "veiculo": _normalizar_nao_identificado(dados.get("veiculo", "")),
        "chassi": _normalizar_nao_identificado(dados.get("chassi", "")),
        "chassi_completo": _normalizar_nao_identificado(dados.get("chassi_completo", "")),
        "placa": _normalizar_nao_identificado(dados.get("placa", "")),
        "shaken_vencimento": _normalizar_nao_identificado(dados.get("shaken_vencimento", "")),
        "data_registro": _normalizar_nao_identificado(dados.get("data_registro", "")),
    }

    if resultado["veiculo"] != "VERIFICAR":
        resultado["veiculo"] = traduzir_veiculo(resultado["veiculo"])

    for campo in ["chassi", "chassi_completo"]:
        if resultado[campo] != "VERIFICAR":
            resultado[campo] = re.sub(r"\s+", "", str(resultado[campo])).upper()

    return resultado


def _converter_datas_dados(dados):
    for campo in ["shaken_vencimento", "data_registro"]:
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

    # Só precisa retry se algum campo for VERIFICAR ou inválido
    if dados.get("shaken_vencimento") == "VERIFICAR" or not validar_data_convertida(dados.get("shaken_vencimento", "")):
        return True

    if dados.get("data_registro") == "VERIFICAR" or not validar_data_convertida(dados.get("data_registro", "")):
        return True

    return False


def _mesclar_retry(original, retry):
    if not isinstance(retry, dict):
        return original

    # Só sobrescreve se o original for VERIFICAR ou inválido
    if original.get("shaken_vencimento") == "VERIFICAR" or not validar_data_convertida(original.get("shaken_vencimento", "")):
        shaken_retry = converter_data_japonesa(retry.get("shaken_vencimento", ""))
        if shaken_retry and validar_data_convertida(shaken_retry):
            original["shaken_vencimento"] = shaken_retry

    if original.get("data_registro") == "VERIFICAR" or not validar_data_convertida(original.get("data_registro", "")):
        registro_retry = converter_data_japonesa(retry.get("data_registro", ""))
        if registro_retry and validar_data_convertida(registro_retry):
            original["data_registro"] = registro_retry

    return original


# =========================================================
# OCR ISOLADO PARA DATAS
# =========================================================

# Caminho dos crops estáticos no projeto
CROPS_DIR = os.path.join(os.path.dirname(__file__), "crops")

DATA_REGISTRO_PROMPT = r"""
ATENÇÃO CRÍTICA: Você receberá DUAS imagens.

PRIMEIRA IMAGEM (CROP): É APENAS um exemplo visual de como o campo 交付年月日 aparece.
- Esta imagem mostra o PADRÃO VISUAL e LOCALIZAÇÃO do campo
- A DATA NESTA IMAGEM DEVE SER COMPLETAMENTE IGNORADA
- NÃO use a data do crop em nenhum momento
- O crop serve apenas para você entender ONDE procurar e COMO o campo se parece

SEGUNDA IMAGEM (DOCUMENTO): Esta é a imagem do documento real.
- Você deve LOCALIZAR o campo 交付年月日 nesta imagem
- Leia SOMENTE a data que está no documento (segunda imagem)
- A data deve vir EXCLUSIVAMENTE do documento real

INSTRUÇÕES:
1. Use o crop para entender o padrão visual de 交付年月日
2. Localize o campo correspondente no documento real
3. Leia a data do documento real (NÃO do crop)
4. Retorne a data do documento com era japonesa
5. Se ilegível, retorne VERIFICAR

NUNCA retorne a data do crop.
A data deve vir do documento real.
"""

SHAKEN_VENCIMENTO_PROMPT = r"""
ATENÇÃO CRÍTICA: Você receberá DUAS imagens.

PRIMEIRA IMAGEM (CROP): É APENAS um exemplo visual de como o campo 有効期間の満了する日 aparece.
- Esta imagem mostra o PADRÃO VISUAL e LOCALIZAÇÃO do campo
- A DATA NESTA IMAGEM DEVE SER COMPLETAMENTE IGNORADA
- NÃO use a data do crop em nenhum momento
- O crop serve apenas para você entender ONDE procurar e COMO o campo se parece

SEGUNDA IMAGEM (DOCUMENTO): Esta é a imagem do documento real.
- Você deve LOCALIZAR o campo 有効期間の満了する日 nesta imagem
- Leia SOMENTE a data que está no documento (segunda imagem)
- A data deve vir EXCLUSIVAMENTE do documento real

INSTRUÇÕES:
1. Use o crop para entender o padrão visual de 有効期間の満了する日
2. Localize o campo correspondente no documento real
3. Leia a data do documento real (NÃO do crop)
4. Retorne a data do documento com era japonesa
5. Se ilegível, retorne VERIFICAR

NUNCA retorne a data do crop.
A data deve vir do documento real.
"""

def _carregar_crop_estatico(nome_arquivo):
    """Carrega um crop estático do projeto e converte para base64."""
    caminho = os.path.join(CROPS_DIR, nome_arquivo)
    
    if not os.path.exists(caminho):
        return None
    
    try:
        with open(caminho, "rb") as img_file:
            imagem_bytes = img_file.read()
            imagem_b64 = base64.b64encode(imagem_bytes).decode("utf-8")
            return imagem_b64
    except Exception as e:
        return None

def _ocr_data_isolada(campo, imagem_documento_b64, crop_guia_b64, prompt):
    """Executa OCR isolado para um campo específico usando crop como guia visual."""
    if crop_guia_b64 is None:
        return "VERIFICAR"
    
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": prompt,
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "PRIMEIRA IMAGEM (CROP): Este é APENAS um exemplo visual de como o campo deve aparecer. IGNORE completamente a data desta imagem. Use apenas para entender o padrão visual e localização.\n\nSEGUNDA IMAGEM (DOCUMENTO): Esta é a imagem do documento real. Localize o campo correspondente ao exemplo e leia SOMENTE a data desta segunda imagem (o documento real). NUNCA use a data do crop.",
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64," + crop_guia_b64,
                                "detail": "high",
                            },
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": "data:image/jpeg;base64," + imagem_documento_b64,
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
        )
        
        texto_bruto = resposta.choices[0].message.content
        
        # Remove aspas e espaços extras
        texto_limpo = texto_bruto.strip().strip('"').strip("'")
        
        return texto_limpo
        
    except Exception as e:
        return "VERIFICAR"

def extrair_dados_do_documento(f):
    """Extrai dados do documento usando crops estáticos como guia."""
    if f is None:
        return None

    try:
        print(
            f"[OCR] Iniciando processamento: "
            f"{getattr(f, 'name', 'arquivo')}"
        )

        imagem_b64 = _preparar_imagem(f)

        # OCR da imagem inteira para campos gerais (exceto datas)
        dados_brutos = _chamar_openai(
            imagem_b64,
            SYSTEM_PROMPT,
        )

        dados = _normalizar_dados_ocr(dados_brutos)

        # Carrega crops estáticos como guia
        crop_data_registro_b64 = _carregar_crop_estatico("data_registro.png")
        crop_shaken_vencimento_b64 = _carregar_crop_estatico("shaken_vencimento.png")

        # Se crops estão disponíveis, usa OCR com guia visual
        if crop_data_registro_b64 or crop_shaken_vencimento_b64:
            # Refaz OCR com crops como guia para datas
            if crop_data_registro_b64:
                data_registro_bruta = _ocr_data_isolada("data_registro", imagem_b64, crop_data_registro_b64, DATA_REGISTRO_PROMPT)
                if data_registro_bruta != "VERIFICAR":
                    dados["data_registro"] = data_registro_bruta
            
            if crop_shaken_vencimento_b64:
                shaken_vencimento_bruto = _ocr_data_isolada("shaken_vencimento", imagem_b64, crop_shaken_vencimento_b64, SHAKEN_VENCIMENTO_PROMPT)
                if shaken_vencimento_bruto != "VERIFICAR":
                    dados["shaken_vencimento"] = shaken_vencimento_bruto

        # Conversão das datas
        dados = _converter_datas_dados(dados)

        print("[OCR] Processamento concluído.")
        return dados

    except Exception as e:
        print(f"[OCR] Erro no processamento: {e}")
        import traceback
        print(traceback.format_exc())

        return {
            "nome": "VERIFICAR",
            "contato": "VERIFICAR",
            "fabricante": "VERIFICAR",
            "modelo": "VERIFICAR",
            "veiculo": "VERIFICAR",
            "chassi": "VERIFICAR",
            "chassi_completo": "VERIFICAR",
            "placa": "VERIFICAR",
            "shaken_vencimento": "VERIFICAR",
            "data_registro": "VERIFICAR",
        }


# Compatibilidade com possíveis imports antigos
extrair_dado = extrair_dados_do_documento
extrair_dados = extrair_dados_do_documento