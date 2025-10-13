from baseDados.conexao import db

class PagamentoFormacao(db.Model):
    __tablename__ = 'pagamento_formacao'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150))
    municipio = db.Column(db.String(120))
    categoria = db.Column(db.String(120))
    valor_trans = db.Column(db.Float)
    numDias = db.Column(db.Float)
    total_receber = db.Column(db.Float)

class HistoricoFormacao(db.Model):
    __tablename__ = 'historico_formacao'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    data = db.Column(db.DateTime)
    utilizador = db.Column(db.String(120))
    ip = db.Column(db.String(60))