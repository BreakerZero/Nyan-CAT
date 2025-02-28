import json
import docx
import csv
import cv2
import numpy as np
import pandas as pd
import requests
from docx import Document
from PIL import Image, ImageDraw, ImageFont
import base64
import io
from io import StringIO
import os
import sys
import psutil
import time
import re
import platform
import subprocess
from subprocess import run, Popen
from concurrent.futures import ThreadPoolExecutor, as_completed

from nyan.converterAPI import ConverterAPI
from flask import Flask, request, jsonify, render_template, redirect, flash, abort, send_from_directory, send_file
import flask_login
from werkzeug.security import generate_password_hash, check_password_hash
import flask_sqlalchemy
from werkzeug.utils import redirect, secure_filename
from nyan.translateAPI import TranslatorAPI
from flask_login import UserMixin, LoginManager, login_user, current_user, login_required, logout_user
import html2text
import threading
from Levenshtein import distance
from celery import Celery
from celery.schedules import crontab
import redis
from celery.result import AsyncResult
from celery import shared_task
from queue import Queue
from celery.utils.log import get_task_logger

redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = os.getenv('REDIS_PORT', '6379')

LANGUAGETOOL_URL = "http://localhost:8081/v2/check"
LANGUAGETOOL_BASE_DIR = "languagetool"
LANGUAGETOOL_VERSION = "LanguageTool-6.5"
LANGUAGETOOL_PATH = os.path.join(LANGUAGETOOL_BASE_DIR, LANGUAGETOOL_VERSION)
ADDED_FILES_DIR = os.path.join(LANGUAGETOOL_PATH, "org", "languagetool", "resource")
PROXY_PATH = os.path.join('proxies.txt')
app = Flask("app")
translator = TranslatorAPI('./translatemodel/')  # chemin vers les modèles
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CELERY_BROKER_URL'] = f'redis://{redis_host}:{redis_port}/0'
app.config['CELERY_RESULT_BACKEND'] = f'redis://{redis_host}:{redis_port}/0'
file_path = os.path.join(os.getcwd(), 'database', 'nyan.db')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + file_path  # Nom de la bdd
app.config['SECRET_KEY'] = '9df31cd3eb2f6f6386571da69d6b418e'  # Clé random pour autentification
app.config['UPLOAD_FOLDER'] = "fileproject"
app.config['UPLOAD_EXTENSIONS'] = ['.png', '.jpg', '.jpeg', '.pdf', '.docx', '.doc', '.odt', '.txt']
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 500  # max 500Mo
db = flask_sqlalchemy.SQLAlchemy(app)  # lien bdd
app.config["DEBUG"] = True  # option debug
celery = Celery(app.name)
celery.conf.update(
	broker_url=f'redis://{redis_host}:{redis_port}/0',
	result_backend=f'redis://{redis_host}:{redis_port}/0',
	beat_schedule={
		'update-proxies-every-hour': {
			'task': 'app.update_proxies',
			'schedule': crontab(minute='0'),
		},
	},
	timezone='UTC'
)
start_lock = threading.Lock()
server_started = False
login_manager = LoginManager()
login_manager.login_view = '/login'
login_manager.init_app(app)
ConvAPI = ConverterAPI()
system = platform.system()
logger = get_task_logger(__name__)


def wait_for_redis():
	redis_client = redis.Redis(host=redis_host, port=6379)
	for _ in range(30):  # Attendre jusqu'à 30 secondes
		try:
			if redis_client.ping():
				print("Redis est prêt.")
				return redis_client
		except ConnectionError:
			print("Redis n'est pas prêt, réessayer...")
		time.sleep(1)
	raise Exception("Impossible de se connecter à Redis après 30 secondes.")


redis_client = wait_for_redis()

from translatepylocal.translators.deepl import DeeplTranslate as PersonalDeepl
from translatepylocal.translators.base import BaseTranslator
from translatepylocal.utils.request import Request

ignored_text = {"...", "…", "“…”", "\"…\"", "\"...\"", "“...”", "\n", "\t", "\r"}
