from flask import Blueprint, render_template, request, redirect, url_for, flash
from baseDados.conexao import db
from modelos.dashboard_dados import DashboardDados
from datetime import datetime
import pandas as pd, os

rota_dashboard = Blueprint('rota_dashboard', __name__)

# -------------------- FUNÇÃO PARA FORMATAR NÚMEROS --------------------
def formatar_numero(valor, com_moeda=False):
    """Formata valores numéricos com pontos de milhar (e adiciona 'Kz' se necessário)."""
    try:
        valor = int(float(valor))
        numero = f"{valor:,}".replace(",", ".")
        return f"{numero} Kz" if com_moeda else numero
    except:
        return valor or "0"

# -------------------- DASHBOARD PRINCIPAL --------------------
@rota_dashboard.route("/dashboard")
def dashboard():
    dado = DashboardDados.query.order_by(DashboardDados.id.desc()).first()
    if not dado:
        flash("Nenhuma base de dados importada ainda.", "info")
        return render_template("dashboard.html", municipios=[], valores_municipios=[])

    return render_template("dashboard.html", **{
        "data_importacao": dado.data_importacao.strftime('%d/%m/%Y'),
        "utilizador": dado.utilizador or "Administrador Geral",
        "ip": dado.ip or "127.0.0.1",

        # ✅ Formatados com separadores
        "populacao_provincia": formatar_numero(dado.populacao_provincia),
        "orcamento_bie": formatar_numero(dado.orcamento_bie, com_moeda=True),
        "total_recebidos": formatar_numero(dado.total_recebidos),
        "total_distribuidos": formatar_numero(dado.total_distribuidos),
        "quantidade_mosquiteiros_distribuidos": formatar_numero(dado.quantidade_mosquiteiros_distribuidos),
        "agregados_estimados": formatar_numero(dado.agregados_estimados),
        "agregados_alcancados": formatar_numero(dado.agregados_alcancados),
        "populacao_beneficiada": formatar_numero(dado.populacao_beneficiada),
        "gravidas_beneficiadas": formatar_numero(dado.gravidas_beneficiadas),
        "criancas_beneficiadas": formatar_numero(dado.criancas_beneficiadas),

        "municipios": dado.municipios or [],
        "valores_municipios": dado.valores_municipios or []
    })

# -------------------- IMPORTAÇÃO --------------------
@rota_dashboard.route("/dashboard/importar", methods=["POST"])
def importar_bd():
    ficheiro = request.files.get("ficheiro")
    if not ficheiro:
        flash("Nenhum ficheiro enviado.", "warning")
        return redirect(url_for("rota_dashboard.dashboard"))

    # ⚠️ Verifica se já existe BD
    existente = DashboardDados.query.first()
    if existente:
        flash("⚠️ Já existe uma base de dados importada. Elimine antes de importar uma nova.", "danger")
        return redirect(url_for("rota_dashboard.dashboard"))

    caminho = os.path.join("instance", "uploads", ficheiro.filename)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    ficheiro.save(caminho)
    print(f"📂 Ficheiro recebido: {ficheiro.filename}")

    try:
        # Detectar tipo de ficheiro
        nome = ficheiro.filename.lower()
        if nome.endswith(".csv"):
            df = pd.read_csv(caminho, sep=";", encoding="utf-8", engine="python", on_bad_lines="skip")
        elif nome.endswith(".xlsx") or nome.endswith(".xls"):
            df = pd.read_excel(caminho, engine="openpyxl")
        elif nome.endswith(".ods"):
            df = pd.read_excel(caminho, engine="odf")
        else:
            flash("Formato de ficheiro não suportado. Use CSV, XLSX, XLS ou ODS.", "warning")
            return redirect(url_for("rota_dashboard.dashboard"))

        print("✅ Ficheiro lido com sucesso")
        print("📊 Colunas encontradas:", df.columns.tolist())
        print("🟢 Primeiras linhas:", df.head().to_dict())

        def limpar_texto(valor):
            import pandas as pd
            if pd.isna(valor):
                return "0"
            valor = str(valor).replace("AOA", "").replace("Kz", "").replace(",", "").replace(";", "").strip()
            return valor

        # Limpa colunas exceto 'municipios'
        for coluna in df.columns:
            if coluna.lower().strip() != "municipios":
                df[coluna] = df[coluna].apply(limpar_texto)

        print("✅ Dados limpos com sucesso")

        municipios = df["municipios"].astype(str).str.strip().tolist()
        valores = df["quantidade_mosquiteiros_distribuidos"].astype(float).fillna(0).tolist()

        dado = DashboardDados(
            data_importacao=datetime.utcnow(),
            utilizador="Administrador Geral",
            ip=request.remote_addr or "127.0.0.1",
            populacao_provincia=df["populacao_provincia"].iloc[0],
            orcamento_bie=df["orcamento_bie"].iloc[0],
            total_recebidos=df["total_recebidos"].iloc[0],
            total_distribuidos=df["total_distribuidos"].iloc[0],
            quantidade_mosquiteiros_distribuidos=str(sum(valores)),
            agregados_estimados=df["agregados_estimados"].iloc[0],
            agregados_alcancados=df["agregados_alcancados"].iloc[0],
            populacao_beneficiada=df["populacao_beneficiada"].iloc[0],
            gravidas_beneficiadas=df["gravidas_beneficiadas"].iloc[0],
            criancas_beneficiadas=df["criancas_beneficiadas"].iloc[0],
            municipios=municipios,
            valores_municipios=valores
        )

        db.session.add(dado)
        db.session.commit()
        print("💾 Dados gravados com sucesso no banco")
        flash("✅ Base de dados importada com sucesso!", "success")

    except Exception as e:
        print(f"❌ ERRO durante importação: {e}")
        flash(f"Ocorreu um erro durante a importação: {e}", "danger")

    return redirect(url_for("rota_dashboard.dashboard"))

# -------------------- ELIMINAR BASE DE DADOS --------------------
@rota_dashboard.route("/dashboard/eliminar", methods=["POST"])
def eliminar_bd():
    DashboardDados.query.delete()
    db.session.commit()
    flash("🗑️ Base de dados eliminada com sucesso.", "warning")
    return redirect(url_for("rota_dashboard.dashboard"))