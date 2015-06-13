import os
import sys

from dateutil.parser import parse as dateparse
import frontmatter
import toolz

from commonplace import db, Note, Tag, Annotation, Link

keys = {"title", "tags", "annotations", "created", "category", 
        "author", "source"}


def create_note(path):
    note = Note.query.filter(Note.path == path).first()
    if note is None:
        note = Note(path=path)
    with open(path) as fin:
        data = frontmatter.load(fin)

    db.session.autoflush = False

    attributes = {"title", "source", "author", "created", "updated", "tags",
                  "category", "links", "annotations"}
    bad_keys = set(data.metadata) - attributes
    if bad_keys:
        msg = "Unexpected frontmatter found on {}:\n>>> {}"
        msg = msg.format(path, bad_key)
        raise ValueError(msg)

    for key in ["title", "source", "author", "created", "updated", "category"]:
        if key in data.metadata:
            setattr(note, key, data.metadata[key])
    if note.updated is None:
        note.updated = note.created

    if "tags" in data.metadata:
        for tag_name in data.metadata["tags"]:
            tag = Tag.query.filter(Tag.name == tag_name).first()
            if tag is None:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            note.tags.append(tag)

    if "annotations" in data.metadata:
        for a in data.metadata["annotations"]:
            query = Annotation.query.filter(Annotation.source_id == note.id,
                                            Annotation.number == a["id"])
            annotation = query.first()
            if annotation is None:
                annotation = Annotation(source_id=note.id, number=a["id"])

            annotation.text = a["text"]
            db.session.add(annotation)

    db.session.add(note)
    db.session.commit()

    return ((note.id, link) for link in data.get("links", []))

def get_files():
    for path, __, files in os.walk("data/scholar/"):
        for fname in files:
            if not fname.endswith("scholmd"):
                continue
            yield os.path.join(path, fname)

if __name__ == "__main__":
    db.create_all()

    links = toolz.concat(create_note(f) for f in get_files())
    links = list(links)     # force evaluation of all Note

    for source_id, dest_title in links:
        dest = Note.query.filter(Note.title == dest_title).first()
        if dest is None:
            source = Note.query.filter(Note.id == source_id).first()
            msg = "Unknown link to '{}' in {}".format(dest_title, source.title)
            raise ValueError(msg)

        l = Link.query.filter(Link.source_id == source_id,
                              Link.dest_id == dest.id).first()
        if l is None:
            l = Link(source_id=source_id, dest_id=dest.id)
        db.session.add(l)
    db.session.commit()
