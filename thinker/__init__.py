from flask import Flask, render_template, abort
from flask.ext.sqlalchemy import SQLAlchemy
from flaskext.markdown import Markdown

app = Flask(__name__)
Markdown(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////home/alan/workspace/thinker/test.db"
db = SQLAlchemy(app)

from .schema import Note, Tag, Link, tags

@app.route("/")
def index():
    return render_template("base.html")

@app.route("/note/<int:note_id>")
def show_note(note_id):
    note = Note.query.filter(Note.id == note_id).first()
    if not note:
        abort(404)
    return render_template("note.html", note=note)

@app.route("/tag/<tag_name>")
@app.route("/tag/")
def show_tag(tag_name=None):
    if tag_name is None:
        count = db.func.count(tags.c.note_id).label("count")

        query = db.session.query(Tag, count) \
                          .join(tags) \
                          .group_by(Tag) \
                          .order_by(db.desc("count"))
        return render_template("tags.html", tags=query)
    else:
        tag = Tag.query.filter(Tag.name == tag_name).first()
        if not tag:
            abort(404)
        return render_template("tag.html", tag=tag)
