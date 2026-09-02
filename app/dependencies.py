from fastapi import Header, HTTPException
import jwt as pyjwt
from app.security import decodificar_token


def obter_usuario_atual(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido.")

    token = authorization.split(" ")[1]

    try:
        payload = decodificar_token(token)
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido.")

    return {
        "tenant_id": payload["tenantId"],
        "user_id": payload["userId"],
        "papel": payload["papel"],
    }


def exigir_owner(usuario: dict) -> None:
    if usuario["papel"] != "owner":
        raise HTTPException(status_code=403, detail="Apenas o dono do negócio pode acessar este recurso.")
