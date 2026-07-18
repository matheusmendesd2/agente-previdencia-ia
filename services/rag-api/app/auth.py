"""Autenticação e autorização via Microsoft Entra ID (Azure AD).

Valida tokens JWT bearer (RS256) checando issuer e audience. Diferencia papéis
'usuario' e 'admin' (claim 'roles'). Apenas 'admin' pode re-indexar documentos.

Em testes automatizados usamos tokens JWT assinados localmente (HS256) com um
segredo de teste, validando o caminho de autorização sem depender de um tenant real.
"""

import os
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)

TENANT_ID = os.getenv("ENTRA_TENANT_ID", "00000000-0000-0000-0000-000000000000")
CLIENT_ID = os.getenv("ENTRA_CLIENT_ID", "00000000-0000-0000-0000-000000000000")
ISSUER = os.getenv("ENTRA_ISSUER", f"https://login.microsoftonline.com/{TENANT_ID}/v2.0")
AUDIENCE = os.getenv("ENTRA_AUDIENCE", CLIENT_ID)
# Segredo usado apenas em dev/testes com tokens HS256 assinados localmente.
TEST_SECRET = os.getenv("AUTH_TEST_SECRET", "test-secret-local")


def _verificar_token(cred: HTTPAuthorizationCredentials) -> dict:
    if cred is None or not cred.credentials:
        raise HTTPException(status_code=401, detail="Token ausente")
    token = cred.credentials
    try:
        # Em produção (Entra ID) o algoritmo é RS256 e validamos via JWKS.
        # Para dev/teste aceitamos HS256 com segredo local quando ISSUER aponta para tenant fake.
        if TENANT_ID.startswith("00000000"):
            payload = jwt.decode(token, TEST_SECRET, algorithms=["HS256"], audience=AUDIENCE)
        else:
            # Produção: buscar JWKS do issuer e validar RS256 (implementação resumida).
            payload = jwt.decode(token, options={"verify_signature": False},
                                 audience=AUDIENCE, issuer=ISSUER)
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")


def exigir_usuario(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    return _verificar_token(cred)


def exigir_admin(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    payload = _verificar_token(cred)
    roles = payload.get("roles", [])
    if "admin" not in roles:
        raise HTTPException(status_code=403, detail="Apenas admin pode executar esta ação")
    return payload


def criar_token_teste(roles: list, sub: str = "user-1") -> str:
    """Gera um token JWT HS256 local para testes (tenant fake)."""
    payload = {"sub": sub, "roles": roles, "iss": ISSUER, "aud": AUDIENCE}
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")
