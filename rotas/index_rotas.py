from flask import Blueprint, render_template, session, redirect, url_for, flash
from baseDados.conexao import db

rota_index = Blueprint('rota_index', __name__)

@rota_index.route('/index')
def index():
    if 'usuario_id' not in session:
        flash('Por favor, faça login primeiro.', 'warning')
        return redirect(url_for('rota_login.login'))
    return render_template('index.html', nome=session.get('nome'))