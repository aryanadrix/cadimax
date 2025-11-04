from flask import Blueprint, render_template, request, send_from_directory, current_app, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from datetime import datetime
import os

from baseDados.conexao import db
from modelos.gestao_documento_modelo import GestaoDocumento

rota_documentos = Blueprint('rota_documentos', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@rota_documentos.route('/documentos', methods=['GET', 'POST'])
def documentos():
    base_dir = os.path.join(current_app.root_path, 'static', 'documentos')
    niveis = ['Nacional', 'Provincial', 'Municipal', 'Comunal']

    # 🔹 Upload
    if request.method == 'POST':
        categoria = request.form.get('categoria')
        nivel = request.form.get('nivel')
        municipio = request.form.get('municipio', '')
        ficheiro = request.files.get('ficheiro')

        if not categoria or not nivel or not ficheiro:
            session["novo_upload"] = True
            flash("Preencha todos os campos obrigatórios.", "warning")
            return redirect(url_for('rota_documentos.documentos'))

        if not allowed_file(ficheiro.filename):
            flash("Tipo de ficheiro não permitido (apenas PDF, DOCX, XLSX).", "danger")
            return redirect(url_for('rota_documentos.documentos'))

        nome_seguro = secure_filename(ficheiro.filename)
        pasta_destino = os.path.join(base_dir, nivel.lower(), categoria.lower().replace(" ", "_"))
        os.makedirs(pasta_destino, exist_ok=True)

        caminho_final = os.path.join(pasta_destino, nome_seguro)
        ficheiro.save(caminho_final)

        # Regista no banco
        doc = GestaoDocumento(
            nome=ficheiro.filename,
            categoria=categoria,
            nivel=nivel,
            municipio=municipio,
            caminho=f"documentos/{nivel.lower()}/{categoria.lower().replace(' ', '_')}/{nome_seguro}",
            criado_por=session.get('nome', 'Administrador'),
        )
        db.session.add(doc)
        db.session.commit()

        flash(f"Documento '{ficheiro.filename}' carregado com sucesso!", "success")
        return redirect(url_for('rota_documentos.documentos'))

    # 🔹 Filtros de pesquisa
    termo = request.args.get('q', '')
    filtro_categoria = request.args.get('categoria', '')
    filtro_nivel = request.args.get('nivel', '')

    query = GestaoDocumento.query
    if termo:
        query = query.filter(GestaoDocumento.nome.ilike(f"%{termo}%"))
    if filtro_categoria:
        query = query.filter_by(categoria=filtro_categoria)
    if filtro_nivel:
        query = query.filter_by(nivel=filtro_nivel)

    documentos = query.order_by(GestaoDocumento.data_upload.desc()).all()

    # 🔹 Contagem de documentos por categoria
    todas_categorias = ["Instrumentos de Avaliação", "Planos e Atas", "Listas de Presença", "Relatórios", "Outros"]
    contagens = {cat: GestaoDocumento.query.filter_by(categoria=cat).count() for cat in todas_categorias}

    # 🔹 Detecta se há novo upload (usando flash temporário de sessão)
    novo_upload = session.pop("novo_upload", False)

    return render_template(
        "gest_documentos.html",
        documentos=documentos,
        niveis=niveis,
        termo=termo,
        contagens=contagens,
        novo_upload=novo_upload
    )





# 🔹 VISUALIZAR documento
@rota_documentos.route('/documentos/ver/<path:filename>')
def ver_documento(filename):
    """
    Exibe o documento diretamente no navegador (PDFs, DOCX, etc.)
    """
    base_dir = os.path.join(current_app.root_path, 'static', 'documentos')
    ficheiro_path = os.path.join(base_dir, filename)

    if not os.path.exists(ficheiro_path):
        flash("Ficheiro não encontrado no servidor.", "danger")
        return redirect(url_for('rota_documentos.documentos'))

    # separa diretório do nome
    pasta = os.path.dirname(filename)
    nome_ficheiro = os.path.basename(filename)

    return send_from_directory(
        directory=os.path.join(base_dir, pasta),
        path=nome_ficheiro,
        as_attachment=False
    )


# 🔹 DOWNLOAD documento
@rota_documentos.route('/documentos/download/<path:filename>')
def download_documento(filename):
    """
    Faz o download direto do documento selecionado
    """
    base_dir = os.path.join(current_app.root_path, 'static', 'documentos')
    ficheiro_path = os.path.join(base_dir, filename)

    if not os.path.exists(ficheiro_path):
        flash("Ficheiro não encontrado no servidor.", "danger")
        return redirect(url_for('rota_documentos.documentos'))

    pasta = os.path.dirname(filename)
    nome_ficheiro = os.path.basename(filename)

    return send_from_directory(
        directory=os.path.join(base_dir, pasta),
        path=nome_ficheiro,
        as_attachment=True
    )

# 🔹 APAGAR documento
@rota_documentos.route('/documentos/apagar/<int:id>', methods=['POST'])
def apagar_documento(id):
    """
    Remove o documento do banco de dados e apaga o ficheiro físico.
    """
    doc = GestaoDocumento.query.get_or_404(id)

    # Caminho absoluto do ficheiro
    base_dir = os.path.join(current_app.root_path, 'static')
    caminho_ficheiro = os.path.join(base_dir, doc.caminho)

    # Apaga o ficheiro físico se existir
    if os.path.exists(caminho_ficheiro):
        os.remove(caminho_ficheiro)

    # Remove o registo do banco
    db.session.delete(doc)
    db.session.commit()

    flash(f"🗑️ Documento '{doc.nome}' removido com sucesso!", "success")
    return redirect(url_for('rota_documentos.documentos'))