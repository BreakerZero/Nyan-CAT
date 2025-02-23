# -*- coding: utf-8 -*-
from utils import *


@app.errorhandler(413)
def too_large(e):
	return "Fichier trop volumineux", 413


@login_manager.user_loader
def load_user(user_id):
	# since the user_id is just the primary key of our user table, use it in the query for the user
	return db.session.get(User, int(user_id))


with app.app_context():
	formatedGlossary = Glos()
	start_celery_worker()
	start_celery_beat()
	global server_started
	if not server_started:
		with start_lock:
			try:
				update_added_txt_and_restart_lt(kill=False)
			except Exception as e:
				pass
			server_started = True


@celery.task(bind=True)
def pre_translate_docx(self, projectid):
	project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(projectid))

	files = [f for f in os.listdir(project_folder) if f.endswith('.docx')]
	if not files or len(files) < 2:
		raise FileNotFoundError("Deux fichiers DOCX sont requis pour déterminer l'entrée et la sortie.")

	input_file = min(files, key=len)
	output_file = max(files, key=len)

	input_path = os.path.join(project_folder, input_file)
	output_path = os.path.join(project_folder, output_file)

	docin = docx.Document(input_path)
	parasin = docin.paragraphs

	try:
		docout = docx.Document(output_path)
	except:
		docout = docx.Document()

	while len(docout.paragraphs) < len(parasin):
		docout.add_paragraph('')

	length = len(parasin)

	doc_lock = threading.Lock()
	file_lock = threading.Lock()

	def load_proxies():
		with open(PROXY_PATH, "r") as f:
			listofproxies = f.read().splitlines()
		q = Queue()
		for proxy in listofproxies:
			q.put(proxy)
		return q

	self.proxies_queue = load_proxies()
	last_modified = os.path.getmtime(PROXY_PATH)

	def process_paragraph(i):
		nonlocal doc_lock, file_lock, last_modified

		if time.time() - last_modified >= 60:
			current_modified = os.path.getmtime(PROXY_PATH)
			if current_modified != last_modified:  # Si le fichier a été mis à jour
				print("Rechargement des proxies en raison de la modification du fichier.")
				self.proxies_queue = load_proxies()
				last_modified = current_modified

		para = parasin[i]
		temp = para.text

		if temp.strip() == "" or temp.strip() in ignored_text:
			pass
		elif docout.paragraphs[i].text != "" and docout.paragraphs[i].text != temp:
			# Paragraph already translated
			pass
		else:
			prev_paragraph = get_context_paragraphs(i, parasin, direction="before")
			next_paragraph = get_context_paragraphs(i, parasin, direction="after")
			index, translation, proxy = translate_paragraph(i, temp, self.proxies_queue, max_retries=float('inf'),
															prev_paragraph=prev_paragraph,
															next_paragraph=next_paragraph,
															formatedGlossary=formatedGlossary)
			if translation:
				with doc_lock:
					docout.paragraphs[i].text = translation
				with file_lock:
					docout.save(output_path)

	with ThreadPoolExecutor(max_workers=15) as executor:
		futures = [executor.submit(process_paragraph, i) for i in range(length)]
		for i, future in enumerate(as_completed(futures)):
			self.update_state(state='PROGRESS', meta={'current': i + 1, 'total': length})
			future.result()  # Récupère les exceptions éventuelles

	# Retourne le statut final
	return {'status': 'Task completed!', 'output_file': output_path}


@celery.task(bind=True)
def update_proxies(self):
	print("Updating proxies task launched")
	proxy_sources = [
		"https://raw.githubusercontent.com/roosterkid/openproxylist/refs/heads/main/HTTPS_RAW.txt",
		"https://raw.githubusercontent.com/vakhov/fresh-proxy-list/refs/heads/master/https.txt",
		"https://raw.githubusercontent.com/r00tee/Proxy-List/refs/heads/main/Https.txt",
		"https://raw.githubusercontent.com/javadbazokar/PROXY-List/refs/heads/main/https.txt",
		"https://raw.githubusercontent.com/officialputuid/KangProxy/refs/heads/KangProxy/https/https.txt",
		"https://raw.githubusercontent.com/vmheaven/VMHeaven-Free-Proxy-Updated/refs/heads/main/https.txt",
		"https://raw.githubusercontent.com/Anonym0usWork1221/Free-Proxies/refs/heads/main/proxy_files/https_proxies.txt",
		"https://raw.githubusercontent.com/zebbern/Proxy-Scraper/refs/heads/main/https.txt",
	]

	# Récupérer les proxies depuis les sources
	proxies = []
	for url in proxy_sources:
		try:
			response = requests.get(url, timeout=10)
			if response.status_code == 200:
				proxies.extend(response.text.splitlines())
		except requests.RequestException as e:
			print(f"Erreur lors de la récupération de proxies depuis {url}: {e}")

	valid_proxies = []
	with ThreadPoolExecutor(max_workers=1000) as executor:
		future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}

		for future in as_completed(future_to_proxy):
			proxy = future_to_proxy[future]
			try:
				is_valid = future.result()
				if is_valid:
					print(f"Proxy {proxy} est valide.")
					valid_proxies.append(proxy)
			except Exception as exc:
				print(f"Erreur lors du test du proxy {proxy}: {exc}")

	with open(PROXY_PATH, 'w') as file:
		file.write("\n".join(valid_proxies))

	return {'status': 'Task completed!'}


@app.route('/favicon.ico')
def favicon():
	return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/', methods=["GET"])
def index():
	return render_template('index.html')


@app.route('/autocomplete', methods=["POST"])
@login_required
def autocomplete():
	tosearch = request.json["begin"].strip().lower()

	matching = Lexicon_fr.query.filter(
		Lexicon_fr.ortho.startswith(tosearch)
	).order_by(
		Lexicon_fr.freqlivres.desc(),
		Lexicon_fr.freqfilms.desc()
	).limit(5).all()

	suggestions = []
	for match in matching:
		word = match.ortho.lower()
		if word != tosearch and " " not in word:
			suggestions.append((word, match.freqlivres, match.freqfilms))

	if not suggestions or suggestions[0][0] == tosearch:
		return jsonify({"result": " "})

	best_match = min(suggestions, key=lambda s: distance(tosearch, s[0]))
	return jsonify({"result": best_match[0]})


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


@app.route("/context", methods=["GET", "POST"])
@login_required
def context():
	if request.method == "POST":
		C_Active = 'Active' in request.form  # Vérifie si la case à cocher "Active" a été cochée
		C_Text = request.form['Text']
		New_Context = Context(Active=C_Active, Text=C_Text)
		try:
			db.session.add(New_Context)
			db.session.commit()
			flash("Ajout de l'entrée de contexte réussi")
			return redirect("/context")
		except:
			flash("L'ajout de l'entrée de contexte a échoué")
			return redirect("/context")
	else:
		ContextList = Context.query.order_by(Context.id).with_entities(Context.id, Context.Active, Context.Text).all()
		return render_template('context.html', ContextList=ContextList)


@app.route("/context/delete/<int:id>")
@login_required
def Context_Delete(id):
	Context_to_Delete = Context.query.get_or_404(id)
	try:
		db.session.delete(Context_to_Delete)
		db.session.commit()
		flash("Suppression réussie")
		return redirect("/context")
	except:
		flash("La suppression de l'entrée de contexte a échoué")
		return redirect("/context")


@app.route("/context/update/<int:id>", methods=["GET", "POST"])
@login_required
def Context_Update(id):
	Context_to_Update = Context.query.get_or_404(id)
	if request.method == "POST":
		Context_to_Update.Active = 'Active' in request.form  # Mise à jour du statut actif
		Context_to_Update.Text = request.form['Text']
		try:
			db.session.commit()
			flash("Mise à jour réussie")
			return redirect("/context")
		except:
			flash("La mise à jour de l'entrée de contexte a échoué")
			return "La mise à jour de l'entrée de contexte a échoué"
	else:
		return render_template('contextupdate.html', Context_to_Update=Context_to_Update)


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
			static_folder = os.path.join("static", "json")
			if not os.path.exists(static_folder):
				os.makedirs(static_folder)

			json_path = os.path.join(static_folder, f"memory{testpseudo.id}.json")
			if not os.path.exists(json_path):
				with open(json_path, "w", encoding="UTF-8") as jsonfile:
					jsonfile.write("[]")

			csv_path = os.path.join(static_folder, f"memory{testpseudo.id}.csv")
			if not os.path.exists(csv_path):
				with open(csv_path, "w", encoding="UTF-8", newline="") as csvfile:
					csv_writer = csv.writer(csvfile)
					csv_writer.writerow(["id", "Source_Lang", "Target_Lang", "Source", "Target"])

			data = TranslationMemory.query.filter_by(Owner=int(testpseudo.id)).all()
			json_data = []

			with open(json_path, "w", encoding="UTF-8") as jsonfile, \
					open(csv_path, "a", encoding="UTF-8", newline="") as csvfile:

				csv_writer = csv.writer(csvfile)
				for i in data:
					entry = {
						"id": i.id,
						"Source_Lang": i.Source_Lang,
						"Target_Lang": i.Target_Lang,
						"Source": i.Source,
						"Target": i.Target
					}
					json_data.append(entry)
					csv_writer.writerow([i.id, i.Source_Lang, i.Target_Lang, i.Source, i.Target])
				json.dump(json_data, jsonfile)

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
		hashpassword = generate_password_hash(password, method="scrypt")

		new_user = User(Pseudo=pseudo, Mail=mail, Password=hashpassword, Status=0, TranslatorSettings="More",
						TranslatorProvider="Nyan-Cat", ApiKey="None", KeepStyle=0, Autocomplete=0)
		# add the new user to the database
		db.session.add(new_user)
		db.session.commit()
		return redirect("/login")
	else:
		return render_template('signup.html')


@app.route('/logout')
@login_required
def logout():
	json_path = os.path.join("static", "json", f"memory{flask_login.current_user.id}.json")
	if os.path.exists(json_path):
		os.remove(json_path)
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
		directory_path = os.path.join(app.config['UPLOAD_FOLDER'], idproject)
		os.makedirs(directory_path, exist_ok=True)
		for item in my_files:
			up_file = my_files.get(item)
			up_file.filename = secure_filename(up_file.filename)
			if up_file.filename != '':
				file_ext = os.path.splitext(up_file.filename)[1]
			if file_ext not in app.config['UPLOAD_EXTENSIONS']:
				abort(400)
			directory_path = os.path.join(app.config['UPLOAD_FOLDER'], str(idproject))
			os.makedirs(directory_path, exist_ok=True)
			up_file.save(os.path.join(directory_path, up_file.filename))
		if type == "Roman/Light Novel (Textuel)":
			type = "text"
		elif type == "Manga/BD (Image)":
			type = "image"
		new_project = Project(id=int(idproject), Name=name, Type=type, Owner=current_owner, Extension=format,
							  Source_Lang=source, Target_Lang=target, Advancement=0, Last_Block=0,
							  Last_Previous_Block=0)
		db.session.add(new_project)
		db.session.commit()
		return redirect('/home')
	else:
		return render_template('newproject.html')


@app.route("/project/text/docx/<int:id>", methods=["GET", "POST"])
@login_required
def projecttextdocx(id):
	if not verify_owner(id):
		logout_user()
		return redirect('/')
	if request.method == "GET":
		# create csv file if not exist
		manage_csv_memory(id)
		# get project data
		(type, extension, last, files, keepstyle, complete, translatorsettings, project,
		 total_sections) = get_project_data_for_get_method(id)
		if extension == "docx":
			return render_template('docxproject.html', id=id, last=last, keepstyle=keepstyle, complete=complete,
								   user=flask_login.current_user, project=project,
								   translatorsettings=translatorsettings, extension=extension, type=type,
								   total_sections=total_sections)
		else:
			return render_template('404.html'), 404
	if request.method == "POST":
		# get project data
		(type, extension, source, target, provider, settings, formality, apikey) = get_project_data_for_post_method(id)
		if extension == "docx":
			folder_path = os.path.join(app.config['UPLOAD_FOLDER'], str(id))
			files = os.listdir(folder_path)
			namefile = min(files, key=len)
			if "ressource" in request.json:  # Demande ressouce fichier original
				Html, PreviousHtml, NextHtml = docx_get_ressource_in_request(request, id, namefile)
				response = jsonify({"result": Html, "previous": PreviousHtml, "next": NextHtml})
				response.headers.add('Access-Control-Allow-Origin', '*')
				return response
			elif "translated" in request.json:  # Demande ressouce fichier traduit
				idblock = int(request.json["translated"])
				idpreviousblock = request.json["previoustranslated"]
				OriginalHtml = str(request.json["originaltext"])
				TranslatedHtml = str(request.json["translatedtext"])
				if TranslatedHtml == '<p><br></p>' or TranslatedHtml == '<p class=""><br></p>':
					TranslatedHtml = '<p></p>'
				SaveName = os.path.join(app.config['UPLOAD_FOLDER'], str(id), "translated-" + namefile)
				if len(files) == 1:  # Création du fichier de sortie s'il n'existe pas
					TranslatedDocx = docx.Document()
					TranslatedDocx.save(SaveName)
				mutex = threading.Lock()
				mutex.acquire()
				while mutex.locked():  # pour gérer un grand nombre d'écriture fichier
					try:
						TranslatedDocx = docx.Document(SaveName)
					except:
						pass
					else:
						mutex.release()
				text = html2text.html2text(TranslatedHtml)
				text = text.replace("\n", "")
				paragraph_exists = idblock < len(TranslatedDocx.paragraphs)
				current_text = TranslatedDocx.paragraphs[idblock].text if paragraph_exists else ""
				if paragraph_exists and current_text.strip() != text.strip() and not current_text == '':
					if idpreviousblock is not None:
						ConverterAPI.ParaHtmlToDocx(ConvAPI, TranslatedHtml, TranslatedDocx, int(idpreviousblock),
													SaveName)
					Html = ConverterAPI.ParaDocxToHtml(ConvAPI, TranslatedDocx, idblock)
				else:
					text = html2text.html2text(OriginalHtml)
					text = text.replace("\n", "")
					parasin = docx.Document(os.path.join(app.config['UPLOAD_FOLDER'], str(id), namefile)).paragraphs
					text = re.sub(r"!\[\]\(data:image\/[^\)]+\)", "", text).replace("\n", "")
					prev_paragraph = get_context_paragraphs(idblock, parasin, direction="before")
					next_paragraph = get_context_paragraphs(idblock, parasin, direction="after")

					if text:
						translation = TranslatorAPI.translate(
							translator, provider, settings, apikey, source, target, formality, text,
							formatedGlossary, prev_paragraph, next_paragraph, Context
						).replace("\n", "")
					else:
						translation = ""

					if re.search(r'\[([^\]]+)\]\(([^\)]+)\)', translation):
						Html = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'<a href="\2">\1</a>', translation)
					elif re.search(r'^#', translation):
						for i in range(6, 0, -1):
							Html = re.sub(r'^' + ('#' * i) + r' (.+)$', rf'<h{i}>\1</h{i}>', text, flags=re.MULTILINE)
					else:
						Html = f'<p>{translation}</p>'
					if current_text == '':
						bloc_to_save = int(idpreviousblock) if idpreviousblock is not None else idblock
						TranslatedHtml = TranslatedHtml if TranslatedHtml != '<p></p>' else Html
						ConverterAPI.ParaHtmlToDocx(ConvAPI, TranslatedHtml, TranslatedDocx, bloc_to_save, SaveName)
					else:
						ConverterAPI.ParaHtmlToDocx(ConvAPI, Html, TranslatedDocx, idblock, SaveName)
				Project.query.filter_by(id=id).first().Last_Previous_Block = Project.query.filter_by(
					id=id).first().Last_Block
				Project.query.filter_by(id=id).first().Last_Block = idblock
				doc = docx.Document(os.path.join(app.config['UPLOAD_FOLDER'], str(id), str(namefile)))
				total_sections = len(doc.paragraphs)
				Project.query.filter_by(id=id).first().Advancement = idblock / total_sections
				db.session.commit()
				PreviousHtml = ConverterAPI.ParaDocxToHtml(ConvAPI, TranslatedDocx, idblock - 1)
				if PreviousHtml == "<p><br></p>":
					PreviousHtml = "<p></p>"
				NextHtml = ConverterAPI.ParaDocxToHtml(ConvAPI, TranslatedDocx, idblock + 1)
				if NextHtml == "<p><br></p>":
					NextHtml = "<p></p>"
				response = jsonify({"result": Html, "previous": PreviousHtml, "next": NextHtml})
				response.headers.add('Access-Control-Allow-Origin', '*')
				return response

@app.route("/project/text/txt/<int:id>", methods=["GET", "POST"])
@login_required
def projecttexttxt(id):
	return "not implemented yet"


@app.route("/project/text/pdf/<int:id>", methods=["GET", "POST"])
@login_required
def projecttextpdf(id):
	return "not implemented yet"


@app.route("/project/image/png/<int:id>", methods=["GET", "POST"])
@login_required
def projectimagepng(id):
	return "not implemented yet"


@app.route("/project/image/jpg/<int:id>", methods=["GET", "POST"])
@login_required
def projectimagejpg(id):
	return "not implemented yet"


@app.route("/project/image/pdf/<int:id>", methods=["GET", "POST"])
@login_required
def projectimagepdf(id):
	return "not implemented yet"


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
		csv_path = os.path.join("static", "csv", f"memory{Project_ID}.csv")
		existing_segment = TranslationMemory.query.filter_by(Owner=User_ID, Project=Project_ID,
															 Segment=Segment_ID).first()
		if existing_segment is None:
			New_TranslationMemory = TranslationMemory(Owner=User_ID, Project=Project_ID, Segment=Segment_ID,
													  Source=Source, Target=Target, Source_Lang=Source_Lang,
													  Target_Lang=Target_Lang)
			db.session.add(New_TranslationMemory)
			db.session.commit()
			if os.path.isfile(csv_path):
				with open(csv_path, "a+") as csvfile:
					writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL,
										lineterminator='\n')
					writer.writerow([Source.replace('\n', ''), Target.replace('\n', '')])
		else:
			TranslationMemory.query.filter_by(Owner=User_ID, Project=Project_ID, Segment=Segment_ID).update(
				{'Source': Source, 'Target': Target, 'Source_Lang': Source_Lang, 'Target_Lang': Target_Lang})
			db.session.commit()
			if os.path.isfile(csv_path):
				with open(csv_path, "a+") as csvfile:
					writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL,
										lineterminator='\n')
					writer.writerow([Source.replace('\n', ''), Target.replace('\n', '')])

		return jsonify({"result": "ok"})


@app.route("/project/<int:id>/train", methods=["POST"])
@login_required
def train(id):
	"""if os.path.isfile("static/csv/memory" + str(id) + ".csv"):
		with open("static/csv/memory" + str(id) + ".csv", "r") as csvfile:
			reader = csv.reader(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
			lines = len(list(reader))
		if lines > 1:
			Source_Lang = Project.query.filter_by(id=id).first().Source_Lang
			Target_Lang = Project.query.filter_by(id=id).first().Target_Lang
			#launch the training in new thread
			thread = threading.Thread(target=Training, args=(id, Source_Lang, Target_Lang))
			thread.start()"""
	return jsonify({"result": "ok"})


@app.route('/clone', methods=['POST'])
def clone():
	data = request.json
	img_data = data['image']
	clone_pt = data['clone_pt']
	target_pt = data['target_pt']
	radius = int(data['radius'])

	# Convertir l'image de base64 en image OpenCV
	img_bytes = io.BytesIO(base64.b64decode(img_data))
	pil_image = Image.open(img_bytes)
	image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
	clone = image.copy()

	# Appliquer le clonage avec mélange des bords
	apply_clone_with_blending(image, clone, clone_pt, target_pt, radius)

	# Convertir l'image modifiée en base64 pour la réponse
	_, buffer = cv2.imencode('.jpg', clone)
	img_str = base64.b64encode(buffer).decode('utf-8')

	return jsonify({'image': img_str})


@app.route('/saveimg/<int:id>', methods=['POST'])
@login_required
def saveimg(id):
	if request.method == 'POST':
		data = request.json
		section = data.get('section')
		imgisbefore = data.get('imgIsBefore')

		# Récupérer l'image base64 et la convertir en une image Pillow
		image_data = data.get('image')
		image_bytes = base64.b64decode(image_data.split(',')[1])
		image = Image.open(io.BytesIO(image_bytes))

		# Créer un objet ImageDraw pour dessiner sur l'image
		draw = ImageDraw.Draw(image)

		# Récupérer les blocs de texte et les ajouter sur l'image
		text_blocks = data.get('textBlocks', [])
		line_height_factor = 1.5  # Facteur de hauteur de ligne pour correspondre à la `line-height` de l'interface web
		for block in text_blocks:
			content = block['content']
			x = block['x']
			y = block['y']
			width = block['width']
			height = block['height']
			sizefont = block['sizefont']

			# Utiliser une police par défaut (ou charger une autre police si nécessaire)
			try:
				font_path = "arial.ttf"
				font = ImageFont.truetype(font_path, size=int(sizefont))
			except IOError:
				font = ImageFont.load_default()

			# Diviser le texte en lignes en respectant les retours à la ligne explicites
			wrapped_lines = []
			for line in content.split('\n'):
				current_line = ""
				for word in line.split():
					# Ajouter chaque mot à la ligne actuelle
					test_line = current_line + (" " if current_line else "") + word
					# Calculer la largeur de la ligne actuelle si le mot est ajouté
					line_width = draw.textbbox((0, 0), test_line, font=font)[2]
					# Si la largeur dépasse le cadre, sauvegarder la ligne actuelle et commencer une nouvelle
					if line_width > width:
						wrapped_lines.append(current_line)
						current_line = word
					else:
						current_line = test_line

				# Ajouter la dernière ligne de chaque paragraphe (segment séparé par '\n')
				if current_line:
					wrapped_lines.append(current_line)
				# Ajouter une ligne vide après un retour à la ligne explicite
				wrapped_lines.append("")

			# Calculer la position pour commencer à dessiner le texte
			text_x = x
			text_y = y

			# Dessiner chaque ligne de texte dans le cadre avec la `line-height` de 1.1
			for line in wrapped_lines:
				if line.strip() != "":
					line_bbox = draw.textbbox((0, 0), line, font=font)
					line_width = line_bbox[2] - line_bbox[0]
					# Dessiner le texte centré horizontalement à l'intérieur du cadre
					draw.text((text_x + (width - line_width) / 2, text_y), line, fill="black", font=font)
					# Déplacer le curseur de dessin vers la ligne suivante en utilisant `line-height`
					text_y += (line_bbox[3] - line_bbox[1]) * line_height_factor

		# Convertir l'image Pillow en base64 pour l'utiliser dans le document Word
		buffered = io.BytesIO()
		image.save(buffered, format="PNG")
		img_str = base64.b64encode(buffered.getvalue()).decode()

		# Charger ou créer un document Word
		files = os.listdir(os.path.join(app.config['UPLOAD_FOLDER'], str(id)))
		targetfile = max(files, key=len)  # Récupère le fichier avec le nom le plus long

		if targetfile:
			targetdoc = Document(os.path.join(app.config['UPLOAD_FOLDER'], str(id), targetfile))
		else:
			return render_template('404.html'), 404

		# Insérer l'image modifiée dans le document Word avec ton ConverterAPI
		ConvAPI.insert_image_from_base64(targetdoc, img_str, ParaPosition=int(section), imgisbefore=imgisbefore)

		# Sauvegarder le document Word
		targetdoc.save(os.path.join(app.config['UPLOAD_FOLDER'], str(id), targetfile))

		return redirect("/project/text/docx/" + str(id))


@app.route('/check_grammar', methods=['POST'])
def check_grammar():
	data = request.get_json()
	text = data.get("text", "")
	project_id = data.get("project_id", "")

	payload = {
		'text': text,
		'language': Project.query.filter_by(id=project_id).first().Target_Lang
	}
	response = requests.post(LANGUAGETOOL_URL, data=payload)

	if response.status_code != 200:
		return jsonify({"error": "LanguageTool server error"}), 500

	# Extraire les erreurs de grammaire et d'orthographe
	result = response.json()
	errors = [
		{
			'message': match['message'],
			'offset': match['offset'],
			'length': match['length'],
			'suggestions': [suggestion['value'] for suggestion in match['replacements']],
			'sentence': match['sentence'],
			'category': match['rule']['category']['name']
		}
		for match in result['matches']
	]

	return jsonify(errors)


@app.route("/vocab", methods=["GET", "POST"])
@login_required
def vocab():
	if request.method == "POST":
		lang = request.form['lang']
		word = request.form['word']
		grammatical_category = request.form['grammatical_category']
		gender = request.form.get('gender')
		plural = bool(request.form.get('plural'))
		description = request.form.get('description')

		new_vocab = Vocab(Lang=lang, Word=word, Grammatical_Category=grammatical_category, Gender=gender, Plural=plural,
						  Description=description)
		try:
			db.session.add(new_vocab)
			db.session.commit()
			flash("Mot ajouté au vocabulaire")
		except:
			flash("Erreur lors de l'ajout du mot")
		update_added_txt_and_restart_lt()
		return redirect("/vocab")

	vocab_list = Vocab.query.all()
	return render_template('vocab.html', vocab_list=vocab_list)


@app.route("/vocab/delete/<int:id>")
@login_required
def delete_vocab(id):
	vocab_entry = Vocab.query.get_or_404(id)
	try:
		db.session.delete(vocab_entry)
		db.session.commit()
		flash("Mot supprimé du vocabulaire")
	except:
		flash("Erreur lors de la suppression du mot")
	update_added_txt_and_restart_lt()
	return redirect("/vocab")


@app.route("/vocab/update/<int:id>", methods=["GET", "POST"])
@login_required
def update_vocab(id):
	vocab_entry = Vocab.query.get_or_404(id)
	if request.method == "POST":
		vocab_entry.Lang = request.form['lang']
		vocab_entry.Word = request.form['word']
		vocab_entry.Grammatical_Category = request.form['grammatical_category']
		vocab_entry.Gender = request.form.get('gender')
		vocab_entry.Plural = bool(request.form.get('plural'))
		vocab_entry.Description = request.form.get('description')
		try:
			db.session.commit()
			flash("Mot mis à jour")
		except:
			flash("Erreur lors de la mise à jour du mot")
		update_added_txt_and_restart_lt()
		return redirect("/vocab")

	return render_template('update_vocab.html', vocab_entry=vocab_entry)


@app.route('/pretranslate/<int:project_id>', methods=['GET'])
@login_required
def pretranslate(project_id):
	project = Project.query.get(project_id)
	if not project:
		return jsonify({"error": "Projet non trouvé"}), 404

	if project.Extension.lower() != "docx":
		return jsonify({"error": "Le projet n'est pas au format DOCX"}), 400

	if project.Owner != str(current_user.id):
		return jsonify({"error": "Vous n'êtes pas autorisé à lancer cette tâche"}), 403

	last_task_id = redis_client.lindex(f"project:{project_id}:tasks", -1)

	if last_task_id:
		last_task_id = last_task_id.decode('utf-8')
		last_task = celery.AsyncResult(last_task_id)
		if last_task.state in ['PENDING', 'STARTED', 'PROGRESS']:
			celery.control.revoke(last_task_id, terminate=True)
			redis_client.hset(
				f"project:{project_id}:task_status",
				last_task_id,
				"revoked"
			)

	new_task = pre_translate_docx.delay(project_id)
	redis_client.rpush(f"project:{project_id}:tasks", new_task.id)

	return jsonify({'task_id': new_task.id}), 202


@app.route('/getprojecttaskstatus/<int:project_id>', methods=['GET'])
@login_required
def get_last_task_for_project(project_id):
	last_task_id = redis_client.lindex(f"project:{project_id}:tasks", -1)

	if not last_task_id:
		return {"error": "Aucune tâche trouvée pour ce projet."}

	task = pre_translate_docx.AsyncResult(last_task_id.decode('utf-8'))
	response = {
		"task_id": last_task_id.decode('utf-8'),
		"state": task.state,
		"info": task.info
	}
	return response


@app.route('/download_file/<int:project_id>/<file_type>', methods=['GET'])
@login_required
def download_file(project_id, file_type):
	project = Project.query.get_or_404(project_id)
	if project.Owner != str(current_user.id):
		abort(403)

	# Détermine le dossier du projet
	project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(project_id))
	files = [f for f in os.listdir(project_folder) if f.endswith('.docx')]

	if len(files) < 2:
		return {"error": "Les fichiers requis n'existent pas pour ce projet."}, 404

	# Identifier le fichier original et le fichier traduit
	input_file = min(files, key=len)
	output_file = max(files, key=len)

	# Sélectionner le fichier à télécharger
	if file_type == 'original':
		file_path = os.path.join(project_folder, input_file)
	elif file_type == 'translated':
		file_path = os.path.join(project_folder, output_file)
	else:
		return {"error": "Type de fichier invalide."}, 400

	# Télécharger le fichier
	return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
	if os.getenv("FLASK_ENV") != "production":
		app.run(host="127.0.0.1", port=5000, threaded=True, debug=True)
