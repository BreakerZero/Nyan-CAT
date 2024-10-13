import os
from io import StringIO

from transformers import MarianTokenizer, MarianMTModel
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

	def load_model(self, route):
		global model
		global tok
		model = f'temp-mt-{route}'
		path = os.path.join(self.models_dir, model)
		model = MarianMTModel.from_pretrained(path)
		tok = MarianTokenizer.from_pretrained(path)
		self.models[route] = (model, tok)
		return 1, f"Successfully loaded model for {route} transation"

	def translate(self, provider="Nyan-CAT", settings="Less", apikey="", source="en", target="fr", formality=None, text="Hello", formatedGlossary="", prev_paragraph: str = "", next_paragraph: str = ""):
		if provider == "Nyan-CAT":  # fournisseur interne
			route = f'{source}-{target}'
			if not self.models.get(route):
				success_code, message = self.load_model(route)
				if not success_code:
					return message
			translated = model.generate(**tok(text, return_tensors="pt", padding=True))
			words: List[str] = [tok.decode(t, skip_special_tokens=True) for t in translated]
			return words[0]
		if provider == "DeepL":
			if apikey != "":  # si une clé est saisie
				if str(formality) == "informal":
					formality = "less"
				elif str(formality) == "formal":
					formality = "more"
				elif str(formality) is None:
					formality = "default"
				translator = deepl.Translator(apikey)
				dictionnary = dict(item.split("\t") for item in formatedGlossary.split("\n"))
				g = translator.create_glossary(
					"My glossary",
					source_lang="EN",
					target_lang="FR",
					entries=dictionnary,
				)
				r = translator.translate_text(text=text, source_lang=source, target_lang=target, glossary=g, formality=formality)
				return str(r)
			else:  # si aucune clé n'a été saisie
				translator = PersonalDeepl(request=Request())
				glossary_df = pd.read_csv(StringIO(formatedGlossary), sep="\t", header=None, names=[source.upper(), target.upper()])
				glossary = BaseTranslator.FormatedGlossary(dataframe=glossary_df, source_language=source, target_language=target)
				return translator.translate(text, target, source, formality, glossary, prev_paragraph, next_paragraph).result
