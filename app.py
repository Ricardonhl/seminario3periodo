import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
# Importações para segurança
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)

# --- CONFIGURAÇÕES DE SEGURANÇA E PORTABILIDADE ---
app.config['SECRET_KEY'] = 'uma-chave-muito-segura-da-unitins' # Necessário para o login
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lixozero.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)

# --- CONFIGURAÇÃO DO FLASK-LOGIN ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Onde mandar quem tentar entrar sem logar

@login_manager.user_loader
def load_user(user_id):
    # Como teremos só 1 admin para o teste, retornamos ele
    return UsuarioAdmin()

# --- MODELOS DO BANCO DE DADOS ---

# 1. Modelo simples de Usuário para o Flask-Login (Kauan/Documentação)
class UsuarioAdmin(UserMixin):
    id = 1
    username = "unitins"
    password = "12345" # Em produção, isso deve ser criptografado!

# 2. Modelo das Denúncias (Lucas/Engenharia de Dados)
class Denuncia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    local = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    foto = db.Column(db.String(300))
    status = db.Column(db.String(20), default='Pendente')

with app.app_context():
    db.create_all()

# --- ROTAS PÚBLICAS (Sem proteção) ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/mapa')
def mapa():
    return render_template('mapa.html')

@app.route('/coletas')
def coletas():
    return render_template('coletas.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/contato')
def contato():
    return render_template('contato.html')

@app.route('/denunciar', methods=['GET', 'POST'])
def denunciar():
    if request.method == 'POST':
        local = request.form['local']
        desc = request.form['descricao']
        arquivo = request.files.get('foto')
        
        nome_da_foto = None
        if arquivo and arquivo.filename != '':
            nome_da_foto = secure_filename(arquivo.filename)
            arquivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nome_da_foto))

        nova_denuncia = Denuncia(local=local, descricao=desc, foto=nome_da_foto)
        db.session.add(nova_denuncia)
        db.session.commit()
        return redirect(url_for('home'))
    
    return render_template('denunciar.html')

# --- ROTAS DE AUTENTICAÇÃO ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        
        # Verificação simples para o seminário
        if user == 'unitins' and pwd == '12345':
            admin_user = UsuarioAdmin()
            login_user(admin_user)
            return redirect(url_for('admin'))
        else:
            flash('Usuário ou senha inválidos!', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- ROTA PROTEGIDA DA PREFEITURA (ADMIN) ---

@app.route('/admin')
@login_required # <-- ESTA LINHA TRANCA A PÁGINA
def admin():
    denuncias = Denuncia.query.all()
    # Adicionamos o nome do usuário logado na página
    return render_template('admin.html', denuncias=denuncias, usuario=current_user.username)

@app.route('/resolver/<int:id>')
@login_required
def resolver(id):
    denuncia = Denuncia.query.get(id)
    if denuncia:
        denuncia.status = 'Resolvido'
        db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)