# criar_admin.py
from app import create_app
from baseDados.conexao import db
from modelos.utilizador_modelo import Utilizador
from werkzeug.security import generate_password_hash

def criar_admins():
    app = create_app()
    with app.app_context():
        db.create_all()  # Garante que as tabelas existem

        # Utilizadores padrão
        utilizadores_default = [
            {"nome": "Administrador Geral", "username": "admin", "senha": "12345"},
            {"nome": "Analista de Dados", "username": "analista", "senha": "12345"},
        ]

        for u in utilizadores_default:
            existente = Utilizador.query.filter_by(username=u["username"]).first()
            if not existente:
                novo = Utilizador(
                    nome=u["nome"],
                    username=u["username"],
                    senha=generate_password_hash(u["senha"])
                )
                db.session.add(novo)

        db.session.commit()
        print("✅ Utilizadores padrão criados com sucesso!")
        print("👉 admin / 12345")
        print("👉 analista / 12345")

if __name__ == "__main__":
    criar_admins()