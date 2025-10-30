# modelos/utilizador_modelo.py
#from baseDados.conexao import db
#from datetime import datetime

#class Utilizador(db.Model):
#    __tablename__ = "utilizadores"
#
#    id = db.Column(db.Integer, primary_key=True)
#    nome = db.Column(db.String(100), nullable=False)
#    username = db.Column(db.String(50), unique=True, nullable=False)
#    senha = db.Column(db.String(200), nullable=False)
#    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

#    def __repr__(self):
#       return f"<Utilizador {self.username}>"

from werkzeug.security import generate_password_hash, check_password_hash

class Utilizador(db.Model):
    __tablename__ = "utilizadores"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.senha = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.senha, password)
