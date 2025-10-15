from flask_migrate import Migrate
from baseDados.conexao import db
import os
from flask import Flask
from flask_wtf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

    app.config.update({
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SESSION_COOKIE_HTTPONLY': True,
        'SESSION_COOKIE_SECURE': os.environ.get('FLASK_ENV') == 'production',
        'PERMANENT_SESSION_LIFETIME': 3600,
    })

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')

    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres') and 'sslmode=' not in app.config['SQLALCHEMY_DATABASE_URI']:
        app.config['SQLALCHEMY_DATABASE_URI'] += '?sslmode=require'

    app.config['UPLOAD_DIR'] = os.getenv('UPLOAD_DIR', os.path.join('instance', 'uploads'))
    os.makedirs(app.config['UPLOAD_DIR'], exist_ok=True)

    # Inicializa o banco
    db.init_app(app)

    csrf.init_app(app)

    # 🔹 Inicializa o Migrate (adiciona esta linha)
    migrate = Migrate(app, db)

    # (Opcional) CSRF

    #if os.getenv('FLASK_ENV') == 'production':
    #try:
    #    from flask_wtf.csrf import CSRFProtect
    #    CSRFProtect(app)
    #except Exception:
    #   pass

    with app.app_context():
        from modelos.utilizador_modelo import Utilizador
        from modelos.importacao_modelo import ImportacaoDB
        from modelos.documento_modelo import Documento
        from modelos.candidato_modelo import Candidato
        from modelos.candidato_selecionado import CandidatoSelecionado, HistoricoImportacao
        from modelos.pag_formacoes import PagamentoFormacao
        from modelos.pag_dias_trabalho import PagamentoDiaTrabalho
        from modelos.dashboard_dados import DashboardDados
        if os.getenv('FLASK_ENV') != 'production':
            db.create_all()

    # Blueprints e context_processor
    from rotas.login_rotas import rota_login
    from rotas.index_rotas import rota_index
    from rotas.config_rotas import rota_config, obter_cores
    from rotas.candidaturas_rotas import rota_candidaturas
    from rotas.padrao_rotas import rota_padrao
    from rotas.candidatos_selecionados_rotas import rota_candidatos_selecionados
    from rotas.pagamentos_rotas import rota_pagamentos
    from rotas.actividades_rotas import rota_actividades
    from rotas.dashboard_rotas import rota_dashboard

    app.register_blueprint(rota_login)
    app.register_blueprint(rota_index)
    app.register_blueprint(rota_config)
    app.register_blueprint(rota_candidaturas)
    app.register_blueprint(rota_padrao)
    app.register_blueprint(rota_candidatos_selecionados)
    app.register_blueprint(rota_pagamentos)
    app.register_blueprint(rota_actividades)
    app.register_blueprint(rota_dashboard)

    @app.context_processor
    def inject_cores():
        return dict(cores=obter_cores())

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')