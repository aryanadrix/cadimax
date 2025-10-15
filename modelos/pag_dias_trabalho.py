from baseDados.conexao import db

class PagamentoDiaTrabalho(db.Model):
    __tablename__ = 'pag_dias_trabalho'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    num_bi = db.Column(db.String(50))
    telefone = db.Column(db.String(50))
    categoria = db.Column(db.String(100))
    municipio = db.Column(db.String(100))
    comuna = db.Column(db.String(100))
    iban = db.Column(db.String(100))
    data_inicio = db.Column(db.String(50))
    data_fim = db.Column(db.String(50))
    numDias = db.Column(db.Float, default=0.0)
    valor_trans = db.Column(db.Float, default=0.0)
    total_receber = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<PagamentoDiaTrabalho {self.nome}>'

class HistoricoDiasTrabalho(db.Model):
    __tablename__ = 'historico_dias_trabalho'
    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200))
    data = db.Column(db.DateTime)
    utilizador = db.Column(db.String(120))
    ip = db.Column(db.String(60))