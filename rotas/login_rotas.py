from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from modelos.utilizador_modelo import Utilizador
from baseDados.conexao import db

rota_login = Blueprint('rota_login', __name__)

@rota_login.route('/', methods=['GET', 'POST'])
@rota_login.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        senha = request.form['senha']

        utilizador = Utilizador.query.filter_by(username=username).first()

        if utilizador and utilizador.senha == senha:
            # ✅ Guarda o ID do utilizador na sessão
            session['usuario_id'] = utilizador.id
            session['nome'] = utilizador.nome
            flash(f'Bem-vindo, {utilizador.nome}!', 'success')
            return redirect(url_for('rota_index.index'))
        else:
            flash('Credenciais inválidas.', 'danger')
            return redirect(url_for('rota_login.login'))

    return render_template('login.html')


@rota_login.route('/logout')
def logout():
    # ✅ Remove a sessão
    session.clear()
    flash('Sessão terminada com sucesso.', 'info')
    return redirect(url_for('rota_login.login'))