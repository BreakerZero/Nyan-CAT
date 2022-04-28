# -*- coding: utf-8 -*-
import json
from operator import truediv
import os
import docx
from backend.converterAPI import ConverterAPI
from enum import unique
from re import template
from flask import Flask, request, jsonify, render_template, redirect, sessions, url_for, flash, abort, Blueprint, Response
import flask_login
from sqlalchemy.sql.elements import Null
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import flask_sqlalchemy
from werkzeug.datastructures import auth_property
from werkzeug.utils import redirect, secure_filename
from backend.translateAPI import TranslatorAPI
from flask_login import UserMixin, LoginManager, login_user, current_user, login_required, logout_user
from flask_dropzone import Dropzone
import html2text
import threading

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
app.config['UPLOAD_EXTENSIONS'] = ['.png', '.jpg', '.jpeg', '.pdf', '.docx', '.doc', '.odt','.txt']  # extensions autorisées
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 50  # max 50Mo
db = flask_sqlalchemy.SQLAlchemy(app)  # lien bdd
app.config["DEBUG"] = True  # option debug
login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)
dropzone = Dropzone(app)
ConvAPI = ConverterAPI()


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
    TranslatorSettings = db.Column(db.Text, nullable=False)
    TranslatorProvider = db.Column(db.Text, nullable=False)
    Formality = db.Column(db.Text)
    ApiKey = db.Column(db.Text, nullable=False)
    KeepStyle = db.Column(db.Integer)
    Autocomplete = db.Column(db.Integer)



class Project(db.Model):  # Modèle projet
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    Name = db.Column(db.Text, nullable=False)
    Type = db.Column(db.Text, nullable=False)
    Owner = db.Column(db.Text, nullable=False)
    Extension = db.Column(db.Text, nullable=False)
    Source_Lang = db.Column(db.Text, nullable=False)
    Target_Lang = db.Column(db.Text, nullable=False)
    Advancement = db.Column(db.Integer, nullable=False)
    Last_Block = db.Column(db.Integer, nullable=False)
    Last_Previous_Block = db.Column(db.Integer, nullable=False)

class Lexicon_fr(db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    ortho = db.Column(db.String, nullable=False)
    freqfilms = db.Column(db.Float, nullable=False)
    freqlivres = db.Column(db.Float, nullable=False)

class TranslationMemory(db.Model):  # Modèle mémoire de traduction
    id = db.Column(db.Integer, primary_key=True, nullable=False, unique=True)
    Source_Lang = db.Column(db.Text, nullable=False)
    Target_Lang = db.Column(db.Text, nullable=False)
    Source = db.Column(db.Text, nullable=False)
    Target = db.Column(db.Text, nullable=False)
    Owner = db.Column(db.Integer, nullable=False)
    Project = db.Column(db.Integer, nullable=False)
    Segment = db.Column(db.Integer, nullable=False)

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
    return render_template('index.html')


@app.route('/autocomplete', methods=["POST"])
@login_required
def autocomplete():
    tosearch = request.json["begin"]
    tosearch = str(tosearch).lower()
    matching= Lexicon_fr.query.filter(Lexicon_fr.ortho.startswith(tosearch)).order_by(Lexicon_fr.freqlivres.desc(), Lexicon_fr.freqfilms.desc()).limit(2).all()
    if len(matching) == 2:
        if str(matching[0].ortho) == tosearch and str(matching[0].ortho) != str(matching[1].ortho) :
            if " " not in str(matching[1].ortho):
                return jsonify({"result": matching[1].ortho})
            else:
                return jsonify({"result": " "})
        elif str(matching[0].ortho) == tosearch and str(matching[0].ortho) == str(matching[1].ortho):
            return jsonify({"result": " "})
        else:
            if " " not in str(matching[0].ortho):
                return jsonify({"result": matching[0].ortho})
            else:
                return jsonify({"result": " "})
    elif len(matching) == 1:
        if str(matching[0].ortho) == tosearch:
            return jsonify({"result": " "})
        else:
            if " " not in str(matching[0].ortho):
                return jsonify({"result": matching[0].ortho})
            else:
                return jsonify({"result": " "})
    else:
        return jsonify({"result": " "})


@app.route('/translate', methods=["POST"])  # chemin de l'API de traduction
@login_required
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
            path = "static/json/memory"+str(testpseudo.id)+".json"
            jsonfile = open(path, "w", encoding="UTF-8")
            data = TranslationMemory.query.filter_by(Owner=int(testpseudo.id)).all()
            jsondata = []
            for i in data:
                jsondata.append({"id": i.id, "Source_Lang": i.Source_Lang, "Target_Lang": i.Target_Lang, "Source": i.Source, "Target": i.Target})
            json.dump(jsondata, jsonfile)
            jsonfile.close()
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
    if os.path.exists("static/json/memory"+str(flask_login.current_user.id)+".json"):
        os.remove("static/json/memory"+str(flask_login.current_user.id)+".json")
    logout_user()
    return redirect("/")


@app.route('/home')
@login_required
def home():
    current = str(flask_login.current_user.id)
    Projectlist = Project.query.filter_by(Owner=current).all()
    return render_template('home.html', pseudo=current_user.Pseudo, Projectlist=Projectlist)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    currentid = str(flask_login.current_user.id)
    User_to_Update = User.query.get_or_404(currentid)
    if request.method == "POST":
        User_to_Update.TranslatorProvider = request.form.get('translatorprovider')
        User_to_Update.ApiKey = request.form.get('api')
        User_to_Update.KeepStyle = True if request.form.get('keepstyle') else False
        User_to_Update.Autocomplete = True if request.form.get('autocomplete') else False
        translatorsettings = request.form.get('translatorsettings')
        if translatorsettings == "Actif":
            User_to_Update.TranslatorSettings = "More"
        elif translatorsettings == "Passif":
            User_to_Update.TranslatorSettings = "Less"
        else:
            User_to_Update.TranslatorSettings = "Disabled"
        formality = request.form.get('formality')
        if formality == "Informel":
            User_to_Update.Formality = "informal"
        elif formality == "Formel":
            User_to_Update.Formality = "formal"
        else:
            User_to_Update.Formality = None
        try:
            db.session.commit()
            return redirect("/home")
        except:
            return "la mise à jour de l'utilisateur a échoué"
    else:
        return render_template('settings.html', User_to_Update=User_to_Update)

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
                              Source_Lang=source, Target_Lang=target, Advancement=0, Last_Block=0)
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
            keepstyle = bool(User.query.filter_by(id=flask_login.current_user.id).first().KeepStyle)
            complete = bool(User.query.filter_by(id=flask_login.current_user.id).first().Autocomplete)
            translatorsettings = str(User.query.filter_by(id=flask_login.current_user.id).first().TranslatorSettings)
            project = Project.query.filter_by(id=id).first()
            if type == "Roman/Light Novel (Textuel)":
                if extension == "docx":
                    return render_template('docxproject.html', id=id, last=last, keepstyle=keepstyle, complete=complete, user=flask_login.current_user, project=project, translatorsettings=translatorsettings)
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
            source = str(Project.query.filter_by(id=id).first().Source_Lang)
            target = str(Project.query.filter_by(id=id).first().Target_Lang)
            translatorprovidersettings = str(User.query.filter_by(id=flask_login.current_user.id).first().TranslatorProvider)
            formality = str(User.query.filter_by(id=flask_login.current_user.id).first().Formality)
            apikey = str(User.query.filter_by(id=flask_login.current_user.id).first().ApiKey)
            if type == "Roman/Light Novel (Textuel)":
                if extension == "docx":
                    files = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'] + "/" + str(id)))
                    namefile = str(files[0])
                    if "ressource" in request.json: #Demande ressouce fichier original
                        idblock = int(request.json["ressource"])
                        OriginalDocx = docx.Document(app.config['UPLOAD_FOLDER'] + "/" + str(id) + "/" + namefile)
                        Html = ConverterAPI.ParaDocxToHtml(ConvAPI, OriginalDocx, idblock)
                        return jsonify({"result": Html})
                    elif "translated" in request.json: #Demande ressouce fichier traduit
                        idblock = int(request.json["translated"])
                        idpreviousblock = request.json["previoustranslated"]
                        OriginalHtml = str(request.json["originaltext"])
                        TranslatedHtml = str(request.json["translatedtext"])
                        if TranslatedHtml == "<p><br></p>":
                            TranslatedHtml = "<p></p>"
                        if len(files) == 1: #Création du fichier de sortie s'il n'existe pas
                            TranslatedDocx = docx.Document()
                            SaveName = app.config['UPLOAD_FOLDER'] + "/" + str(id) + "/" + "translated-" + namefile
                            TranslatedDocx.save(SaveName)
                        SaveName = app.config['UPLOAD_FOLDER'] + "/" + str(id) + "/" + "translated-" + namefile
                        mutex = threading.Lock()
                        mutex.acquire()
                        while mutex.locked(): #pour gérer un grand nombre d'écriture fichier
                            try:
                                TranslatedDocx = docx.Document(SaveName)
                            except:
                                pass
                            else:
                                mutex.release()
                        text = html2text.html2text(TranslatedHtml)
                        if idblock < len(TranslatedDocx.paragraphs): #L'écriture du fichier de sortie s'écrivant au fur et à mesure
                            if TranslatedDocx.paragraphs[idblock].text != text: #Si le text est différant on enregistre ce nouveau texte
                                if idpreviousblock is not None:
                                    ConverterAPI.ParaHtmlToDocx(ConvAPI, TranslatedHtml, TranslatedDocx, int(idpreviousblock), SaveName)
                                Html= ConverterAPI.ParaDocxToHtml(ConvAPI, TranslatedDocx, idblock)
                            else:
                                Html = ConverterAPI.ParaDocxToHtml(ConvAPI, TranslatedDocx, idblock)
                        else: #Si le block n'existe pas dans le document de sortie
                            text = html2text.html2text(OriginalHtml)
                            translation = TranslatorAPI.translate(translator, translatorprovidersettings, apikey, source, target, formality, text, formatedGlossary) #on tente une traduction si on a rien dans la mémoire de traduction
                            Html = '<p>' + translation + "</p>"
                            ConverterAPI.ParaHtmlToDocx(ConvAPI, Html, TranslatedDocx, idblock, SaveName)
                        Project.query.filter_by(id=id).first().Last_Previous_Block = Project.query.filter_by(id=id).first().Last_Block
                        Project.query.filter_by(id=id).first().Last_Block = idblock
                        db.session.commit()
                        return jsonify({"result": Html})
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

@app.route("/addsegment", methods=['POST'])
@login_required
def addsegment():
    if request.method == 'POST':
        User_ID = request.json['User_ID']
        Project_ID = request.json['Project_ID']
        Segment_ID = request.json['Segment_ID']
        Source = request.json['Source']
        Target = request.json['Target']
        Source_Lang = request.json['Source_Lang']
        Target_Lang = request.json['Target_Lang']
        #search if the segment already exists
        if TranslationMemory.query.filter_by(Owner=User_ID, Project=Project_ID, Segment=Segment_ID).first() is None:
            New_TranslationMemory = TranslationMemory(Owner=User_ID, Project=Project_ID, Segment=Segment_ID, Source=Source, Target=Target, Source_Lang=Source_Lang, Target_Lang=Target_Lang)
            db.session.add(New_TranslationMemory)
            db.session.commit()
        else:
            TranslationMemory.query.filter_by(Owner=User_ID, Project=Project_ID, Segment=Segment_ID).update({'Source':Source, 'Target':Target, 'Source_Lang':Source_Lang, 'Target_Lang':Target_Lang})
            db.session.commit()
        return jsonify({"result": "ok"})


app.run(host="127.0.0.1", port=5000, threaded=True)