from flask import Flask, render_template, abort
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
uri = "sqlite:////home/alan/workspace/commonplace/test.db"
app.config["SQLALCHEMY_DATABASE_URI"] = uri
db = SQLAlchemy(app)

from .schema import Note, Tag, Annotation, Link, tags   # noqa
from .api import api  # noqa

app.register_blueprint(api, url_prefix="/api")


@app.route("/")
def index():
    return render_template("base.html")

@app.route("/note/<int:note_id>/")
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


@app.route("/category/<category>")
@app.route("/category/")
def show_category(category=None):
    if category is None:
        count = db.func.count(Note.category).label("count")
        query = db.session.query(Note.category, count) \
                          .group_by(Note.category) \
                          .order_by(db.desc("count"))
        return render_template("categories.html", categories=query)
    else:
        notes = Note.query.filter(Note.category == category)
        if not notes.first():
            abort(404)
        return render_template("category.html", category=category, notes=notes)
