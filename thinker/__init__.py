
from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown

app = Flask(__name__)
Markdown(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////home/alan/workspace/thinker/test.db"
db = SQLAlchemy(app)

from .schema import Note, Tag, Link

@app.route("/")
def index():
    return render_template("base.html")

@app.route("/note/<int:note_id>")
def show_note(note_id):
    note = Note.query.filter(Note.id == note_id).first()
    return render_template("note.html", note=note)
