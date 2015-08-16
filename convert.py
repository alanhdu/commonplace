import os

from commonplace import db, Note, Tag
from asciidoc import AsciiDoc

def create_note(path):
    note = Note.query.filter(Note.path == path).first()
    if note is None:
        note = Note(path=path)

    doc = AsciiDoc(path)
    doc.parse()

    fields = Note.__table__.columns.keys()

    for key, value in doc.metadata.items():
        if key in fields:
            setattr(note, key, value)

    if "tags" in doc.metadata:
        note.tags = []
        for tag_name in doc.metadata["tags"]:
            tag = Tag.query.filter(Tag.name == tag_name).first()
            if tag is None:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            note.tags.append(tag)

    db.session.add(note)
    db.session.commit()


if __name__ == "__main__":
    db.create_all()
    for path, __, files in os.walk("data/"):
        for fname in files:
            if fname.endswith(".adoc"):
                create_note(os.path.join(path, fname))
