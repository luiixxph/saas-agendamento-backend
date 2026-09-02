from fastapi import APIRouter, HTTPException
from app.database import get_connection, release_connection
from app.security import gerar_hash_senha, conferir_senha, gerar_token
from app.schemas import LoginInput, RegistrarOwnerInput

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
def login(dados: LoginInput):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tenants WHERE slug = %s", (dados.tenantSlug,))
        tenant_row = cursor.fetchone()
        if tenant_row is None:
            raise HTTPException(status_code=404, detail="Negócio não encontrado.")
        tenant_id = tenant_row[0]

        cursor.execute(
            "SELECT id, senha_hash, papel FROM users WHERE tenant_id = %s AND email = %s",
            (tenant_id, dados.email),
        )
        user_row = cursor.fetchone()
        if user_row is None:
            raise HTTPException(status_code=401, detail="Email ou senha inválidos.")

        user_id, senha_hash, papel = user_row

        if not conferir_senha(dados.senha, senha_hash):
            raise HTTPException(status_code=401, detail="Email ou senha inválidos.")

        token = gerar_token(tenant_id, user_id, papel)
        return {"token": token}
    finally:
        cursor.close()
        release_connection(conn)


@router.post("/registrar-owner", status_code=201)
def registrar_owner(dados: RegistrarOwnerInput):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tenants WHERE slug = %s", (dados.tenantSlug,))
        tenant_row = cursor.fetchone()
        if tenant_row is None:
            raise HTTPException(status_code=404, detail="Negócio não encontrado.")
        tenant_id = tenant_row[0]

        senha_hash = gerar_hash_senha(dados.senha)

        cursor.execute(
            """INSERT INTO users (tenant_id, nome, email, senha_hash, papel)
               VALUES (%s, %s, %s, %s, 'owner')
               RETURNING id, nome, email, papel""",
            (tenant_id, dados.nome, dados.email, senha_hash),
        )
        novo = cursor.fetchone()
        conn.commit()

        return {"id": novo[0], "nome": novo[1], "email": novo[2], "papel": novo[3]}
    finally:
        cursor.close()
        release_connection(conn)
