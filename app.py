from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.secret_key = "chave_super_secreta"

# Configuração do PostgreSQL (ajusta com as tuas credenciais)
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:bBshVLxaJHketVuDYxmUDPGYkpexUmPG@postgres.railway.internal:5432/railway'


if os.environ.get('RAILWAY_ENVIRONMENT'):
    # 🚀 No Railway (produção)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
else:
    # 💻 No teu computador (desenvolvimento)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local.db'









app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



db = SQLAlchemy(app)

# Modelo de utilizador
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    senha = db.Column(db.String(100), nullable=False)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = Usuario.query.filter_by(username=username, senha=password).first()
        if user:
            session['logado'] = True
            session['usuario_nome'] = user.nome
            session['usuario_username'] = user.username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Credenciais erradas, por favor repetir.")
    return render_template('login.html')

@app.route('/index')
def index():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html', nome=session.get('usuario_nome'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Páginas placeholders
@app.route('/candidaturas')
def candidaturas():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html', nome=session.get('usuario_nome'))

@app.route('/candidatos_selecionados')
def candidatos_selecionados():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html', nome=session.get('usuario_nome'))

@app.route('/pagamentos')
def pagamentos():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html', nome=session.get('usuario_nome'))

@app.route('/registo_af')
def registo_af():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html', nome=session.get('usuario_nome'))

@app.route('/dashboard')
def dashboard():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html', nome=session.get('usuario_nome'))

@app.route('/configuracoes')
def configuracoes():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html', nome=session.get('usuario_nome'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)