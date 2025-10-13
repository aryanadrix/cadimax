from baseDados.conexao import db
from datetime import datetime

class Actividade(db.Model):
    __tablename__ = 'actividades'

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(255), nullable=False)
    corpo = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(255), nullable=True)
    data_atividade = db.Column(db.String(50), nullable=False)
    data_publicacao = db.Column(db.DateTime, default=datetime.utcnow)
    autor = db.Column(db.String(120), nullable=True)

    def __repr__(self):
        return f"<Actividade {self.titulo}>"