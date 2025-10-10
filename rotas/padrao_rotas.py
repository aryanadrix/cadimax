# rotas/padrao_rotas.py
from flask import Blueprint, render_template, session, redirect, url_for

rota_padrao = Blueprint('rota_padrao', __name__)

@rota_padrao.route('/em_construcao')
def em_construcao():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))
    return render_template('em_construcao.html')


@rota_padrao.route('/')
def raiz():
    return redirect(url_for('rota_login.login'))
