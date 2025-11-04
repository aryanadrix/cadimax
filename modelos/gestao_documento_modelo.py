# modelos/gestao_documento_modelo.py
from baseDados.conexao import db
from datetime import datetime

class GestaoDocumento(db.Model):
    __tablename__ = "gestao_documentos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(200), nullable=False)
    categoria = db.Column(db.String(100), nullable=False)      # ex: "Relatórios", "Listas"
    nivel = db.Column(db.String(50), nullable=False)            # ex: "Nacional", "Provincial", "Municipal", "Comunal"
    municipio = db.Column(db.String(100))
    caminho = db.Column(db.String(300), nullable=False)
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    criado_por = db.Column(db.String(100), nullable=False)      # Nome do utilizador que fez upload