from settings import *

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

class Context(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	Active = db.Column(db.Boolean, nullable=False)
	Text = db.Column(db.String(500), nullable=False)

class Vocab(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	Lang = db.Column(db.String(3), nullable=False)
	Word = db.Column(db.String(100), nullable=False)
	Grammatical_Category = db.Column(db.String(50), nullable=False)  # e.g., "N", "V", "ADJ"
	Gender = db.Column(db.String(1))  # "m" for masculin, "f" for feminin
	Plural = db.Column(db.Boolean, default=False)  # True if no plural (sp)
	Description = db.Column(db.String(200))

