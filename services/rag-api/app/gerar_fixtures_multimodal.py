"""Gera documentos sintéticos (imagem + sidecar JSON) para testes de multimodal.

Campos simulados de boleto/carteirinha/apólice. O sidecar permite testes
reproduzíveis sem dependência do Tesseract; o caminho real de OCR é documentado.
"""

import json
import os

from PIL import Image, ImageDraw, ImageFont


FIXTURES = [
    {
        "arquivo": "boleto_001.png",
        "dados": {
            "numero_apolice": "AP-2024-001",
            "valor": "350.00",
            "data_vencimento": "2026-08-10",
            "nome_segurado": "Ana Silva",
        },
    },
    {
        "arquivo": "carteirinha_002.png",
        "dados": {
            "numero_apolice": "AP-2024-002",
            "nome_segurado": "Bruno Costa",
            "plano": "Previdência Premium",
            "validade": "2027-01-31",
        },
    },
    {
        "arquivo": "apolice_003.png",
        "dados": {
            "numero_apolice": "AP-2023-777",
            "valor_cobertura": "50000.00",
            "tipo": "Vida",
            "nome_segurado": "Carla Dias",
            "data_inicio": "2023-05-01",
        },
    },
]


def gerar():
    out = os.path.join(os.path.dirname(__file__), "documentos_teste")
    os.makedirs(out, exist_ok=True)
    for doc in FIXTURES:
        img = Image.new("RGB", (600, 300), "white")
        d = ImageDraw.Draw(img)
        try:
            fonte = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            fonte = ImageFont.load_default()
        y = 20
        d.text((20, y), "SEGURADORA EXEMPLO S.A.", fill="black", font=fonte)
        y += 40
        for chave, valor in doc["dados"].items():
            d.text((20, y), f"{chave}: {valor}", fill="black", font=fonte)
            y += 35
        caminho = os.path.join(out, doc["arquivo"])
        img.save(caminho)
        with open(caminho + ".json", "w", encoding="utf-8") as f:
            json.dump(doc["dados"], f, ensure_ascii=False, indent=2)
        print("gerado:", caminho)


if __name__ == "__main__":
    gerar()
