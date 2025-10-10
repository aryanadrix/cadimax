from baseDados.conexao import db

class CandidatoSelecionado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120))
    vaga = db.Column(db.String(120))
    municipio = db.Column(db.String(120))
    comuna = db.Column(db.String(120))
    resultado = db.Column(db.String(120))

class HistoricoImportacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(120))
    data = db.Column(db.DateTime)
    utilizador = db.Column(db.String(120))
    ip = db.Column(db.String(45))