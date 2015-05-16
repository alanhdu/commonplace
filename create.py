import glob
import json
import os

from dateutil.parser import parse as dateparse

from thinker import db, Note, Tag, Link


def create_note(path):
    with open(os.path.join(path, "data.json")) as fin:
        data = json.load(fin)
    with open(os.path.join(path, "note.md")) as fin:
        data["text"] = fin.read()
    try:
        with open(os.path.join(path, "clip.md")) as fin:
            data["clip"] = fin.read()
    except IOError:
        pass

    note = Note.query.filter(Note.title == data["title"]).first()
    if not note:
        note = Note()

    for key, value in data.items():
        if key in {"created", "updated"}:
            value = dateparse(value)
        if key not in {"tags"}:
            setattr(note, key, value)

    for tag in data.get("tags", []):
        t = Tag.query.filter(Tag.name == tag).first()
        if not t:
            t = Tag(name=tag)
            db.session.add(t)
        note.tags.append(t)

    db.session.add(note)
    
if __name__ == "__main__":
    db.create_all()
    for path in glob.glob("data/raw/*/*"):
        create_note(path)
        
    db.session.commit()
