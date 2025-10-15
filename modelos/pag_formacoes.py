from baseDados.conexao import db

class PagamentoFormacao(db.Model):
    __tablename__ = 'pagamento_formacao'
    id = db.Column(db.Integer, primary_key=True)
    num_de_control_formacoes = db.Column(db.String(100))
    nome = db.Column(db.String(150))
    categoria = db.Column(db.String(120))
    municipio = db.Column(db.String(120))
    comuna = db.Column(db.String(120))
    telefone_formacoes = db.Column(db.String(50))
    numero_bi_formacoes = db.Column(db.String(50))
    iban_formacoes = db.Column(db.String(120))
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