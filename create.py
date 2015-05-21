import glob
import json
import os

from dateutil.parser import parse as dateparse
import yaml

from commonplace import db, Note, Tag, Category


def create_note(path):
    with open(os.path.join(path, "note.scholmd")) as fin:
        data = fin.read()

    data = yaml.load(data.split("---\n")[1])

    note = Note.query.filter(Note.title == data["title"]).first()
    if not note:
        note = Note()

    note.title = data["title"]
    if "updated" in data:
        note.updated = dateparse(data["updated"])
    if "created" in data:
        note.created = dateparse(data["created"])
    for tag in data.get("tags", []):
        t = Tag.query.filter(Tag.name == tag).first()
        if t is None:
            t = Tag(name=tag)
            db.session.add(t)
        note.tags.append(t)

    category = Category.query.filter(Category.name == data["category"]).first()
    if category is None:
        category = Category(name=data["category"])
        db.session.add(category)
    note.category = category

    db.session.add(note)

if __name__ == "__main__":
    db.create_all()
    for path in glob.glob("data/temp/*/*"):
        create_note(path)

    db.session.commit()
