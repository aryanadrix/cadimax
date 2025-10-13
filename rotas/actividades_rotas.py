from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from baseDados.conexao import db
from modelos.actividade_modelo import Actividade

rota_actividades = Blueprint('rota_actividades', __name__)

UPLOAD_ACTIVIDADES = os.path.join('static', 'img', 'actividades')
os.makedirs(UPLOAD_ACTIVIDADES, exist_ok=True)

# ====================== PORTAL PÚBLICO ======================
@rota_actividades.route('/actividades')
def actividades():
    posts = Actividade.query.order_by(Actividade.data_publicacao.desc()).all()
    return render_template('actividades.html', posts=posts)

# ====================== ÁREA ADMINISTRATIVA ======================
@rota_actividades.route('/admin/actividades')
def admin_actividades():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))
    actividades = Actividade.query.order_by(Actividade.data_publicacao.desc()).all()
    return render_template('admin_actividades.html', actividades=actividades)

# Criar nova publicação
@rota_actividades.route('/admin/actividades/novo', methods=['POST'])
def nova_actividade():
    titulo = request.form.get('titulo')
    corpo = request.form.get('corpo')
    data_atividade = request.form.get('data_atividade')
    foto = request.files.get('foto')

    if not (titulo and corpo and data_atividade):
        flash('Preencha todos os campos obrigatórios.', 'warning')
        return redirect(url_for('rota_actividades.admin_actividades'))

    foto_path = None
    if foto and foto.filename:
        filename = secure_filename(foto.filename)
        foto_path = os.path.join(UPLOAD_ACTIVIDADES, filename)
        foto.save(foto_path)
        foto_path = '/' + foto_path

    nova = Actividade(
        titulo=titulo,
        corpo=corpo,
        data_atividade=data_atividade,
        foto=foto_path,
        autor=session.get('nome', 'Administrador'),
    )
    db.session.add(nova)
    db.session.commit()
    flash('✅ Publicação criada com sucesso!', 'success')
    return redirect(url_for('rota_actividades.admin_actividades'))

# API — obter dados de uma publicação (para editar)
@rota_actividades.route('/admin/actividades/<int:aid>/json')
def get_actividade_json(aid):
    act = Actividade.query.get_or_404(aid)
    return jsonify({
        'id': act.id,
        'titulo': act.titulo,
        'corpo': act.corpo,
        'foto': act.foto,
        'data_atividade': act.data_atividade
    })

# Editar publicação
@rota_actividades.route('/admin/actividades/editar/<int:aid>', methods=['POST'])
def editar_actividade(aid):
    act = Actividade.query.get(aid)
    if not act:
        return jsonify({'success': False, 'msg': 'Publicação não encontrada.'})

    act.titulo = request.form.get('titulo')
    act.corpo = request.form.get('corpo')
    act.data_atividade = request.form.get('data_atividade')
    foto = request.files.get('foto')
    if foto and foto.filename:
        filename = secure_filename(foto.filename)
        foto_path = os.path.join(UPLOAD_ACTIVIDADES, filename)
        foto.save(foto_path)
        act.foto = '/' + foto_path

    db.session.commit()
    return jsonify({'success': True})

# Eliminar publicação
@rota_actividades.route('/admin/actividades/eliminar/<int:aid>', methods=['POST'])
def eliminar_actividade(aid):
    act = Actividade.query.get(aid)
    if not act:
        flash('Publicação não encontrada.', 'danger')
        return redirect(url_for('rota_actividades.admin_actividades'))
    db.session.delete(act)
    db.session.commit()
    flash('🗑️ Publicação eliminada com sucesso!', 'success')
    return redirect(url_for('rota_actividades.admin_actividades'))