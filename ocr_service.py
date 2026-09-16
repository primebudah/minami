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


# =========================================================
# FUNÇÕES DE DEBUG
# =========================================================

def _debug_log(tipo, mensagem, dados=None):
    """Armazena logs de debug no session_state para persistência"""
    try:
        if "debug_ocr_logs" not in st.session_state:
            st.session_state.debug_ocr_logs = []
        
        log_entry = {
            "tipo": tipo,
            "mensagem": mensagem,
            "timestamp": str(st.session_state.get("_debug_counter", 0))
        }
        
        if dados is not None:
            log_entry["dados"] = dados
        
        st.session_state.debug_ocr_logs.append(log_entry)
        st.session_state._debug_counter = st.session_state.get("_debug_counter", 0) + 1
    except Exception as e:
        # Se falhar ao armazenar log, não quebra o processamento
        print(f"[DEBUG] Erro ao armazenar log: {e}")


def _mostrar_logs_debug():
    """Exibe todos os logs de debug armazenados no session_state"""
    try:
        if "debug_ocr_logs" not in st.session_state or not st.session_state.debug_ocr_logs:
            return
        
        with st.expander("🔍 Logs de Debug OCR (Persistente)", expanded=True):
            for i, log in enumerate(st.session_state.debug_ocr_logs):
                st.markdown(f"**[{i+1}] {log['tipo']}** - {log['mensagem']}")
                if "dados" in log:
                    if isinstance(log["dados"], dict):
                        st.json(log["dados"])
                    else:
                        st.write(log["dados"])
                st.divider()
    except Exception as e:
        st.error(f"Erro ao exibir logs de debug: {e}")
        import traceback
        st.error(traceback.format_exc())


def converter_data_japonesa(valor):
    """
    Converte somente datas completas e válidas.
    Não completa mês ou dia ausente com 01.
    """

    if valor is None:
        return None

    texto = str(valor).strip()

    _debug_log("CONVERSOR_DATA", f"Entrada: '{texto}'")

    if not texto or _campo_nao_identificado(texto):
        _debug_log("CONVERSOR_DATA", "Texto vazio ou não identificado")
        return None

    texto = _converter_numeros_japoneses(texto)
    _debug_log("CONVERSOR_DATA", f"Após converter números: '{texto}'")

    match = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", texto)
    if match:
        resultado = _formatar_data_iso(
            match.group(1), match.group(2), match.group(3)
        )
        _debug_log("CONVERSOR_DATA", f"Match formato ISO: {resultado}")
        return resultado

    match = re.fullmatch(
        r"(\d{4})[\/.\-](\d{1,2})[\/.\-](\d{1,2})",
        texto,
    )
    if match:
        resultado = _formatar_data_iso(
            match.group(1), match.group(2), match.group(3)
        )
        _debug_log("CONVERSOR_DATA", f"Match formato com separadores: {resultado}")
        return resultado

    match = re.fullmatch(
        r"(\d{1,2})[\/.\-](\d{1,2})[\/.\-](\d{4})",
        texto,
    )
    if match:
        resultado = _formatar_data_iso(
            match.group(3), match.group(2), match.group(1)
        )
        _debug_log("CONVERSOR_DATA", f"Match formato invertido: {resultado}")
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
    #     _debug_log("CONVERSOR_DATA", f"Match formato japonês sem era: {resultado}")
    #     return resultado

    if "令和" in texto or re.search(r"\bR\s*\d+", texto, re.I):
        _debug_log("CONVERSOR_DATA", "Detectada era Reiwa")
        ano = extrair_ano_reiwa_regex(texto)
        _debug_log("CONVERSOR_DATA", f"Ano Reiwa extraído: {ano}")
        if ano is None:
            return None

        mes_match = re.search(r"(\d{1,2})\s*月", texto)
        dia_match = re.search(r"(\d{1,2})\s*日", texto)

        _debug_log("CONVERSOR_DATA", f"Mês extraído: {mes_match.group(1) if mes_match else 'NÃO ENCONTRADO'}")
        _debug_log("CONVERSOR_DATA", f"Dia extraído: {dia_match.group(1) if dia_match else 'NÃO ENCONTRADO'}")

        if mes_match and dia_match:
            resultado = _formatar_data_iso(
                ano, mes_match.group(1), dia_match.group(1)
            )
            _debug_log("CONVERSOR_DATA", f"Resultado Reiwa: {resultado}")
            _debug_log("CONVERSOR_DATA", f"Compondo data: ano={ano}, mes={mes_match.group(1)}, dia={dia_match.group(1)}")
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
            _debug_log("CONVERSOR_DATA", f"Resultado Reiwa alt: {resultado}")
            return resultado

        return None

    for era, regex, conversor in [
        ("平成", r"(?:平成|H)\s*([0-9]+)", calcular_ano_heisei),
        ("昭和", r"(?:昭和|S)\s*([0-9]+)", calcular_ano_showa),
        ("大正", r"(?:大正|T)\s*([0-9]+)", calcular_ano_taisho),
        ("明治", r"(?:明治|M)\s*([0-9]+)", calcular_ano_meiji),
    ]:
        if era in texto or re.search(regex, texto, re.I):
            _debug_log("CONVERSOR_DATA", f"Detectada era {era}")
            match_ano = re.search(regex, texto, re.I)
            if not match_ano:
                return None

            ano = conversor(match_ano.group(1))
            _debug_log("CONVERSOR_DATA", f"Ano {era} extraído: {ano}")
            mes_match = re.search(r"(\d{1,2})\s*月", texto)
            dia_match = re.search(r"(\d{1,2})\s*日", texto)

            _debug_log("CONVERSOR_DATA", f"Mês extraído: {mes_match.group(1) if mes_match else 'NÃO ENCONTRADO'}")
            _debug_log("CONVERSOR_DATA", f"Dia extraído: {dia_match.group(1) if dia_match else 'NÃO ENCONTRADO'}")

            if not mes_match or not dia_match:
                return None

            resultado = _formatar_data_iso(
                ano, mes_match.group(1), dia_match.group(1)
            )
            _debug_log("CONVERSOR_DATA", f"Resultado {era}: {resultado}")
            _debug_log("CONVERSOR_DATA", f"Compondo data: ano={ano}, mes={mes_match.group(1)}, dia={dia_match.group(1)}")
            return resultado

    numeros = re.sub(r"\D", "", texto)
    if len(numeros) == 8 and 1900 <= int(numeros[:4]) <= 2100:
        resultado = _formatar_data_iso(
            numeros[:4], numeros[4:6], numeros[6:8]
        )
        _debug_log("CONVERSOR_DATA", f"Match apenas números: {resultado}")
        return resultado

    _debug_log("CONVERSOR_DATA", "Nenhum match encontrado")
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
DATA DE REGISTRO
=========================================================

DATA DE REGISTRO:
Use EXCLUSIVAMENTE o campo:
交付年月日

INSTRUÇÃO CRÍTICA:
1. Primeiro, localize VISUALMENTE o rótulo 交付年月日 no documento
2. Leia SOMENTE a data que está dentro da mesma célula/linha do rótulo 交付年月日
3. NÃO use datas de outras células vizinhas

NUNCA use para data_registro:
初度検査年月
有効期間の満了する日
qualquer outra data do documento

EXEMPLO CRÍTICO:
Se o documento mostrar:
交付年月日 = 令和8年7月23日
初度検査年月 = 平成28年11月
有効期間の満了する日 = 令和9年12月4日

Resultado OBRIGATÓRIO:
data_registro = 令和8年7月23日
shaken_vencimento = 令和9年12月4日

NUNCA retorne:
data_registro = 平成28年11月 (errado - é 初度検査年月)
data_registro = 令和9年12月4日 (errado - é 有効期間の満了する日)

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

SHAKEN_VENCIMENTO:
Use exclusivamente:
有効期間の満了する日

Não confunda com:
交付年月日
初度検査年月
data de primeira inspeção
data de registro

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
DATA DE REGISTRO
=========================================================

DATA DE REGISTRO:
Use EXCLUSIVAMENTE o campo:
交付年月日

INSTRUÇÃO CRÍTICA:
1. Primeiro, localize VISUALMENTE o rótulo 交付年月日 no documento
2. Leia SOMENTE a data que está dentro da mesma célula/linha do rótulo 交付年月日
3. NÃO use datas de outras células vizinhas

NUNCA use para data_registro:
初度検査年月
有効期間の満了する日
qualquer outra data do documento

EXEMPLO CRÍTICO:
Se o documento mostrar:
交付年月日 = 令和8年7月23日
初度検査年月 = 平成28年11月
有効期間の満了する日 = 令和9年12月4日

Resultado OBRIGATÓRIO:
data_registro = 令和8年7月23日
shaken_vencimento = 令和9年12月4日

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

        _debug_log("CONVERSOR_DADOS", f"{campo} original do OCR: '{valor}'")

        if _campo_nao_identificado(valor):
            dados[campo] = "VERIFICAR"
            continue

        convertido = converter_data_japonesa(valor)

        _debug_log("CONVERSOR_DADOS", f"{campo} convertido: '{convertido}'")

        if convertido and validar_data_convertida(convertido):
            dados[campo] = convertido
            _debug_log("CONVERSOR_DADOS", f"{campo} FINAL (antes de tabela): '{convertido}'")
        else:
            dados[campo] = "VERIFICAR"
            _debug_log("CONVERSOR_DADOS", f"{campo} FINAL (antes de tabela): 'VERIFICAR'")

    return dados


# =========================================================
# RETRY
# =========================================================

def _dados_precisam_retry(dados):
    if not dados:
        return True

    if not validar_data_convertida(dados.get("shaken_vencimento", "")):
        return True

    if not validar_data_convertida(dados.get("data_registro", "")):
        return True

    try:
        ano_shaken = int(str(dados["shaken_vencimento"])[:4])
        ano_registro = int(str(dados["data_registro"])[:4])

        if abs(ano_shaken - ano_registro) > 5:
            return True
    except Exception:
        return True

    return False


def _mesclar_retry(original, retry):
    if not isinstance(retry, dict):
        return original

    shaken_retry = converter_data_japonesa(retry.get("shaken_vencimento", ""))
    if shaken_retry and validar_data_convertida(shaken_retry):
        original["shaken_vencimento"] = shaken_retry

    registro_retry = converter_data_japonesa(retry.get("data_registro", ""))
    if registro_retry and validar_data_convertida(registro_retry):
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

        # Inicializa storage de debug no session_state
        if "debug_ocr_logs" not in st.session_state:
            st.session_state.debug_ocr_logs = []

        imagem_b64 = _preparar_imagem(f)

        dados_brutos = _chamar_openai(
            imagem_b64,
            SYSTEM_PROMPT,
        )

        # Armazena JSON bruto no session_state
        st.session_state.debug_ocr_logs.append({
            "tipo": "JSON_BRUTO",
            "mensagem": f"Arquivo: {getattr(f, 'name', 'arquivo')}",
            "dados": dados_brutos
        })

        dados = _normalizar_dados_ocr(dados_brutos)
        dados = _converter_datas_dados(dados)

        if _dados_precisam_retry(dados):
            print("[OCR] Executando segunda conferência...")
            retry_bruto = _chamar_openai(imagem_b64, RETRY_PROMPT)
            dados = _mesclar_retry(dados, retry_bruto)
            dados = _converter_datas_dados(dados)

        print("[OCR] Processamento concluído.")
        return dados

    except Exception as e:
        print(f"[OCR] Erro no processamento: {e}")

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