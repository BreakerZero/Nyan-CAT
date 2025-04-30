from models import *


def apply_clone_with_blending(image, clone, clone_pt, target_pt, radius):
	mask = np.zeros((radius * 2, radius * 2), dtype=np.uint8)
	cv2.circle(mask, (radius, radius), radius, 255, -1)
	# Augmenter le flou gaussien pour adoucir davantage les bords
	mask = cv2.GaussianBlur(mask, (31, 31), 0)

	for y in range(-radius, radius):
		for x in range(-radius, radius):
			if x ** 2 + y ** 2 <= radius ** 2:
				src_x = int(clone_pt['x']) + x
				src_y = int(clone_pt['y']) + y
				tgt_x = int(target_pt['x']) + x
				tgt_y = int(target_pt['y']) + y
				if (0 <= src_x < image.shape[1] and 0 <= src_y < image.shape[0] and
						0 <= tgt_x < clone.shape[1] and 0 <= tgt_y < clone.shape[0]):
					alpha = mask[y + radius, x + radius] / 255.0
					clone[tgt_y, tgt_x] = (1.0 - alpha) * image[tgt_y, tgt_x] + alpha * image[src_y, src_x]


def docx_get_ressource_in_request(request, id, namefile):
	idblock = int(request.json["ressource"])
	OriginalDocx = docx.Document(os.path.join(app.config['UPLOAD_FOLDER'], str(id), namefile))
	Html = ConverterAPI.ParaDocxToHtml(ConvAPI, OriginalDocx, idblock)
	PreviousHtml = ConverterAPI.ParaDocxToHtml(ConvAPI, OriginalDocx, idblock - 1)
	if PreviousHtml == "<p><br></p>":
		PreviousHtml = "<p></p>"
	NextHtml = ConverterAPI.ParaDocxToHtml(ConvAPI, OriginalDocx, idblock + 1)
	if NextHtml == "<p><br></p>":
		NextHtml = "<p></p>"
	return Html, PreviousHtml, NextHtml


def verify_owner(project_id):
	return str(flask_login.current_user.id) == str(Project.query.filter_by(id=project_id).first().Owner)


def manage_csv_memory(project_id):
	csv_dir = os.path.join("static", "csv")
	csv_path = os.path.join(csv_dir, f"memory{project_id}.csv")

	os.makedirs(csv_dir, exist_ok=True)

	# Crée le fichier CSV si nécessaire
	if not os.path.isfile(csv_path):
		with open(csv_path, "w") as csvfile:
			writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL, lineterminator='\n')
			project = Project.query.filter_by(id=project_id).first()
			writer.writerow([project.Source_Lang, project.Target_Lang])


def get_project_data_for_get_method(project_id):
	project = Project.query.filter_by(id=project_id).first()
	user = User.query.filter_by(id=flask_login.current_user.id).first()

	# Récupérer le chemin du dossier de projet
	project_folder = os.path.join(app.config['UPLOAD_FOLDER'], str(project_id))

	# Trouver le fichier DOCX avec le nom le plus court
	docx_files = [f for f in os.listdir(project_folder) if f.endswith('.docx')]

	if not docx_files:
		total_sections = 0  # Aucun fichier trouvé
	else:
		# Trouver le fichier avec le nom le plus court
		shortest_docx = min(docx_files, key=len)

		# Ouvrir le fichier DOCX et compter les paragraphes
		doc_path = os.path.join(project_folder, shortest_docx)
		doc = Document(doc_path)
		total_sections = len(doc.paragraphs)  # Compter les paragraphes

	return (
		project.Type,
		project.Extension,
		project.Last_Block,
		os.listdir(project_folder),
		user.KeepStyle,
		user.Autocomplete,
		user.TranslatorSettings,
		project,
		total_sections
	)


def get_project_data_for_post_method(project_id):
	project = Project.query.filter_by(id=project_id).first()
	user = User.query.filter_by(id=project.Owner).first()
	return (
		project.Type,
		project.Extension,
		project.Source_Lang,
		project.Target_Lang,
		user.TranslatorProvider,
		user.TranslatorSettings,
		user.Formality,
		user.ApiKey
	)


def get_context_paragraphs(i, parasin, direction="before"):
	context = []

	# Set the range for previous (before) or next (after) paragraphs
	if direction == "before":
		start = max(0, i - 5)
		end = i
		step = 1
	else:
		start = i + 1
		end = min(len(parasin), i + 6)
		step = 1

	# Iterate through the range to gather context paragraphs
	for j in range(start, end, step):
		para_text = parasin[j].text.strip()
		if para_text:
			context.append(para_text)

	return " ".join(context)


def Glos():  # fonction formatage glossaire
	formatedGlo = ""
	i = 0
	Gloquery = Glossary.query.order_by(Glossary.Source, Glossary.Target).with_entities(Glossary.Source,
	                                                                                   Glossary.Target).all()
	if Gloquery is None:
		return formatedGlo
	else:
		for _ in Gloquery:
			formatedGlo = formatedGlo + str(Gloquery[i][0]) + "\t" + str(Gloquery[i][1]) + "\n"
			i = i + 1
		return formatedGlo[:-1]


def update_added_txt_and_restart_lt(kill=True):
	# Récupération des mots dans la base de données
	vocab_entries = Vocab.query.all()

	# Organisation par langue pour les entrées de vocabulaire
	vocab_by_lang = {}
	for entry in vocab_entries:
		lang = entry.Lang
		if lang not in vocab_by_lang:
			vocab_by_lang[lang] = []

		# Format de l'entrée : mot;forme de base;catégorie genre nombre
		Gender = entry.Gender or "e"  # Vide si non défini
		Plural = "sp" if entry.Plural else "s"
		vocab_line = f"{entry.Word};{entry.Word};{entry.Grammatical_Category} {Gender} {Plural}".strip()
		vocab_by_lang[lang].append(vocab_line)

	# Mise à jour des fichiers `added.txt` pour chaque langue
	for lang, entries in vocab_by_lang.items():
		added_txt_path = os.path.join(ADDED_FILES_DIR, lang, "added.txt")
		backup_path = os.path.join(ADDED_FILES_DIR, lang, "added_backup.txt")

		# Sauvegarder l'original `added.txt` si non déjà fait
		if not os.path.exists(backup_path):
			os.rename(added_txt_path, backup_path)

		# Charger les données depuis le backup
		with open(backup_path, "r") as backup_file:
			original_content = backup_file.readlines()

		# Écrire l'original + les entrées de la base dans `added.txt`
		with open(added_txt_path, "w") as f:
			f.writelines(original_content)  # Ajouter le contenu d'origine
			f.write("\n")
			f.write("\n".join(entries))  # Ajouter les mots du vocab

	try:
		if system == "Linux" or system == "Darwin":
			if kill:
				run(["pkill", "-f", "languagetool-server"])
			Popen(["java", "-cp", os.path.join(LANGUAGETOOL_PATH, "languagetool-server.jar"),
			       "org.languagetool.server.HTTPServer", "--port", "8081", "--allow-origin"])
		elif system == "Windows":
			if kill:
				run(["taskkill", "/F", "/IM", "java.exe"], check=True)
			Popen(["java", "-cp", os.path.join(LANGUAGETOOL_PATH, "languagetool-server.jar"),
			       "org.languagetool.server.HTTPServer", "--port", "8081", "--allow-origin"],
			      creationflags=subprocess.CREATE_NEW_CONSOLE)  # Détache le processus sur Windows
	except Exception:
		pass


def translate_paragraph(index, para_text, proxies_queue, max_retries=float('inf'), prev_paragraph: str = "", next_paragraph: str = "", formatedGlossary="", project_id=1):
	with app.app_context():
		translation = None
		numberoftries = 0
		proxy = None

		while translation is None and numberoftries < max_retries:
			numberoftries += 1
			time.sleep(2.5)

			# Get a proxy from the queue
			try:
				proxy = proxies_queue.get_nowait()
			except:
				print(f"No proxies available for paragraph {index}")
				break

			try:
				(type, extension, source, target, provider, settings, formality, apikey) = get_project_data_for_post_method(
					project_id)
				translation = TranslatorAPI.translate(
					translator, provider, settings, apikey, source, target, formality, para_text,
					formatedGlossary, prev_paragraph, next_paragraph, Context
				).replace("\n", "")
			except Exception as e:
				logger.info(e)
			finally:
				proxies_queue.put(proxy)

		if translation is None:
			print(f"Failed to translate paragraph {index} after {max_retries} attempts.")
		if translation == '':
			return index, para_text, proxy
		print(f"Paragraph {index} translated successfully.")
		return index, translation, proxy


def test_proxy(proxy):
	try:
		response = requests.get("https://google.com/", proxies={"https": f"http://{proxy}"}, timeout=5)
		return response.status_code in [200, 429]
	except requests.RequestException:
		return False
