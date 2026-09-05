from fastapi import APIRouter, Depends, HTTPException
from psycopg2 import errors
from app.database import get_connection, release_connection
from app.dependencies import obter_usuario_atual, exigir_owner
from app.schemas import AgendamentoInput

router = APIRouter(prefix="/api/appointments", tags=["appointments"])


@router.post("", status_code=201)
def criar_agendamento(dados: AgendamentoInput):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tenants WHERE slug = %s", (dados.tenantSlug,))
        tenant_row = cursor.fetchone()
        if tenant_row is None:
            raise HTTPException(status_code=404, detail="Negócio não encontrado.")
        tenant_id = tenant_row[0]

        cursor.execute(
            "SELECT id FROM services WHERE id = %s AND tenant_id = %s",
            (dados.serviceId, tenant_id),
        )
        if cursor.fetchone() is None:
            raise HTTPException(status_code=404, detail="Serviço não encontrado para este negócio.")

        cursor.execute(
            """SELECT id FROM appointments
               WHERE tenant_id = %s AND service_id = %s AND horario = %s AND status = 'confirmado'""",
            (tenant_id, dados.serviceId, dados.horario),
        )
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Este horário acabou de ser preenchido. Escolha outro.")

        try:
            cursor.execute(
                """INSERT INTO appointments (tenant_id, service_id, cliente_nome, cliente_contato, horario)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id, cliente_nome, horario, status""",
                (tenant_id, dados.serviceId, dados.clienteNome, dados.clienteContato, dados.horario),
            )
            novo = cursor.fetchone()
            conn.commit()
        except errors.UniqueViolation:
            conn.rollback()
            raise HTTPException(status_code=409, detail="Este horário acabou de ser preenchido. Escolha outro.")

        return {"id": novo[0], "cliente_nome": novo[1], "horario": str(novo[2]), "status": novo[3]}
    finally:
        cursor.close()
        release_connection(conn)


@router.get("/disponibilidade")
def horarios_ocupados(tenant: str, serviceId: int, data: str):
    """Rota PÚBLICA — devolve os horários já ocupados de um serviço em um dia específico,
    para o front desabilitar essas opções antes do visitante tentar agendar."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM tenants WHERE slug = %s", (tenant,))
        tenant_row = cursor.fetchone()
        if tenant_row is None:
            raise HTTPException(status_code=404, detail="Negócio não encontrado.")
        tenant_id = tenant_row[0]

        cursor.execute(
            """SELECT horario FROM appointments
               WHERE tenant_id = %s AND service_id = %s
                 AND horario::date = %s
                 AND status = 'confirmado'
               ORDER BY horario""",
            (tenant_id, serviceId, data),
        )
        linhas = cursor.fetchall()

        return {"horariosOcupados": [str(l[0]) for l in linhas]}
    finally:
        cursor.close()
        release_connection(conn)


@router.get("")
def listar_agendamentos(usuario: dict = Depends(obter_usuario_atual)):
    exigir_owner(usuario)

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT a.id, a.cliente_nome, a.cliente_contato, a.horario, a.status, s.nome
               FROM appointments a
               JOIN services s ON s.id = a.service_id
               WHERE a.tenant_id = %s
               ORDER BY a.horario""",
            (usuario["tenant_id"],),
        )
        linhas = cursor.fetchall()
        return [
            {
                "id": l[0],
                "cliente_nome": l[1],
                "cliente_contato": l[2],
                "horario": str(l[3]),
                "status": l[4],
                "servico": l[5],
            }
            for l in linhas
        ]
    finally:
        cursor.close()
        release_connection(conn)
