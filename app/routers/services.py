from fastapi import APIRouter, Depends
from app.database import get_connection, release_connection
from app.dependencies import obter_usuario_atual, exigir_owner
from app.schemas import ServicoInput

router = APIRouter(prefix="/api/services", tags=["services"])


@router.get("")
def listar_servicos(tenant: str):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT s.id, s.nome, s.duracao_minutos, s.preco_centavos
               FROM services s
               JOIN tenants t ON t.id = s.tenant_id
               WHERE t.slug = %s AND s.ativo = TRUE
               ORDER BY s.id""",
            (tenant,),
        )
        linhas = cursor.fetchall()
        return [
            {"id": l[0], "nome": l[1], "duracao_minutos": l[2], "preco_centavos": l[3]}
            for l in linhas
        ]
    finally:
        cursor.close()
        release_connection(conn)


@router.post("", status_code=201)
def criar_servico(dados: ServicoInput, usuario: dict = Depends(obter_usuario_atual)):
    exigir_owner(usuario)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO services (tenant_id, nome, duracao_minutos, preco_centavos)
               VALUES (%s, %s, %s, %s)
               RETURNING id, nome, duracao_minutos, preco_centavos""",
            (usuario["tenant_id"], dados.nome, dados.duracaoMinutos, dados.precoCentavos),
        )
        novo = cursor.fetchone()
        conn.commit()
        return {"id": novo[0], "nome": novo[1], "duracao_minutos": novo[2], "preco_centavos": novo[3]}
    finally:
        cursor.close()
        release_connection(conn)
