from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "chave_super_secreta"  # obrigatória para usar sessões

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == 'marillson2025@' and password == '12345@':
            session['logado'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Credenciais erradas, por favor repetir.")
    return render_template('login.html')


@app.route('/index')
def index():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# rotas placeholder
@app.route('/candidaturas')
def candidaturas():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/candidatos_selecionados')
def candidatos_selecionados():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/pagamentos')
def pagamentos():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/registo_af')
def registo_af():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/configuracoes')
def configuracoes():
    if not session.get('logado'):
        return redirect(url_for('login'))
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)