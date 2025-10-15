from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
import os, pandas as pd, unicodedata, re
from datetime import datetime
from baseDados.conexao import db
from modelos.pag_formacoes import PagamentoFormacao, HistoricoFormacao
from modelos.pag_dias_trabalho import PagamentoDiaTrabalho, HistoricoDiasTrabalho

rota_pagamentos = Blueprint('rota_pagamentos', __name__)

UPLOAD_FORMACOES = os.path.join('static', 'uploads', 'formacoes')
UPLOAD_DIAS = os.path.join('static', 'uploads', 'dias_trabalho')
os.makedirs(UPLOAD_FORMACOES, exist_ok=True)
os.makedirs(UPLOAD_DIAS, exist_ok=True)

# ------------ utils ------------
def _norm(s: str) -> str:
    if not isinstance(s, str):
        return s
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    return s.strip().lower().replace(' ', '_')

def _read_df(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.csv':
        try:
            return pd.read_csv(path, sep=None, engine='python', encoding='utf-8')
        except Exception:
            return pd.read_csv(path, sep=None, engine='python', encoding='latin1')
    elif ext == '.xlsx':
        return pd.read_excel(path)
    elif ext == '.ods':
        return pd.read_excel(path, engine='odf')
    else:
        raise ValueError('Formato inválido (use .csv, .xlsx ou .ods)')

def _match(df_cols, *palavras):
    for c in df_cols:
        if any(p in c for p in palavras):
            return c
    return None

def _pick(df_cols, exact_first: list[str], contains_after: list[str] = None):
    contains_after = contains_after or []
    for c in df_cols:
        if c in exact_first:
            return c
    for c in df_cols:
        if any(p in c for p in contains_after):
            return c
    return None

_num_regex = re.compile(r'[^0-9,.\-]')
def to_num(value) -> float:
    if value is None:
        return 0.0
    s = str(value).strip()
    if not s:
        return 0.0
    s = _num_regex.sub('', s)
    if ',' in s and '.' not in s:
        s = s.replace(',', '.')
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    try:
        return float(s)
    except Exception:
        return 0.0

# ------------ página ------------
@rota_pagamentos.route('/pagamentos', methods=['GET'])
def pagamentos():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    aba_ativa = request.args.get('aba', 'formacoes')

    # --- Bases ---
    formadores = PagamentoFormacao.query.all()
    trabalhadores = PagamentoDiaTrabalho.query.all()

    # --- Históricos ---
    historico_formacoes = HistoricoFormacao.query.order_by(HistoricoFormacao.data.desc()).limit(1).all()
    historico_dias = HistoricoDiasTrabalho.query.order_by(HistoricoDiasTrabalho.data.desc()).limit(1).all()

    # ✅ Cada aba agora tem o seu filtro independente
    municipios_formacoes = sorted({f.municipio for f in formadores if f.municipio})
    categorias_formacoes = sorted({f.categoria for f in formadores if getattr(f, 'categoria', None)})

    municipios_dias = sorted({t.municipio for t in trabalhadores if t.municipio})
    categorias_dias = sorted({t.categoria for t in trabalhadores if getattr(t, 'categoria', None)})

    return render_template(
        'pagamentos.html',
        formadores=formadores,
        trabalhadores=trabalhadores,
        historico_formacoes=historico_formacoes,
        historico_dias=historico_dias,
        municipios_formacoes=municipios_formacoes,
        categorias_formacoes=categorias_formacoes,
        municipios_dias=municipios_dias,
        categorias_dias=categorias_dias,
        aba_ativa=aba_ativa
    )

# ------------ importações ------------
@rota_pagamentos.route('/importar_formacoes', methods=['POST'])
def importar_formacoes():
    ficheiro = request.files.get('ficheiro')
    titulo = request.form.get('titulo') or 'Formações'
    if not ficheiro:
        flash('Selecione um ficheiro.', 'warning')
        return redirect(url_for('rota_pagamentos.pagamentos', aba='formacoes'))

    path = os.path.join(UPLOAD_FORMACOES, secure_filename(ficheiro.filename))
    ficheiro.save(path)
    try:
        df = _read_df(path)
    except Exception as e:
        flash(f'Erro ao ler ficheiro: {e}', 'danger')
        return redirect(url_for('rota_pagamentos.pagamentos', aba='formacoes'))

    df.columns = [_norm(c) for c in df.columns]

    col_contrl = _pick(df.columns, ['nome'], ['nome'])
    col_comun = _pick(df.columns, ['comuna'], ['comuna'])
    col_tel = _pick(df.columns, ['telefone'], ['telefone'])
    col_bi = _pick(df.columns, ['bi'], ['bi'])
    col_iban = _pick(df.columns, ['iban'], ['iban'])

    col_nome = _pick(df.columns, ['nome'], ['nome'])
    col_mun  = _pick(df.columns, ['municipio'], ['municip'])
    col_cat  = _pick(df.columns, ['categoria'], ['categoria','funcao','funca','func'])
    col_val  = _pick(df.columns, ['valor_trans'], ['valor_trans','valor'])
    col_dias = _pick(df.columns, ['numdias'], ['dias','numdias'])



    if not all([col_nome, col_mun, col_cat, col_val, col_dias]):
        flash('Colunas esperadas não encontradas (nome, município, categoria, valor_trans, numDias).', 'danger')
        return redirect(url_for('rota_pagamentos.pagamentos', aba='formacoes'))

    HistoricoFormacao.query.delete()
    db.session.commit()
    db.session.add(HistoricoFormacao(
        titulo=titulo, data=datetime.now(),
        utilizador=session.get('nome', 'Administrador Geral'),
        ip=request.remote_addr
    ))

    PagamentoFormacao.query.delete()

    df = df.fillna("").replace({"nan": "", "NaN": ""}, regex=True)

    for _, r in df.iterrows():
        valor = to_num(r[col_val])
        dias  = to_num(r[col_dias])
        reg = PagamentoFormacao(




            num_de_control_formacoes=str(r[col_contrl]).strip() if col_contrl else "",
            nome=str(r[col_nome]).strip(),
            categoria=str(r[col_cat]).strip(),
            municipio=str(r[col_mun]).strip(),
            comuna=str(r[col_comun]).strip() if col_comun else "",
            telefone_formacoes=str(r[col_tel]).strip() if col_tel else "",
            numero_bi_formacoes=str(r[col_bi]).strip() if col_bi else "",
            iban_formacoes=str(r[col_iban]).strip() if col_iban else "",
            valor_trans=valor,
            numDias=dias,
            total_receber=valor * dias







        )
        db.session.add(reg)

    db.session.commit()
    flash('✅ Base de Formações importada com sucesso!', 'success')
    return redirect(url_for('rota_pagamentos.pagamentos', aba='formacoes'))

@rota_pagamentos.route('/importar_dias', methods=['POST'])
def importar_dias():
    ficheiro = request.files.get('ficheiro')
    titulo = request.form.get('titulo') or 'Dias de Trabalho'
    if not ficheiro:
        flash('Selecione um ficheiro.', 'warning')
        return redirect(url_for('rota_pagamentos.pagamentos', aba='dias'))

    path = os.path.join(UPLOAD_DIAS, secure_filename(ficheiro.filename))
    ficheiro.save(path)
    try:
        df = _read_df(path)
    except Exception as e:
        flash(f'Erro ao ler ficheiro: {e}', 'danger')
        return redirect(url_for('rota_pagamentos.pagamentos', aba='dias'))

    df.columns = [_norm(c) for c in df.columns]

    col_id = _pick(df.columns, ['id'], ['id'])
    col_nome = _pick(df.columns, ['nome'], ['nome'])
    col_bi = _pick(df.columns, ['num_bi'], ['num_bi'])
    col_tel = _pick(df.columns, ['telefone'], ['telefone'])
    col_mun  = _pick(df.columns, ['municipio'], ['municip'])
    col_ibn = _pick(df.columns, ['iban'], ['iban'])
    col_dati = _pick(df.columns, ['data_inicio'], ['data_inicio'])
    col_datf = _pick(df.columns, ['data_fim'], ['data_fim'])
    col_cat  = _pick(df.columns, ['categoria'], ['categoria','funcao','funca','func'])
    col_val  = _pick(df.columns, ['valor_trans'], ['valor_trans','valor'])
    col_dias = _pick(df.columns, ['numdias'], ['dias','numdias'])


    if not all([col_nome, col_mun, col_cat, col_val, col_dias]):
        flash('Colunas esperadas não encontradas (nome, município, categoria, valor_trans, numDias).', 'danger')
        return redirect(url_for('rota_pagamentos.pagamentos', aba='dias'))

    HistoricoDiasTrabalho.query.delete()
    db.session.commit()
    db.session.add(HistoricoDiasTrabalho(
        titulo=titulo,
        data=datetime.now(),
        utilizador=session.get('nome', 'Administrador Geral'),
        ip=request.remote_addr
    ))

    PagamentoDiaTrabalho.query.delete()

    df = df.fillna("").replace({"nan": "", "NaN": ""}, regex=True)

    def _map_status(v):
        if v is None:
            return "NÃO PAGO"
        s = str(v).strip().upper()
        if s in {"SIM", "PAGO", "YES", "1"}:
            return "PAGO"
        return "NÃO PAGO"

    for _, r in df.iterrows():
        if not str(r.get(col_nome, '')).strip():
            continue
        try:
            valor = to_num(r.get(col_val))
            dias  = to_num(r.get(col_dias))
            reg = PagamentoDiaTrabalho(

                nome=str(r[col_nome]).strip(),
                num_bi=str(r[col_bi]).strip() if col_bi else "",
                telefone=str(r[col_tel]).strip() if col_tel else "",
                municipio=str(r[col_mun]).strip(),
                iban=str(r[col_ibn]).strip() if col_ibn else "",
                data_inicio=str(r[col_dati]).strip() if col_dati else "",
                data_fim=str(r[col_datf]).strip() if col_datf else "",
                categoria=str(r[col_cat]).strip() if col_cat else "",
                valor_trans=valor,
                numDias=dias,
                total_receber=valor * dias
            )
            db.session.add(reg)
        except Exception as e:
            print(f"[ERRO AO INSERIR LINHA]: {e} -> {r.to_dict()}")
            continue

    db.session.commit()
    flash('✅ Base de Dias de Trabalho importada com sucesso!', 'success')
    return redirect(url_for('rota_pagamentos.pagamentos', aba='dias'))

# ------------ eliminar histórico ------------
@rota_pagamentos.route('/eliminar_historico_formacoes/<int:hid>', methods=['POST'])
def eliminar_historico_formacoes(hid):
    hist = HistoricoFormacao.query.get(hid)
    if hist:
        db.session.delete(hist)
    PagamentoFormacao.query.delete()
    db.session.commit()
    flash('🗑️ Histórico/Formações eliminados.', 'success')
    return redirect(url_for('rota_pagamentos.pagamentos', aba='formacoes'))

@rota_pagamentos.route('/eliminar_historico_dias/<int:hid>', methods=['POST'])
def eliminar_historico_dias(hid):
    hist = HistoricoDiasTrabalho.query.get(hid)
    if hist:
        db.session.delete(hist)
    PagamentoDiaTrabalho.query.delete()
    db.session.commit()
    flash('🗑️ Histórico/Dias eliminados.', 'success')
    return redirect(url_for('rota_pagamentos.pagamentos', aba='dias'))

# ------------ APIs de filtro (município & categoria) ------------
@rota_pagamentos.route('/api/pagamentos/<tipo>')
def api_pagamentos(tipo):
    mun  = request.args.get('municipio', 'todos')
    cat  = request.args.get('categoria', 'todas')

    if tipo == 'formacoes':
        q = PagamentoFormacao.query
        if mun.lower() != 'todos':
            q = q.filter_by(municipio=mun)
        if cat.lower() != 'todas':
            q = q.filter_by(categoria=cat)

        dados = [{
            'id': x.id,
            'num_de_control_formacoes': x.num_de_control_formacoes,
            'nome': x.nome,
            'categoria': x.categoria,
            'municipio': x.municipio,
            'comuna': x.comuna,
            'telefone_formacoes': x.telefone_formacoes,
            'numero_bi_formacoes': x.numero_bi_formacoes,
            'iban_formacoes': x.iban_formacoes,
            'valor_trans': x.valor_trans,
            'numDias': x.numDias,
            'total_receber': x.total_receber

        } for x in q.all()]
    else:
        q = PagamentoDiaTrabalho.query
        if mun.lower() != 'todos':
            q = q.filter_by(municipio=mun)
        # ✅ também permite filtrar por categoria nos DIAS
        if cat.lower() != 'todas':
            q = q.filter_by(categoria=cat)

        # ✅ devolver categoria e valor_trans (eram os que faltavam)
        dados = [{
            'id': x.id,
            'nome': x.nome,
            'num_bi':x.num_bi,
            'telefone':x.telefone,
            'municipio': x.municipio,
            'iban':x.iban,
            'data_inicio':x.data_inicio,
            'data_fim':x.data_fim,
            'categoria': x.categoria,
            'valor_trans': x.valor_trans,
            'numDias': x.numDias,
            'total_receber': x.total_receber,

        } for x in q.all()]

    total = len(dados)
    verba = sum(float(d['total_receber'] or 0) for d in dados)
    media = round(sum(float(d.get('numDias') or 0) for d in dados) / total, 1) if total else 0.0
    return jsonify({'items': dados, 'total': total, 'verba': verba, 'media': media})