import os
import re
import time
from io import StringIO

from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
from translatepylocal.translators.deepl import DeeplTranslate as PersonalDeepl
from translatepylocal.translators.base import BaseTranslator
from translatepylocal.utils.request import Request
import pandas as pd
import deepl


class TranslatorAPI:
	def __init__(self, models_dir):
		self.models = {}
		self.models_dir = models_dir
		self.load_model()

	def get_supported_langs(self):
		routes = [x.split('-')[-2:] for x in os.listdir(self.models_dir)]
		return routes

	def load_model(self):
		model_id = "facebook/nllb-200-distilled-600M"
		local_path = os.path.join(self.models_dir, "nllb-600M")

		self.model = AutoModelForSeq2SeqLM.from_pretrained(local_path if os.path.isdir(local_path) else model_id)
		self.tokenizer = AutoTokenizer.from_pretrained(local_path if os.path.isdir(local_path) else model_id)

		return 1, f"✅ Chargé NLLB-600M"

	def translate(self, provider="Nyan-CAT", settings="Less", apikey="", source="en", target="fr", formality=None, text="Hello", formatedGlossary="", prev_paragraph: str = "", next_paragraph: str = "", Context="", proxy=None):
		if provider == "Nyan-CAT":  # fournisseur interne
			translator = pipeline('translation', model=self.model, tokenizer=self.tokenizer, src_lang="eng_Latn",  tgt_lang='fre_Latn')
			result = translator(text)
			return result[0]['translation_text']
		elif provider == "DeepL":
			context_suppl = ', '.join([context.Text for context in Context.query.filter_by(Active=True).with_entities(Context.Text).all()])
			clean_text = re.sub(r'!\[\]\(data:image\/[a-zA-Z]+;base64,[^\)]+\)', '', text)
			if apikey != '':
				time.sleep(3)
				if str(formality) == "informal":
					formality = "less"
				elif str(formality) == "formal":
					formality = "more"
				elif str(formality) is None:
					formality = "default"

				translator = deepl.DeepLClient(apikey, verify_ssl=False, send_platform_info=False)

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
				if proxy:
					translator = PersonalDeepl(request=Request([proxy]))
				else:
					translator = PersonalDeepl(request=Request())
				glossary_df = pd.read_csv(StringIO(formatedGlossary), sep="\t", header=None, names=[source.upper(), target.upper()])
				glossary = BaseTranslator.FormatedGlossary(dataframe=glossary_df, source_language=source, target_language=target)
				return translator.translate(clean_text, target, source, formality, glossary, prev_paragraph, next_paragraph).result
		return None
