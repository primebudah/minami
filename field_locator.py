import cv2
import pytesseract
import numpy as np
import os

# Configuração do Tesseract
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_PREFIX = r"C:\Program Files\Tesseract-OCR\tessdata"

def find_registration_field_bbox(image):
    """
    Encontra a posição do campo '初度登録年月'
    usando OCR leve apenas para detecção de labels.
    
    Returns:
        tuple: (x1, y1, x2, y2) - coordenadas do bbox
    Raises:
        ValueError: Se o campo não for encontrado
    """
    # Configura Tesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
    os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX
    
    # Converte para grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # OCR leve para detecção de labels
    data = pytesseract.image_to_data(
        gray,
        lang="jpn",
        output_type=pytesseract.Output.DICT,
        config="--psm 6"
    )
    
    # Keywords para busca
    target_keywords = ["初度登録", "初度検査", "登録年月", "記録年月日"]
    
    n_boxes = len(data["text"])
    
    for i in range(n_boxes):
        text = data["text"][i].strip()
        
        for keyword in target_keywords:
            if keyword in text:
                x = data["left"][i]
                y = data["top"][i]
                w = data["width"][i]
                h = data["height"][i]
                
                # Expandir área para capturar a data ao lado
                padding_x = 300
                padding_y = 100
                
                x1 = max(0, x)
                y1 = max(0, y)
                
                x2 = x + w + padding_x
                y2 = y + h + padding_y
                
                print(f"[FIELD LOCATOR] Label '{keyword}' encontrada em: ({x1}, {y1}, {x2}, {y2})")
                return (x1, y1, x2, y2)
    
    raise ValueError("Campo de registro não encontrado no documento")

def extract_field_region(image, bbox):
    """
    Recorta a região do campo usando o bbox.
    
    Args:
        image: Imagem original
        bbox: (x1, y1, x2, y2)
    
    Returns:
        numpy.ndarray: Imagem recortada
    """
    x1, y1, x2, y2 = bbox
    h, w = image.shape[:2]
    
    # Limita às dimensões da imagem
    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)
    
    region = image[y1:y2, x1:x2]
    print(f"[FIELD LOCATOR] Região recortada: {region.shape}")
    
    return region
