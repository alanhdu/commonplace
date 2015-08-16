from flask import Flask, render_template, abort
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
uri = "sqlite:////home/alan/workspace/commonplace/test.db"
app.config["SQLALCHEMY_DATABASE_URI"] = uri
db = SQLAlchemy(app)

from .schema import Note, Tag, tags   # noqa


@app.route("/")
def index():
    return render_template("base.html")

@app.route("/note/<int:note_id>/")
def show_note(note_id):
    note = Note.query.get_or_404(note_id)
    return render_template("note.html", note=note)

@app.route("/tag/")
def list_tags():
    count = db.func.count(tags.columns.note_id)
    query = db.session.query(Tag, count) \
                      .join(tags) \
                      .group_by(Tag) \
                      .order_by(count)
    return render_template("tags.html", tags=query)

@app.route("/tag/<tag_name>")
def show_tag(tag_name):
    tag = Tag.query.filter(Tag.name == tag_name).first_or_404()
    return render_template("tag.html", tag=tag)

@app.route("/category/")
def list_categories():
    count = db.func.count(Note.category)
    query = db.session.query(Note.category, count) \
                      .group_by(Note.category) \
                      .order_by(count)
    return render_template("categories.html", categories=query)


@app.route("/category/<category>")
def show_category(category):
    notes = Note.query.filter(Note.category == category)
    if not notes:
        abort(404)
    return render_template("category.html", category=category, notes=notes)
