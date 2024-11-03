import json
import docx
import csv
import cv2
import numpy as np
import requests
from docx import Document
from PIL import Image, ImageDraw, ImageFont
import base64
import io
import os
import re
import platform
import subprocess
from subprocess import run, Popen

from nyan.converterAPI import ConverterAPI
from flask import Flask, request, jsonify, render_template, redirect, flash, abort, send_from_directory
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash
import flask_sqlalchemy
from werkzeug.utils import redirect, secure_filename
from nyan.translateAPI import TranslatorAPI
from flask_login import UserMixin, LoginManager, login_user, current_user, login_required, logout_user
import html2text
import threading
from Levenshtein import distance

LANGUAGETOOL_URL = "http://localhost:8081/v2/check"
LANGUAGETOOL_BASE_DIR = "languagetool"
LANGUAGETOOL_VERSION = "LanguageTool-6.5"
LANGUAGETOOL_PATH = os.path.join(LANGUAGETOOL_BASE_DIR, LANGUAGETOOL_VERSION)
ADDED_FILES_DIR = os.path.join(LANGUAGETOOL_PATH, "org", "languagetool", "resource")
app = Flask(__name__)
translator = TranslatorAPI('./translatemodel/')  # chemin vers les modèles
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
file_path = os.path.join(os.getcwd(), 'database', 'nyan.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + file_path  # Nom de la bdd
app.config['SECRET_KEY'] = '9df31cd3eb2f6f6386571da69d6b418e'  # Clé random pour autentification
app.config['UPLOAD_FOLDER'] = "fileproject"
app.config['UPLOAD_EXTENSIONS'] = ['.png', '.jpg', '.jpeg', '.pdf', '.docx', '.doc', '.odt', '.txt']
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 500  # max 500Mo
db = flask_sqlalchemy.SQLAlchemy(app)  # lien bdd
app.config["DEBUG"] = True  # option debug
start_lock = threading.Lock()
server_started = False
login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)
ConvAPI = ConverterAPI()
system = platform.system()
