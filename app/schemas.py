from pydantic import BaseModel


class LoginInput(BaseModel):
    tenantSlug: str
    email: str
    senha: str


class RegistrarOwnerInput(BaseModel):
    tenantSlug: str
    nome: str
    email: str
    senha: str


class ServicoInput(BaseModel):
    nome: str
    duracaoMinutos: int = 30
    precoCentavos: int = 0


class AgendamentoInput(BaseModel):
    tenantSlug: str
    serviceId: int
    clienteNome: str
    clienteContato: str
    horario: str
