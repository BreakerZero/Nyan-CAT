import docx
from converterAPI import ConverterAPI
t = ConverterAPI()
temp = docx.Document("temp.docx")
ConverterAPI.ParaHtmlToDocx(t, '<h1 class="ql-align-right">Je dis <em style="color: rgb(192, 80, 77);">probablement</em> parce que, n’ayant absolument aucune envie d’être associé davantage à un film dont l’absurdité défie les frontières du surréalisme, j’avais décidé de m’en dissocier complètement après avoir remis la cassette aux membres de la société cinématographique.</h1><p>testtesttesttesttesttest</p>', temp, 0, 0, "temp.docx")
ConverterAPI.ParaDocxToHtml(t, temp, 0)