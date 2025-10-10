from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
import os
import pandas as pd
from datetime import datetime
from baseDados.conexao import db
from modelos.candidato_selecionado import CandidatoSelecionado, HistoricoImportacao

rota_candidatos_selecionados = Blueprint('rota_candidatos_selecionados', __name__)

UPLOAD_FOLDER = os.path.join('static', 'uploads', 'selecionados')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@rota_candidatos_selecionados.route('/candidatos_selecionados', methods=['GET', 'POST'])
def candidatos_selecionados():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    # 📤 IMPORTAÇÃO
    if request.method == 'POST':
        titulo = request.form.get('titulo')
        ficheiro = request.files.get('ficheiro')

        if not ficheiro:
            flash('⚠️ Selecione um ficheiro para importar.', 'warning')
            return redirect(url_for('rota_candidatos_selecionados.candidatos_selecionados'))

        filename = secure_filename(ficheiro.filename)
        caminho = os.path.join(UPLOAD_FOLDER, filename)
        ficheiro.save(caminho)

        # Detectar formato
        try:
            if filename.endswith('.csv'):
                df = pd.read_csv(caminho, sep=';', encoding='utf-8')
            elif filename.endswith('.xlsx'):
                df = pd.read_excel(caminho)
            elif filename.endswith('.ods'):
                df = pd.read_excel(caminho, engine='odf')
            else:
                flash('❌ Formato inválido. Use CSV, XLSX ou ODS.', 'danger')
                return redirect(url_for('rota_candidatos_selecionados.candidatos_selecionados'))
        except Exception as e:
            flash(f'❌ Erro ao ler ficheiro: {e}', 'danger')
            return redirect(url_for('rota_candidatos_selecionados.candidatos_selecionados'))

        if df.empty:
            flash('⚠️ O ficheiro está vazio.', 'warning')
            return redirect(url_for('rota_candidatos_selecionados.candidatos_selecionados'))

        # Normalizar colunas
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        df = df.rename(columns={
            'município': 'municipio',
            'nome_completo': 'nome',
            'vaga_aplicada': 'vaga'
        })
        if 'n' in df.columns:
            df = df.drop(columns=['n'])

        required_cols = ['nome', 'vaga', 'municipio', 'comuna', 'resultado']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            flash(f'❌ Colunas ausentes: {", ".join(missing)}', 'danger')
            return redirect(url_for('rota_candidatos_selecionados.candidatos_selecionados'))

        # Guardar histórico
        historico = HistoricoImportacao(
            titulo=titulo or f'Importação {datetime.now().strftime("%d/%m/%Y %H:%M")}',
            data=datetime.now(),
            utilizador=session.get('nome'),
            ip=request.remote_addr
        )
        db.session.add(historico)
        db.session.commit()

        # Substitui base atual
        CandidatoSelecionado.query.delete()
        db.session.commit()

        # Inserir nova base
        total_importados = 0
        for _, row in df.iterrows():
            novo = CandidatoSelecionado(
                nome=str(row['nome']),
                vaga=str(row['vaga']),
                municipio=str(row['municipio']),
                comuna=str(row['comuna']),
                resultado=str(row['resultado'])
            )
            db.session.add(novo)
            total_importados += 1

        db.session.commit()
        flash(f'✅ {total_importados} candidatos importados com sucesso!', 'success')
        return redirect(url_for('rota_candidatos_selecionados.candidatos_selecionados'))

    # 📊 VISUALIZAÇÃO E FILTRO
    filtro_municipio = request.args.get('municipio', '').strip()
    filtro_vaga = request.args.get('vaga', '').strip()

    # Obter todos municípios e vagas únicos para os dropdowns
    municipios_disponiveis = sorted(list({c.municipio for c in CandidatoSelecionado.query.all()}))
    vagas_disponiveis = sorted(list({c.vaga for c in CandidatoSelecionado.query.all()}))

    query = CandidatoSelecionado.query
    if filtro_municipio:
        query = query.filter(CandidatoSelecionado.municipio == filtro_municipio)
    if filtro_vaga:
        query = query.filter(CandidatoSelecionado.vaga == filtro_vaga)

    candidatos = query.all()
    historico = HistoricoImportacao.query.order_by(HistoricoImportacao.data.desc()).limit(10).all()

    contagem_municipio = {}
    contagem_vaga = {}
    for c in candidatos:
        contagem_municipio[c.municipio] = contagem_municipio.get(c.municipio, 0) + 1
        contagem_vaga[c.vaga] = contagem_vaga.get(c.vaga, 0) + 1

    return render_template(
        'candidatos_selecionados.html',
        candidatos=candidatos,
        historico=historico,
        total=len(candidatos),
        filtro_municipio=filtro_municipio,
        filtro_vaga=filtro_vaga,
        municipios_disponiveis=municipios_disponiveis,
        vagas_disponiveis=vagas_disponiveis,
        municipios=list(contagem_municipio.keys()),
        vagas=list(contagem_vaga.keys()),
        dados_municipio=list(contagem_municipio.values()),
        dados_vaga=list(contagem_vaga.values())
    )