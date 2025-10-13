from flask import Flask
from baseDados.conexao import db
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = 'segredo_campanha'

    # Banco dinâmico: Railway ou local
    if os.environ.get('RAILWAY_ENVIRONMENT'):
        app.config[
            'SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bBshVLxaJHketVuDYxmUDPGYkpexUmPG@postgres.railway.internal:5432/railway'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa o SQLAlchemy
    db.init_app(app)

    # Importa modelos dentro do contexto
    with app.app_context():
        # Modelos principais
        from modelos.utilizador_modelo import Utilizador
        from modelos.importacao_modelo import ImportacaoDB
        from modelos.documento_modelo import Documento
        from modelos.candidato_modelo import Candidato
        from modelos.candidato_selecionado import CandidatoSelecionado, HistoricoImportacao


        # 🔸 NOVOS MODELOS DE PAGAMENTO
        from modelos.pag_formacoes import PagamentoFormacao
        from modelos.pag_dias_trabalho import PagamentoDiaTrabalho

        # Cria todas as tabelas caso não existam
        db.create_all()

    # Importa e regista os blueprints
    from rotas.login_rotas import rota_login
    from rotas.index_rotas import rota_index
    from rotas.config_rotas import rota_config, obter_cores
    from rotas.candidaturas_rotas import rota_candidaturas
    from rotas.padrao_rotas import rota_padrao
    from rotas.candidatos_selecionados_rotas import rota_candidatos_selecionados
    from rotas.pagamentos_rotas import rota_pagamentos
    from rotas.actividades_rotas import rota_actividades

    app.register_blueprint(rota_login)
    app.register_blueprint(rota_index)
    app.register_blueprint(rota_config)
    app.register_blueprint(rota_candidaturas)
    app.register_blueprint(rota_padrao)
    app.register_blueprint(rota_candidatos_selecionados)
    app.register_blueprint(rota_pagamentos)
    app.register_blueprint(rota_actividades)

    # 🔹 Injeta cores personalizadas nos templates
    @app.context_processor
    def inject_cores():
        return dict(cores=obter_cores())

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)