import json
import re

import ipdb

from flask import Blueprint, request, redirect, url_for, abort
import toolz

from .. import db, Note, Tag, Annotation

api = Blueprint('api', __name__)


def _pick(whitelist, d):
    return toolz.keyfilter(lambda u: u in whitelist, d)

def _update_note(note, request):
    whitelist = {"title", "text", "source", "category"}
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

@api.route("/annotations/annotations/<int:annotation_id>",
           methods=["GET", "PUT", "DELETE"])
def annotation_read(annotation_id):
    annotation = Annotation.query.get(annotation_id)

    if request.method == "GET":
        return json.dumps(annotation.to_annotatejs())
    elif request.method == "DELETE":
        note = annotation.source
        db.session.delete(annotation)

        _find = re.compile(r"\|@{}\|(.*?)\|@\|".format(annotation_id),
                           re.DOTALL)
        note.text = _find.sub("\1", note.text)
        db.session.add(note)

        db.session.commit()

        return "", 204  # intentional no response
    elif request.method == "PUT":
        annotation.text = request.get_json()["text"]
        db.session.add(annotation)
        db.session.commit()

        url = url_for("api.annotation_read", annotation_id=annotation.id)
        return redirect(url)

@api.route("/annotations/annotations", methods=["POST", "GET"])
def annotation_index():
    if request.method == "GET":
        return json.dumps([annotation.to_annotatejs() 
                           for annotation in Annotation.query.all()])
    elif request.method == "POST":
        data = request.get_json()
        start = data["ranges"][0]["startOffset"]
        end = data["ranges"][0]["endOffset"]

        note = Note.query.get(data["note_id"])

        annotation = Annotation(text=data["text"], source_id=data["note_id"])
        db.session.add(annotation)
        db.session.flush()

        offset = note.offset(start)
        print(note.text[start + offset: end + offset], offset, start, end)
        note.text = "".join([note.text[:start + offset], 
                             "|@{}|".format(annotation.id),
                             note.text[start + offset: end + offset],
                             "|@|",
                             note.text[end + offset:]])
        db.session.add(note)
        db.session.commit()

        url = url_for("api.annotation_read", annotation_id=annotation.id)
        return redirect(url)

