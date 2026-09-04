import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.routers import auth, services, appointments, admin

load_dotenv()

app = FastAPI(title="SaaS de Agendamento Multi-Tenant")

origens_permitidas = [o.strip() for o in os.getenv("CORS_ORIGIN", "").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origens_permitidas,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def status():
    return {"status": "API do SaaS de agendamento rodando."}


app.include_router(auth.router)
app.include_router(services.router)
app.include_router(appointments.router)
app.include_router(admin.router)
