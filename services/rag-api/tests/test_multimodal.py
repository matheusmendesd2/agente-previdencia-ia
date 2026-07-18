import os

from app.multimodal import LocalMockExtractor, AzureVisionExtractor
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "documentos_teste")


def _caminho(nome):
    return os.path.normpath(os.path.join(FIXTURES_DIR, nome))


def test_extrair_boleto():
    res = LocalMockExtractor().extrair(_caminho("boleto_001.png"))
    assert res.sucesso is True
    assert res.dados["numero_apolice"] == "AP-2024-001"
    assert res.dados["valor"] == "350.00"


def test_extrair_carteirinha():
    res = LocalMockExtractor().extrair(_caminho("carteirinha_002.png"))
    assert res.sucesso is True
    assert res.dados["nome_segurado"] == "Bruno Costa"


def test_extrair_apolice():
    res = LocalMockExtractor().extrair(_caminho("apolice_003.png"))
    assert res.sucesso is True
    assert res.dados["tipo"] == "Vida"
    assert res.dados["valor_cobertura"] == "50000.00"


def test_imagem_corrompida_trata_graciosamente():
    # Arquivo inexistente -> extractor retorna sucesso=False sem quebrar.
    res = LocalMockExtractor().extrair(_caminho("nao_existe.png"))
    assert res.sucesso is False


def test_endpoint_extrair_via_upload():
    import shutil
    os.makedirs("uploads_tmp", exist_ok=True)
    # O extractor local usa sidecar JSON; copiamos o sidecar para junto do upload.
    shutil.copy(_caminho("boleto_001.png.json"), os.path.join("uploads_tmp", "boleto_001.png.json"))
    caminho = _caminho("boleto_001.png")
    with open(caminho, "rb") as f:
        resp = client.post("/multimodal/extrair", files={"file": ("boleto_001.png", f, "image/png")})
    assert resp.status_code == 200
    data = resp.json()
    assert data["dados"]["numero_apolice"] == "AP-2024-001"


def test_endpoint_rejeita_nao_imagem():
    resp = client.post(
        "/multimodal/extrair",
        files={"file": ("doc.txt", b"texto", "text/plain")},
    )
    assert resp.status_code == 400
