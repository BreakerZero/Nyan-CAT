#!/usr/bin/env python3
import docx
from htmldocx import HtmlToDocx

docout = docx.Document("myexemple.docx")
new_parser = HtmlToDocx()
html = '<h3><strong>dff</strong></h3>'
temp = new_parser.parse_html_string(html)
out_para = docout.paragraphs[0]
out_para.text = ""
for run in temp.paragraphs[0].runs:
    output_run = out_para.add_run(run.text)
    # Run's font data
    output_run.style = run.style
    # Run's color data
    output_run.font.color.rgb = run.font.color.rgb
    # Run's bold data
    output_run.bold = run.bold
    # Run's italic data
    output_run.italic = run.italic
    # Run's underline data
    output_run.underline = run.underline
    out_para.style.name =temp.paragraphs[0].style.name

toshearch = "dffzrzu"
popfile =  open("database/pop_french.txt", 'r', encoding="utf-8")
popword = [line.split('\n') for line in popfile.readlines()]
matching = [i for i in popword if i[0].startswith(toshearch)]
if matching == None:
    globalfile = open("database/french.txt", 'r', encoding="utf-8")
    word = [line.split('\n') for line in globalfile.readlines()]
    matching = [i for i in popword if i[0].startswith(toshearch)]
try:
    if matching[0][0] == toshearch:
        try:
            print (matching[1][0])
        except:
            print("null")
    else:
        print(matching[0][0])
except:
    print("null")




temp.save("temp.docx")
docout.save("myexemple.docx")
