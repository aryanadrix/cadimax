from datetime import datetime
from baseDados.conexao import db

class DashboardDados(db.Model):
    __tablename__ = "dashboard_dados"

    id = db.Column(db.Integer, primary_key=True)
    data_importacao = db.Column(db.DateTime, default=datetime.utcnow)
    utilizador = db.Column(db.String(100))
    ip = db.Column(db.String(50))

    # Campos principais (strings para exibição)
    populacao_provincia = db.Column(db.String(100))
    orcamento_bie = db.Column(db.String(100))
    total_recebidos = db.Column(db.String(100))
    total_distribuidos = db.Column(db.String(100))
    quantidade_mosquiteiros_distribuidos = db.Column(db.String(100))

    agregados_estimados = db.Column(db.String(100))
    agregados_alcancados = db.Column(db.String(100))
    populacao_beneficiada = db.Column(db.String(100))
    gravidas_beneficiadas = db.Column(db.String(100))
    criancas_beneficiadas = db.Column(db.String(100))

    # Gráfico
    municipios = db.Column(db.PickleType)
    valores_municipios = db.Column(db.PickleType)

    def __repr__(self):
        return f"<DashboardDados id={self.id}>"