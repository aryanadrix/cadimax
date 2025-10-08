from baseDados.conexao import db
from datetime import datetime

class Documento(db.Model):
    __tablename__ = 'documento'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    ficheiro = db.Column(db.String(200), nullable=False)
    usuario = db.Column(db.String(100))
    ip = db.Column(db.String(50))
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)