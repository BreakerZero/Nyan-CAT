import os
from transformers import MarianTokenizer, MarianMTModel
import json
from typing import List
from deeplprovider.translators.deepl import DeepL as PersonalDeepl
import requests
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
        model = f'opus-mt-{route}'
        path = os.path.join(self.models_dir, model)
        try:  # on vérifie que le bon modèle Helsinki est bien là
            model = MarianMTModel.from_pretrained(path)
            tok = MarianTokenizer.from_pretrained(path)
        except:
            return 0, f"Make sure you have downloaded model for {route} translation"
        self.models[route] = (model, tok)
        return 1, f"Successfully loaded model for {route} transation"

    def translate(self, provider="Nyan-CAT", settings="Less", apikey="", source="en", target="fr", formality=None, text="Hello", formatedGloassary=""):
        print("settings", settings)
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
                dictionnary = dict(item.split("\t") for item in formatedGloassary.split("\n"))
                g = translator.create_glossary(
                    "My glossary",
                    source_lang="EN",
                    target_lang="FR",
                    entries=dictionnary,
                )
                r = translator.translate_text(text=text, source_lang=source, target_lang=target, glossary=g, formality=formality)
                return str(r)
            else:  # si aucune clé n'a été sasie
                try:
                    Deepltra = PersonalDeepl()
                    re = Deepltra.translate(text, target, source, formatedGloassary, formality)
                    return re[1]
                except:
                    return "impossible"
