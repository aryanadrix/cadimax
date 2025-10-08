# rotas/config_rotas.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_from_directory
from modelos.importacao_modelo import ImportacaoDB
from modelos.documento_modelo import Documento
from modelos.candidato_modelo import Candidato
from baseDados.conexao import db
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import unicodedata
from modelos.utilizador_modelo import Utilizador
from werkzeug.security import generate_password_hash
import pandas as pd


rota_config = Blueprint('rota_config', __name__)

# Pastas (dentro de /static/uploads)
BASES_DIR = os.path.join('static', 'uploads', 'bases')
DOCS_DIR = os.path.join('static', 'uploads', 'docs')
CONFIG_DIR = os.path.join('static', 'config')
CORES_FILE = os.path.join(CONFIG_DIR, 'cores.json')

ALLOWED_DB_EXT = {'xlsx', 'csv', 'ods'}
MAX_PDF_MB = 11


def _garante_pastas():
    os.makedirs(BASES_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _get_ip():
    return request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)


def _user_nome():
    return session.get('nome', 'Desconhecido')


# -------------------- Personalização (cores) --------------------
def obter_cores():
    if not os.path.exists(CORES_FILE):
        return {"navbar": "#fb6e2b", "footer": "#fb6e2b"}
    with open(CORES_FILE, 'r') as f:
        return json.load(f)


def guardar_cores_json(novas):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CORES_FILE, 'w') as f:
        json.dump(novas, f)


# -------------------- Normalização de nomes --------------------
def _slug(s: str) -> str:
    """minúsculas, sem acentos, apenas [a-z0-9_]"""
    s = s.strip().lower()
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )
    out = []
    for ch in s:
        if ch.isalnum():
            out.append(ch)
        elif ch in [' ', '-', '.', '/', '\\']:
            out.append('_')
    return ''.join(out)


# Mapa de sinónimos -> campo alvo
SINONIMOS = {
    'nome': 'nome', 'nome_completo': 'nome', 'candidato': 'nome', 'beneficiario': 'nome',
    'municipio': 'municipio', 'município': 'municipio', 'munic': 'municipio', 'cidade': 'municipio',
    'comuna': 'comuna', 'bairro': 'comuna', 'localidade': 'comuna',
    'vaga': 'vaga', 'funcao': 'vaga', 'função': 'vaga', 'cargo': 'vaga', 'posicao': 'vaga', 'posição': 'vaga',
    'documentos': 'documentos', 'docs': 'documentos', 'anexos': 'documentos',
    'completo': 'completo', 'completou': 'completo', 'entrega_completa': 'completo', 'docs_completos': 'completo'
}


def _mapear_colunas(cols):
    normalizados = [_slug(c) for c in cols]
    mapa = {}
    for i, n in enumerate(normalizados):
        alvo = SINONIMOS.get(n)
        if not alvo:
            for k, v in SINONIMOS.items():
                if n.startswith(k):
                    alvo = v
                    break
        mapa[i] = alvo
    return mapa, normalizados


def _to_bool(val):
    if val is None:
        return False
    s = str(val).strip().lower()
    return s in {'1', 'true', 't', 'sim', 'yes', 'y', 'ok', 'completo', 'completa'}


# -------------------- Processamento do ficheiro de candidatos --------------------
def processar_candidatos(caminho_ficheiro: str, titulo: str):
    ext = caminho_ficheiro.rsplit('.', 1)[-1].lower()

    if ext == 'xlsx':
        df = pd.read_excel(caminho_ficheiro, engine='openpyxl')
    elif ext == 'csv':
        try:
            df = pd.read_csv(caminho_ficheiro)
        except Exception:
            df = pd.read_csv(caminho_ficheiro, sep=';')
    elif ext == 'ods':
        try:
            df = pd.read_excel(caminho_ficheiro, engine='odf')
        except Exception as e:
            raise RuntimeError("Para .ods, por favor instale o pacote 'odfpy'. Erro: " + str(e))
    else:
        raise RuntimeError("Extensão não suportada para processamento.")

    if df.empty:
        db.session.query(Candidato).delete()
        db.session.commit()
        return

    mapa, normalizados = _mapear_colunas(list(df.columns))
    db.session.query(Candidato).delete()
    db.session.commit()

    registos = []
    for _, row in df.iterrows():
        dados_raw = {}
        nome = municipio = comuna = vaga = documentos = None
        completo = False

        for idx, col in enumerate(df.columns):
            val = row[col]
            alvo = mapa[idx]

            if alvo is None:
                dados_raw[normalizados[idx]] = None if pd.isna(val) else str(val)
            else:
                if alvo == 'nome':
                    nome = None if pd.isna(val) else str(val)
                elif alvo == 'municipio':
                    municipio = None if pd.isna(val) else str(val)
                elif alvo == 'comuna':
                    comuna = None if pd.isna(val) else str(val)
                elif alvo == 'vaga':
                    vaga = None if pd.isna(val) else str(val)
                elif alvo == 'documentos':
                    documentos = None if pd.isna(val) else str(val)
                elif alvo == 'completo':
                    completo = _to_bool(val)

        # -------- Lógica reforçada: completo se tiver BI + CV + NIB/IBAN --------
        texto_todo = " ".join([
            str(val).lower() for val in row.values if pd.notna(val)
        ])
        tem_bi = any(x in texto_todo for x in ['bi', 'bilhete'])
        tem_cv = any(x in texto_todo for x in ['cv', 'curriculum'])
        tem_nib = any(x in texto_todo for x in ['nib', 'iban'])
        if tem_bi and tem_cv and tem_nib:
            completo = True
        # ------------------------------------------------------------------------

        registos.append(Candidato(
            nome=nome,
            municipio=municipio,
            comuna=comuna,
            vaga=vaga,
            documentos=documentos,
            completo=completo,
            fonte_titulo=titulo,
            raw=dados_raw
        ))

    if registos:
        db.session.bulk_save_objects(registos)
        db.session.commit()


# -------------------- Páginas --------------------
@rota_config.route('/configuracoes')
def configuracoes():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    _garante_pastas()

    importacoes = ImportacaoDB.query.order_by(ImportacaoDB.data_hora.desc()).limit(10).all()
    documentos = Documento.query.order_by(Documento.data_hora.desc()).all()
    utilizadores = Utilizador.query.order_by(Utilizador.id.desc()).all()
    cores = obter_cores()

    return render_template(
        'configuracoes.html',
        importacoes=importacoes,
        documentos=documentos,
        utilizadores=utilizadores,
        cores=cores
    )


# ------------ BASE DE DADOS ------------
@rota_config.route('/importar_db', methods=['POST'])
def importar_db():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    titulo = request.form.get('titulo', '').strip()
    ficheiro = request.files.get('ficheiro')

    if not titulo or not ficheiro:
        flash("Preencha o título e selecione um ficheiro.", "danger")
        return redirect(url_for('rota_config.configuracoes'))

    ext = ficheiro.filename.rsplit('.', 1)[-1].lower() if '.' in ficheiro.filename else ''
    if ext not in ALLOWED_DB_EXT:
        flash("Formato inválido! Aceites: .xlsx, .csv, .ods", "danger")
        return redirect(url_for('rota_config.configuracoes'))

    _garante_pastas()
    nome_seguro = secure_filename(ficheiro.filename)
    caminho = os.path.join(BASES_DIR, nome_seguro)
    ficheiro.save(caminho)

    reg = ImportacaoDB(
        titulo=titulo,
        ficheiro=nome_seguro,
        usuario=_user_nome(),
        ip=_get_ip()
    )
    db.session.add(reg)
    db.session.commit()

    ids_mantidos = [i.id for i in ImportacaoDB.query.order_by(ImportacaoDB.data_hora.desc()).limit(10).all()]
    if ids_mantidos:
        antigos = ImportacaoDB.query.filter(~ImportacaoDB.id.in_(ids_mantidos)).all()
        for ant in antigos:
            try:
                os.remove(os.path.join(BASES_DIR, ant.ficheiro))
            except Exception:
                pass
            db.session.delete(ant)
        db.session.commit()

    try:
        processar_candidatos(caminho, titulo)
        flash("✅ Base importada e candidatos atualizados!", "success")
    except Exception as e:
        flash(f"⚠️ Importado o ficheiro, mas falhou o processamento dos candidatos: {e}", "warning")

    return redirect(url_for('rota_config.configuracoes'))


@rota_config.route('/download_base/<int:import_id>')
def download_base(import_id):
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))
    reg = ImportacaoDB.query.get_or_404(import_id)
    return send_from_directory(BASES_DIR, reg.ficheiro, as_attachment=True)


@rota_config.route('/apagar_importacao/<int:import_id>', methods=['POST'])
def apagar_importacao(import_id):
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))
    reg = ImportacaoDB.query.get_or_404(import_id)
    try:
        os.remove(os.path.join(BASES_DIR, reg.ficheiro))
    except Exception:
        pass
    db.session.delete(reg)
    db.session.commit()
    flash("🗑️ Importação removida.", "info")
    return redirect(url_for('rota_config.configuracoes'))


# ------------ DOCUMENTOS (PDF) ------------
@rota_config.route('/upload_doc', methods=['POST'])
def upload_doc():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    titulo = request.form.get('titulo_doc', '').strip()
    ficheiro = request.files.get('ficheiro_doc')

    if not titulo or not ficheiro:
        flash("Preencha o título e selecione um PDF.", "danger")
        return redirect(url_for('rota_config.configuracoes'))

    ext = ficheiro.filename.rsplit('.', 1)[-1].lower() if '.' in ficheiro.filename else ''
    if ext != 'pdf':
        flash("Apenas ficheiros PDF são permitidos.", "danger")
        return redirect(url_for('rota_config.configuracoes'))

    ficheiro.seek(0, os.SEEK_END)
    tamanho_mb = ficheiro.tell() / (1024 * 1024)
    ficheiro.seek(0)
    if tamanho_mb > MAX_PDF_MB:
        flash("PDF excede 11MB.", "danger")
        return redirect(url_for('rota_config.configuracoes'))

    _garante_pastas()
    nome_seguro = secure_filename(ficheiro.filename)
    caminho = os.path.join(DOCS_DIR, nome_seguro)
    ficheiro.save(caminho)

    reg = Documento(
        titulo=titulo,
        ficheiro=nome_seguro,
        usuario=_user_nome(),
        ip=_get_ip()
    )
    db.session.add(reg)
    db.session.commit()

    flash("✅ Upload feito com sucesso!", "success")
    return redirect(url_for('rota_config.configuracoes'))


@rota_config.route('/ver_doc/<int:doc_id>')
def ver_doc(doc_id):
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))
    reg = Documento.query.get_or_404(doc_id)
    return send_from_directory(DOCS_DIR, reg.ficheiro, as_attachment=False)


@rota_config.route('/apagar_doc/<int:doc_id>', methods=['POST'])
def apagar_doc(doc_id):
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))
    reg = Documento.query.get_or_404(doc_id)
    try:
        os.remove(os.path.join(DOCS_DIR, reg.ficheiro))
    except Exception:
        pass
    db.session.delete(reg)
    db.session.commit()
    flash("🗑️ Documento removido.", "info")
    return redirect(url_for('rota_config.configuracoes'))


# ------------ Guardar e obter cores ------------
@rota_config.route('/guardar_cores', methods=['POST'])
def guardar_cores_rota():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    cor_global = request.form.get('cor_global') or "#fb6e2b"

    guardar_cores_json({
        "navbar": cor_global,
        "footer": cor_global,
        "botoes": cor_global,
        "graficos": cor_global
    })

    flash("🎨 Tema atualizado com sucesso!", "success")
    return redirect(url_for('rota_config.configuracoes'))


# -------------------- UTILIZADORES --------------------
@rota_config.route('/criar_utilizador', methods=['POST'])
def criar_utilizador():
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    nome = request.form.get('nome')
    username = request.form.get('username')
    senha = request.form.get('senha')

    if not nome or not username or not senha:
        flash("Preencha todos os campos.", "danger")
        return redirect(url_for('rota_config.configuracoes'))

    if Utilizador.query.filter_by(username=username).first():
        flash("Já existe um utilizador com esse nome de utilizador.", "warning")
        return redirect(url_for('rota_config.configuracoes'))

    novo = Utilizador(
        nome=nome,
        username=username,
        senha=generate_password_hash(senha)
    )
    db.session.add(novo)
    db.session.commit()

    flash("✅ Utilizador criado com sucesso!", "success")
    return redirect(url_for('rota_config.configuracoes'))


@rota_config.route('/apagar_utilizador/<int:id>', methods=['POST'])
def apagar_utilizador(id):
    if 'usuario_id' not in session:
        return redirect(url_for('rota_login.login'))

    user = Utilizador.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    flash("🗑️ Utilizador removido.", "info")
    return redirect(url_for('rota_config.configuracoes'))