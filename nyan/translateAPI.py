import os
import re
from io import StringIO

# from transformers import MarianTokenizer, MarianMTModel
import json
from typing import List
from translatepylocal.translators.deepl import DeeplTranslate as PersonalDeepl
from translatepylocal.translators.base import BaseTranslator
from translatepylocal.utils.request import Request
import pandas as pd
import deepl


class TranslatorAPI:
	def __init__(self, models_dir):
		self.models = {}
		self.models_dir = models_dir

	def get_supported_langs(self):
		routes = [x.split('-')[-2:] for x in os.listdir(self.models_dir)]
		return routes

	"""def load_model(self, route):
		global model
		global tok
		model = f'temp-mt-{route}'
		path = os.path.join(self.models_dir, model)
		model = MarianMTModel.from_pretrained(path)
		tok = MarianTokenizer.from_pretrained(path)
		self.models[route] = (model, tok)
		return 1, f"Successfully loaded model for {route} transation"""""

	def translate(self, provider="Nyan-CAT", settings="Less", apikey="", source="en", target="fr", formality=None, text="Hello", formatedGlossary="", prev_paragraph: str = "", next_paragraph: str = "", Context=""):
		if provider == "Nyan-CAT":  # fournisseur interne
			"""route = f'{source}-{target}'
			if not self.models.get(route):
				success_code, message = self.load_model(route)
				if not success_code:
					return message
			translated = model.generate(**tok(text, return_tensors="pt", padding=True))
			words: List[str] = [tok.decode(t, skip_special_tokens=True) for t in translated]
			return words[0]"""
			pass
		if provider == "DeepL":
			context_suppl = ', '.join([context.Text for context in Context.query.filter_by(Active=True).with_entities(Context.Text).all()])
			clean_text = re.sub(r'!\[\]\(data:image\/[a-zA-Z]+;base64,[^\)]+\)', '', text)
			if apikey != "":

				if str(formality) == "informal":
					formality = "less"
				elif str(formality) == "formal":
					formality = "more"
				elif str(formality) is None:
					formality = "default"

				translator = deepl.Translator(apikey)

				gloassary_clean_text = re.sub(r'[^\w\s]', '', clean_text).lower()

				filtered_glossary = {
					key: value
					for key, value in (item.split("\t") for item in formatedGlossary.split("\n"))
					if key.lower() in gloassary_clean_text
				}

				if not filtered_glossary:
					first_entry = next(iter(item.split("\t") for item in formatedGlossary.split("\n")), None)
					if first_entry:
						filtered_glossary[first_entry[0]] = first_entry[1]
					else:
						filtered_glossary["Hi!"] = "Salut!"

				existing_glossaries = translator.list_glossaries()
				for glos in existing_glossaries:
					translator.delete_glossary(glos.glossary_id)

				g = translator.create_glossary(
					"My glossary",
					source_lang="EN",
					target_lang="FR",
					entries=filtered_glossary,
				)
				context = f'global context: {context_suppl}, previous sentences : {prev_paragraph}, next sentences : {next_paragraph}'

				r = translator.translate_text(text=clean_text, source_lang=source, target_lang=target, glossary=g, formality=formality, context=context, model_type='prefer_quality_optimized')
				return str(r)
			else:
				translator = PersonalDeepl(request=Request())
				glossary_df = pd.read_csv(StringIO(formatedGlossary), sep="\t", header=None, names=[source.upper(), target.upper()])
				glossary = BaseTranslator.FormatedGlossary(dataframe=glossary_df, source_language=source, target_language=target)
				return translator.translate(clean_text, target, source, formality, glossary, prev_paragraph, next_paragraph).result
