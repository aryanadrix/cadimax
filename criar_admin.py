from app import create_app
from baseDados.conexao import db
from modelos.utilizador_modelo import Utilizador

app = create_app()

with app.app_context():
    db.create_all()

    username_admin = 'marillson2025@'
    admin_existente = Utilizador.query.filter_by(username=username_admin).first()

    if not admin_existente:
        novo_admin = Utilizador(
            nome='Marillson Rodrigues',
            username=username_admin,
            senha='12345@'
        )
        db.session.add(novo_admin)
        db.session.commit()
        print("✅ Administrador criado com sucesso!")
    else:
        print(f"⚠️ O utilizador '{username_admin}' já existe na base de dados.")