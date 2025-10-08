# modelos/candidato_modelo.py
from baseDados.conexao import db
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
import os

# Usa JSONB no PostgreSQL (Railway) e JSON no SQLite (local)
is_pg = bool(os.environ.get('RAILWAY_ENVIRONMENT'))
JSONType = PG_JSONB if is_pg else SQLITE_JSON

class Candidato(db.Model):
    __tablename__ = 'candidatos'

    id = db.Column(db.Integer, primary_key=True)

    # Campos "core" que usamos nos gráficos/filtragem
    nome = db.Column(db.String(255))
    municipio = db.Column(db.String(255))
    comuna = db.Column(db.String(255))
    vaga = db.Column(db.String(255))
    documentos = db.Column(db.String(255))     # pode vir texto (ex.: "BI;Certidão")
    completo = db.Column(db.Boolean, default=False)

    # Metadados
    fonte_titulo = db.Column(db.String(255))   # título dado no upload
    criado_em = db.Column(db.DateTime, server_default=db.func.now())

    # Tudo o resto da linha original fica aqui
    raw = db.Column(JSONType)