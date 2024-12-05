from flask import Flask, render_template, request, session, redirect, url_for
from flask_caching import Cache
from pypdf import PdfReader
import os
from openai import OpenAI


API_KEY = "" #<-- API kulcs helye
client = OpenAI(
    api_key= API_KEY,
)

app = Flask(__name__)
wsgi_app = app.wsgi_app
app.secret_key = 'supersecretkey'
cache = Cache(app, config={'CACHE_TYPE': 'simple'})


conversations = []

@app.route("/", methods=["GET", "POST"])
def index():
    status_message = "Nincs fajl feltoltve"
    question = request.form.get("question")
    if question:
        pdf = cache.get('pdf')
        if pdf:
            status_message = "Kesz"
            content = f"You are an intelligent assistant. You will receive a text and a question as a prompt. Your task is to answer the question based on the text. If the text does not contain the answer, respond with: A dokumentum nem tartalmazza a valaszt. Always answer in Hungarian. You will see the page numbers before the text in this format: /x/. Always include these at the end of the answer. Text: {pdf} Previous questions and answers: {conversations} Current question: {question}"
            messages = [ {"role": "system", "content": content} ]
            chat = client.chat.completions.create(
                model="gpt-4o-mini", messages=messages
            )
            reply = chat.choices[0].message.content
            answer = f"{reply}" if question else None
            conversations.append((question, answer))
    if 'file' in request.files:
        file = request.files['file']
        if file.filename != "":
            try:
                pdf_text = ""
                reader = PdfReader(file)
                for i in range(9):
                    page = reader.pages[i]
                    pdf_text += f"/{i+1}/" +page.extract_text() + " "
                pdf_text = pdf_text.replace("\n", " ")
                cache.set('pdf', pdf_text)
                
                status_message = "Kesz"
            except Exception as e:
                status_message = f"Hiba a fajl feldolgozasakor: {e}"
        else:
            status_message = "Nincs fajl kivalasztva."
    question = ""

    return render_template("index.html", conversations=conversations, status_message=status_message)

if __name__ == '__main__':
    import os
    HOST = os.environ.get('SERVER_HOST', 'localhost')
    try:
        PORT = int(os.environ.get('SERVER_PORT', '5555'))
    except ValueError:
        PORT = 5555
    app.run(HOST, PORT)
