import json

from flask import Blueprint, request, redirect, url_for
import toolz
import ipdb

from thinker import db, Note, Tag

api = Blueprint('api', __name__)


def _pick(whitelist, d):
    return toolz.keyfilter(lambda u: u in whitelist, d)

def _update_note(note, request):
    whitelist = {"title", "text", "clip", "source", "category"}
    for key, value in _pick(whitelist, request.form).items():
        setattr(note, key, value)

    tags = set(json.loads(request.form["tags"].replace("'", '"')))

    for tag in note.tags:
        if tag.name not in tags:
            note.tags.remove(tag)
        else:
            tags.remove(tag.name)

    for tag in tags:
        t = db.session.query(Tag).filter(Tag.name == tag).first()
        if t is None:
            t = Tag(name=tag)
        note.tags.append(t)

    db.session.add(note)
    db.session.commit()


@api.route("/note/<int:note_id>", methods=["POST"])
def update_note(note_id):
    note = Note.query.get(note_id)
    _update_note(note, request)

    return redirect(url_for("show_note", note_id=note.id))

@api.route("/note/new", methods=["PUT"])
def create_note():
    note = Note()
    _update_note(note, request)

    return redirect(url_for("show_note", note_id=note.id))
