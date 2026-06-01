import re
import cv2
import numpy as np
import pytesseract
from datetime import datetime
import os

# =========================================================
# CONFIG
# =========================================================

DEBUG_MODE = True

# Intervalo válido para veículos modernos
MIN_YEAR = 1990
MAX_YEAR = 2035

# Labels possíveis da data de registro
TARGET_LABELS = [
    "初度登録年月",
    "初度検査年月",
    "記録年月日"
]

# Regex rígida Reiwa
REIWA_REGEX = r'令和\s*([1-9]|1[0-9]|20)\s*年\s*(\d{1,2})\s*月'

# Regex rígida Heisei
HEISEI_REGEX = r'平成\s*([1-9]|[1-2][0-9]|3[0-1])\s*年\s*(\d{1,2})\s*月'

# Regex Showa
SHOWA_REGEX = r'昭和\s*([1-9]|[1-5][0-9]|6[0-4])\s*年\s*(\d{1,2})\s*月'

# Configuração do Tesseract (ajuste conforme sua instalação)
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_PREFIX = r"C:\Program Files\Tesseract-OCR\tessdata"

# =========================================================
# HELPERS
# =========================================================

def debug_log(message):
    if DEBUG_MODE:
        print(f"[DEBUG TESSERACT] {message}")

def save_debug_image(name, image):
    if DEBUG_MODE:
        debug_dir = "debug_ocr"
        os.makedirs(debug_dir, exist_ok=True)
        cv2.imwrite(os.path.join(debug_dir, name), image)
        debug_log(f"Imagem salva: {name}")

def upscale_image(image, scale=2):
    h, w = image.shape[:2]
    return cv2.resize(
        image,
        (w * scale, h * scale),
        interpolation=cv2.INTER_CUBIC
    )

def preprocess_for_ocr(image):
    """Pré-processamento agressivo para OCR"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Redução de ruído
    gray = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Threshold adaptativo
    binary = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        2
    )
    
    # Upscale
    binary = upscale_image(binary, 2)
    
    return binary

# =========================================================
# CONVERSÃO DE ERAS JAPONESAS
# =========================================================

def convert_japanese_year(era, year):
    year = int(year)
    
    if era == "令和":
        return 2018 + year
    elif era == "平成":
        return 1988 + year
    elif era == "昭和":
        return 1925 + year
    else:
        raise ValueError(f"Era japonesa desconhecida: {era}")

# =========================================================
# ROI
# =========================================================

def extract_registration_roi(image):
    """
    ROI da região da data de registro.
    Ajustar se necessário dependendo do modelo.
    """
    h, w = image.shape[:2]
    
    # Região superior central/direita (ajuste conforme necessário)
    # Aumentando a área para capturar mais contexto
    x1 = int(w * 0.30)
    x2 = int(w * 0.90)
    y1 = int(h * 0.05)
    y2 = int(h * 0.45)
    
    roi = image[y1:y2, x1:x2]
    
    debug_log(f"ROI => x:{x1}-{x2} y:{y1}-{y2}")
    save_debug_image("roi_raw.png", roi)
    
    return roi

# =========================================================
# OCR
# =========================================================

def run_ocr(image):
    """Executa OCR com Tesseract"""
    try:
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        # Configura TESSDATA_PREFIX
        os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX
        
        config = (
            "--oem 3 "
            "--psm 6 "
        )
        
        text = pytesseract.image_to_string(
            image,
            lang="jpn",
            config=config
        )
        
        return text
    except Exception as e:
        debug_log(f"Erro no OCR: {e}")
        raise

# =========================================================
# EXTRAÇÃO
# =========================================================

def find_target_line(text):
    """Busca linha com label de data de registro"""
    lines = text.splitlines()
    
    for line in lines:
        clean = line.strip()
        for label in TARGET_LABELS:
            if label in clean:
                debug_log(f"Label encontrada: {label}")
                debug_log(f"Linha alvo: {clean}")
                return clean
    
    # Fallback: junta linhas próximas
    for i, line in enumerate(lines):
        for label in TARGET_LABELS:
            if label in line:
                merged = "".join(lines[i:i+3])
                debug_log(f"Linha mesclada: {merged}")
                return merged
    
    raise ValueError("Linha da data de registro não encontrada.")

def parse_japanese_date(target_line):
    """Parse de data japonesa usando regex rígida"""
    # REIWA
    match = re.search(REIWA_REGEX, target_line)
    if match:
        year = match.group(1)
        month = int(match.group(2))
        gregorian = convert_japanese_year("令和", year)
        return gregorian, month
    
    # HEISEI
    match = re.search(HEISEI_REGEX, target_line)
    if match:
        year = match.group(1)
        month = int(match.group(2))
        gregorian = convert_japanese_year("平成", year)
        return gregorian, month
    
    # SHOWA
    match = re.search(SHOWA_REGEX, target_line)
    if match:
        year = match.group(1)
        month = int(match.group(2))
        gregorian = convert_japanese_year("昭和", year)
        return gregorian, month
    
    raise ValueError("Nenhuma data japonesa válida encontrada.")

def validate_year(year):
    """Valida se o ano está no intervalo válido"""
    if not (MIN_YEAR <= year <= MAX_YEAR):
        raise ValueError(
            f"Ano inválido detectado: {year}. "
            f"OCR provavelmente capturou outro campo."
        )

# =========================================================
# PIPELINE PRINCIPAL
# =========================================================

def extract_registration_date(image_path):
    """
    Pipeline principal para extração de data de registro
    usando Tesseract + OpenCV
    """
    try:
        # Carregar imagem
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Erro ao carregar imagem: {image_path}")
        
        debug_log(f"Imagem carregada: {image_path}")
        
        # ROI
        roi = extract_registration_roi(image)
        
        # Pré-processamento
        processed = preprocess_for_ocr(roi)
        save_debug_image("roi_processed.png", processed)
        
        # OCR
        text = run_ocr(processed)
        debug_log("OCR bruto:")
        debug_log(text)
        
        # Salvar texto bruto para debug
        if DEBUG_MODE:
            debug_dir = "debug_ocr"
            os.makedirs(debug_dir, exist_ok=True)
            with open(os.path.join(debug_dir, "ocr_text.txt"), "w", encoding="utf-8") as f:
                f.write(text)
        
        # Linha alvo
        target_line = find_target_line(text)
        
        # Parse da data
        year, month = parse_japanese_date(target_line)
        
        debug_log(f"Ano detectado: {year}")
        debug_log(f"Mês detectado: {month}")
        
        # Validação
        validate_year(year)
        
        # Data final
        final_date = datetime(year, month, 1)
        return final_date.strftime("%Y-%m-%d")
        
    except Exception as e:
        debug_log(f"Erro na extração: {e}")
        raise

# =========================================================
# TESTE
# =========================================================

if __name__ == "__main__":
    image_path = "documento.jpg"
    
    try:
        result = extract_registration_date(image_path)
        print("\n========================")
        print("DATA EXTRAÍDA")
        print("========================")
        print(result)
    except Exception as e:
        print("\n========================")
        print("ERRO OCR")
        print("========================")
        print(str(e))
