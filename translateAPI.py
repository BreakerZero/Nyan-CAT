import os
from transformers import MarianTokenizer, MarianMTModel
import json
from typing import List
from deeplprovider.translators.deepl import DeepL
import requests

class TranslatorAPI():
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
        path = os.path.join(self.models_dir,model)
        try:    #on vérifie que le bon modèle Helsinki est bien là
            model = MarianMTModel.from_pretrained(path)
            tok = MarianTokenizer.from_pretrained(path)
        except:
            return 0,f"Make sure you have downloaded model for {route} translation"
        self.models[route] = (model,tok)
        return 1,f"Successfully loaded model for {route} transation"

    def translate(self, provider="Nyan-CAT", apikey="" , source="en", target="fr", formality=None, text="Hello", formatedGloassary=""):
        if provider == "Nyan-CAT": #fournisseur interne
            route = f'{source}-{target}'
            if not self.models.get(route):
                success_code, message = self.load_model(route)
                if not success_code:
                    return message
            translated = model.generate(**tok(text, return_tensors="pt", padding=True))
            words: List[str] =[tok.decode(t, skip_special_tokens=True) for t in translated]
            return words[0]
        if provider == "DeepL":
            if apikey != "": #si une clé est saisie
                if str(formality)=="informal":
                    formality="less"
                if str(formality)=="formal":
                    formality="more"
                if str(formality)==None:
                    formality="default"
                count = requests.get("https://api-free.deepl.com/v2/usage?auth_key="+ apikey)
                count = json.loads(count.text)
                if int(count["character_count"])+ 1000 < int(count["character_limit"]):
                    re = requests.post(
                    url="https://api-free.deepl.com/v2/translate",
                    data={
                        "target_lang": target,
                        "auth_key": apikey,
                        "text": text,
                        "formality": formality,
                    },)
                    re = json.loads(re.text)
                    return re['translations'][0]['text']
                else:
                    return "La limite de votre clé API DeepL a été atteinte, veuillez utiliser une autre méthode de traduction"
            else: #si aucune clé n'a été sasie
                try:
                    Deepltra = DeepL()
                    re = Deepltra.translate(text, target, source,formatedGloassary, formality)
                    return re[1]
                except:
                    return "impossible"
            
        