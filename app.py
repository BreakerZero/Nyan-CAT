from operator import truediv
import os
from enum import unique
from re import template
from flask import Flask, request, jsonify, render_template, redirect, sessions, url_for, flash, abort, Blueprint, \
    Response
import flask_login
from sqlalchemy.sql.elements import Null
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import flask_sqlalchemy
from werkzeug.datastructures import auth_property
from werkzeug.utils import redirect, secure_filename
from translateAPI import TranslatorAPI
from flask_login import UserMixin, LoginManager, login_user, current_user, login_required, logout_user
from flask_dropzone import Dropzone

app = Flask(__name__)
app.config['DROPZONE_REDIRECT_VIEW'] = "home"
app.config['DROPZONE_DEFAULT_MESSAGE'] = "Déposez vos fichiers ici (faites un glisser-deposer ou cliquez pour ouvrir)"
app.config['DROPZONE_ALLOWED_FILE_CUSTOM'] = True
app.config['DROPZONE_ALLOWED_FILE_TYPE'] = '.png, .jpg, .jpeg, .pdf, .docx, .doc, .odt,.txt'
app.config['DROPZONE_INVALID_FILE_TYPE'] = "L'extension de ce fichier de correspond pas avec votre précédente sélection"
app.config['DROPZONE_UPLOAD_MULTIPLE'] = True
translator = TranslatorAPI('./translatemodel/')  # chemin vers les modèles
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database//nyan.db'  # Nom de la bdd
app.config['SECRET_KEY'] = '9df31cd3eb2f6f6386571da69d6b418e'  # Clé random pour autentification
app.config['UPLOAD_FOLDER'] = "fileproject"
app.config['UPLOAD_EXTENSIONS'] = ['.png', '.jpg', '.jpeg', '.pdf', '.docx', '.doc', '.odt',
                                   '.txt']  # extensions autorisées
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 50  # max 50Mo
db = flask_sqlalchemy.SQLAlchemy(app)  # lien bdd
app.config["DEBUG"] = True  # option debug
login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)
dropzone = Dropzone(app)


@app.errorhandler(413)
def too_large(e):
    return "Fichier trop volumineux", 413


@login_manager.user_loader
def load_user(user_id):
    # since the user_id is just the primary key of our user table, use it in the query for the user
    return User.query.get(int(user_id))


class Glossary(db.Model):  # Modèle du glossaire
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    Source_Lang = db.Column(db.Text, nullable=False)
    Target_Lang = db.Column(db.Text, nullable=False)
    Source = db.Column(db.Text, nullable=False)
    Target = db.Column(db.Text, nullable=False)


class User(UserMixin, db.Model):  # Modèle utilisateur
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    Pseudo = db.Column(db.Text, nullable=False, unique=True)
    Mail = db.Column(db.Text, nullable=False, unique=True)
    Password = db.Column(db.Text, nullable=False)
    Status = db.Column(db.Integer)


class Project(db.Model):  # Modèle projet
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    Name = db.Column(db.Text, nullable=False)
    Type = db.Column(db.Text, nullable=False)
    Owner = db.Column(db.Text, nullable=False)
    Extension = db.Column(db.Text, nullable=False)
    Source_Lang = db.Column(db.Text, nullable=False)
    Target_Lang = db.Column(db.Text, nullable=False)
    Advancement = db.Column(db.Text, nullable=False)
    Last_Block = db.Column(db.Text, nullable=False)


def Glos():  # fonction formatage glossaire
    formatedGlo = ""
    i = 0
    Gloquery = Glossary.query.order_by(Glossary.Source, Glossary.Target).with_entities(Glossary.Source,
                                                                                       Glossary.Target).all()
    if Gloquery is None:
        return formatedGlo
    else:
        for line in Gloquery:
            formatedGlo = formatedGlo + str(Gloquery[i][0]) + "\t" + str(Gloquery[i][1]) + "\n"
            i = i + 1
        return formatedGlo[:-1]


formatedGlossary = Glos()


@app.route('/', methods=["GET"])  # racine site
def index():
    Glo = Glossary.query.filter_by(Source="Data Overmind").first()  # toute les tâches par ordre d'ID
    return render_template('index.html', Glo=Glo)  # template avec réponse de requete de task


@app.route('/autocomplete', methods=["POST"])
@login_required
def autocomplete():
    toshearch = request.json["begin"]
    popfile = open("database/pop_french.txt", 'r', encoding="utf-8")
    popword = [line.split('\n') for line in popfile.readlines()]
    matching = [i for i in popword if i[0].startswith(toshearch)]
    if len(matching) == 0:
        globalfile = open("database/french.txt", 'r', encoding="utf-8")
        word = [line.split('\n') for line in globalfile.readlines()]
        matching = [i for i in word if i[0].startswith(toshearch)]

    try:
        if matching[0][0] == toshearch:
            try:
                return jsonify({"result": matching[1][0]})
            except:
                return jsonify({"result": " "})
        else:
            return jsonify({"result": matching[0][0]})
    except:
        return jsonify({"result": " "})


@app.route('/translate', methods=["POST"])  # chemin de l'API de traduction
def get_prediction():
    provider = request.json['provider']
    apikey = request.json['apikey']
    source = request.json['source']
    target = request.json['target']
    formality = request.json['formality']
    text = request.json['text']
    translation = TranslatorAPI.translate(translator, provider, apikey, source, target, formality, text,
                                          formatedGlossary)
    return jsonify({"output": translation})


@app.route("/glossary", methods=["GET", "POST"])
@login_required
def glossary():
    if request.method == "POST":
        G_Source_Lang = request.form['Source_Lang']
        G_Target_Lang = request.form['Target_Lang']
        G_Source = request.form['Source']
        G_Target = request.form['Target']
        New_Glossary = Glossary(Source_Lang=G_Source_Lang, Target_Lang=G_Target_Lang, Source=G_Source, Target=G_Target)
        try:
            db.session.add(New_Glossary)
            db.session.commit()
            flash("Ajout dans le glossaire réussie")
            return redirect("/glossary")
        except:
            flash("l'ajout dans le glossaire a échoué")
            return redirect("/glossary")
    else:
        EditGlossary = Glossary.query.order_by(Glossary.id).with_entities(Glossary.id, Glossary.Source_Lang,
                                                                          Glossary.Target_Lang, Glossary.Source,
                                                                          Glossary.Target).all()
        return render_template('glossary.html', EditGlossary=EditGlossary)


@app.route("/glossary/delete/<int:id>")
@login_required
def Glossary_Delete(id):
    Glossary_to_Delete = Glossary.query.get_or_404(id)
    try:
        db.session.delete(Glossary_to_Delete)
        db.session.commit()
        flash("Suppression Réussie")
        return redirect("/glossary")
    except:
        flash("La suppression dans le glossaire a échoué")
        return redirect("/glossary")


@app.route("/glossary/update/<int:id>", methods=["GET", "POST"])
@login_required
def Glossary_Update(id):
    Glossary_to_Update = Glossary.query.get_or_404(id)
    if request.method == "POST":
        Glossary_to_Update.Source_Lang = request.form['Source_Lang']
        Glossary_to_Update.Target_Lang = request.form['Target_Lang']
        Glossary_to_Update.Source = request.form['Source']
        Glossary_to_Update.Target = request.form['Target']
        try:
            db.session.commit()
            return redirect("/glossary")
        except:
            return "la mise à jour dans le glossaire a échoué"
    else:
        return render_template('update.html', Glossary_to_Update=Glossary_to_Update)


@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        pseudo = request.form.get('pseudo')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        testpseudo = User.query.filter_by(Pseudo=pseudo).first()
        if not testpseudo or not check_password_hash(testpseudo.Password, password):
            flash("Authentification impossible, vérifiez vos informations d'identification.")
            return redirect("/login")
        else:
            login_user(testpseudo, remember=remember)
            return redirect("/home")
    else:
        return render_template('login.html')


@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        mail = request.form.get('mail')
        pseudo = request.form.get('pseudo')
        password = request.form.get('password')
        testmail = User.query.filter_by(Mail=mail).first()  # verification pseudo déjà existant
        if testmail:  # si utilisateur déjà existant retour à la page de connexion en disant que l'adresse existe déjà
            flash("Cette adresse est déjà utilisée:")
            return redirect("/signup")
        testpseudo = User.query.filter_by(Pseudo=pseudo).first()
        if testpseudo:
            flash("Ce nom d'utilisateur est déjà utilisé, choisissez-en un autre ou :")
            return redirect("/signup")
        hashpassword = generate_password_hash(password, method="sha3_256")

        new_user = User(Pseudo=pseudo, Mail=mail, Password=hashpassword, Status=0)
        # add the new user to the database
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    else:
        return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/home')
@login_required
def home():
    current = str(flask_login.current_user.id)
    Projectlist = Project.query.filter_by(Owner=current).all()
    return render_template('home.html', pseudo=current_user.Pseudo, Projectlist=Projectlist)


@app.route("/settings")
@login_required
def settings():
    return 'settings'


@app.route("/newproject", methods=["GET", "POST"])
@login_required
def newproject():
    if request.method == "POST":
        my_files = request.files
        name = request.form.get('name')
        type = request.form.get('type')
        format = request.form.get('format')
        source = request.form.get('source')
        target = request.form.get('target')
        current_owner = str(flask_login.current_user.id)
        try:
            idproject = db.session.query(Project).order_by(Project.id.desc()).first().id
        except:
            idproject = "0"
        idproject = str(int(idproject) + 1)
        os.mkdir(app.config['UPLOAD_FOLDER'] + "/" + idproject)
        for item in my_files:
            up_file = my_files.get(item)
            up_file.filename = secure_filename(up_file.filename)
            if up_file.filename != '':
                file_ext = os.path.splitext(up_file.filename)[1]
            if file_ext not in app.config['UPLOAD_EXTENSIONS']:
                abort(400)
            up_file.save(os.path.join(app.config['UPLOAD_FOLDER'] + "/" + idproject, up_file.filename))
        new_project = Project(id=int(idproject), Name=name, Type=type, Owner=current_owner, Extension=format,
                              Source_Lang=source, Target_Lang=target, Advancement=0, Last_Block=1)
        db.session.add(new_project)
        db.session.commit()
        return redirect('/home')
    else:
        return render_template('newproject.html')


@app.route("/project/<int:id>", methods=["GET", "POST"])
@login_required
def project(id):
    if str(flask_login.current_user.id) == str(Project.query.filter_by(id=id).first().Owner):
        if request.method == "GET":
            type = str(Project.query.filter_by(id=id).first().Type)
            extension = str(Project.query.filter_by(id=id).first().Extension)
            last = str(Project.query.filter_by(id=id).first().Last_Block)
            files = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'] + "/" + str(id)))
            print(files[0])
            if type == "Roman/Light Novel (Textuel)":
                if extension == "docx":
                    return render_template('docxproject.html', id=id, last=last)
                if extension == "txt":
                    return "txt"
                if extension == "pdf":
                    return "pdf"
            if type == "Manga/BD (Image)":
                if extension == "png":
                    return "png"
                if extension == "jpg/jpeg":
                    return "jpg"
                if extension == "pdf":
                    return "pdf"
        if request.method == "POST":
            type = str(Project.query.filter_by(id=id).first().Type)
            extension = str(Project.query.filter_by(id=id).first().Extension)
            if type == "Roman/Light Novel (Textuel)":
                if extension == "docx":
                    print(request.data)
                    r = Response(response="<i>TEST OK</i>", status=200, mimetype="text/plain")
                    r.headers["Content-Type"] = "text/plain; charset=utf-8"
                    return r
                if extension == "txt":
                    return "txt"
                if extension == "pdf":
                    return "pdf"
            if type == "Manga/BD (Image)":
                if extension == "png":
                    return "png"
                if extension == "jpg/jpeg":
                    return "jpg"
                if extension == "pdf":
                    return "pdf"
    else:
        logout_user()
        return redirect('/')


app.run(host="127.0.0.1")
