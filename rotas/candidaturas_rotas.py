# rotas/candidaturas_rotas.py
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from modelos.candidato_modelo import Candidato
from baseDados.conexao import db
from sqlalchemy import func

rota_candidaturas = Blueprint('rota_candidaturas', __name__)

@rota_candidaturas.route('/candidaturas')
def candidaturas():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    # Filtros (query params)
    municipio = request.args.get('municipio') or None
    vaga = request.args.get('vaga') or None

    query = Candidato.query
    if municipio:
        query = query.filter(Candidato.municipio == municipio)
    if vaga:
        query = query.filter(Candidato.vaga == vaga)

    # Data para tabela (limite para não estourar a página; podes paginar depois)
    linhas = query.order_by(Candidato.id.desc()).limit(500).all()

    # Dropdowns únicos
    municipios = [m[0] for m in db.session.query(Candidato.municipio).filter(Candidato.municipio.isnot(None)).distinct().order_by(Candidato.municipio.asc()).all()]
    vagas = [v[0] for v in db.session.query(Candidato.vaga).filter(Candidato.vaga.isnot(None)).distinct().order_by(Candidato.vaga.asc()).all()]

    return render_template(
        'candidaturas.html',
        linhas=linhas,
        municipios=municipios,
        vagas=vagas,
        filtro_municipio=municipio,
        filtro_vaga=vaga
    )

@rota_candidaturas.route('/candidaturas/data')
def candidaturas_data():
    if 'usuario_id' not in session:
        return jsonify({"erro": "não autenticado"}), 401

    municipio = request.args.get('municipio') or None
    vaga = request.args.get('vaga') or None

    base = Candidato.query
    if municipio:
        base = base.filter(Candidato.municipio == municipio)
    if vaga:
        base = base.filter(Candidato.vaga == vaga)

    total = base.count()
    completos = base.filter(Candidato.completo.is_(True)).count()
    incompletos = total - completos

    # freq por vaga
    por_vaga = db.session.query(Candidato.vaga, func.count(Candidato.id)).select_from(Candidato)
    if municipio:
        por_vaga = por_vaga.filter(Candidato.municipio == municipio)
    if vaga:
        por_vaga = por_vaga.filter(Candidato.vaga == vaga)
    por_vaga = por_vaga.group_by(Candidato.vaga).all()

    # freq por município
    por_mun = db.session.query(Candidato.municipio, func.count(Candidato.id)).select_from(Candidato)
    if municipio:
        por_mun = por_mun.filter(Candidato.municipio == municipio)
    if vaga:
        por_mun = por_mun.filter(Candidato.vaga == vaga)
    por_mun = por_mun.group_by(Candidato.municipio).all()

    return jsonify({
        "total": total,
        "completos": completos,
        "incompletos": incompletos,
        "por_vaga": [{"label": v[0] or "—", "valor": int(v[1])} for v in por_vaga],
        "por_municipio": [{"label": m[0] or "—", "valor": int(m[1])} for m in por_mun],
    })