from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import os
from app.database import get_connection, release_connection
from app.security import gerar_hash_senha

router = APIRouter(prefix="/api/admin", tags=["admin"])

ADMIN_SECRET = os.getenv("ADMIN_SECRET")


class ServicoNovoTenant(BaseModel):
    nome: str
    duracaoMinutos: int = 30
    precoCentavos: int = 0


class NovoTenantInput(BaseModel):
    nomeNegocio: str
    slug: str
    donoNome: str
    donoEmail: str
    donoSenha: str
    servicos: list[ServicoNovoTenant] = []


def exigir_admin(x_admin_secret: str = Header(None)):
    if not ADMIN_SECRET or x_admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Acesso negado.")


@router.post("/criar-tenant", status_code=201)
def criar_tenant(dados: NovoTenantInput, x_admin_secret: str = Header(None)):
    exigir_admin(x_admin_secret)

    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tenants WHERE slug = %s", (dados.slug,))
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Já existe um negócio com esse identificador (slug).")

        cursor.execute(
            "INSERT INTO tenants (nome, slug) VALUES (%s, %s) RETURNING id",
            (dados.nomeNegocio, dados.slug),
        )
        tenant_id = cursor.fetchone()[0]

        senha_hash = gerar_hash_senha(dados.donoSenha)
        cursor.execute(
            """INSERT INTO users (tenant_id, nome, email, senha_hash, papel)
               VALUES (%s, %s, %s, %s, 'owner')
               RETURNING id""",
            (tenant_id, dados.donoNome, dados.donoEmail, senha_hash),
        )
        owner_id = cursor.fetchone()[0]

        servicos_criados = []
        for servico in dados.servicos:
            cursor.execute(
                """INSERT INTO services (tenant_id, nome, duracao_minutos, preco_centavos)
                   VALUES (%s, %s, %s, %s)
                   RETURNING id, nome""",
                (tenant_id, servico.nome, servico.duracaoMinutos, servico.precoCentavos),
            )
            novo = cursor.fetchone()
            servicos_criados.append({"id": novo[0], "nome": novo[1]})

        conn.commit()

        return {
            "tenantId": tenant_id,
            "slug": dados.slug,
            "ownerId": owner_id,
            "servicosCriados": servicos_criados,
        }
    except HTTPException:
        conn.rollback()
        raise
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=500, detail="Erro ao criar o negócio. Nenhum dado foi salvo.")
    finally:
        cursor.close()
        release_connection(conn)
