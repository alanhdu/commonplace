from collections import deque
import os

import frontmatter
import toolz

from commonplace import db, Note, Tag, Annotation

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
                  "category", "annotations"}
    bad_keys = set(data.metadata) - attributes
    if bad_keys:
        msg = "Unexpected frontmatter found on {}:\n>>> {}"
        msg = msg.format(path, bad_keys)
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
            if tag not in note.tags:
                note.tags.append(tag)

    annotation_links = deque()
    if "annotations" in data.metadata:
        for a in data.metadata["annotations"]:
            query = Annotation.query.filter(Annotation.source_id == note.id,
                                            Annotation.number == a["id"])
            annotation = query.first()
            if annotation is None:
                annotation = Annotation(source=note, number=a["id"])
                print("source_id", annotation.source_id)

            db.session.add(annotation)
            if "link" in a:
                yield annotation.id, a["link"]

    db.session.add(note)
    db.session.commit()

def get_files():
    for path, __, files in os.walk("data/"):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            yield os.path.join(path, fname)

if __name__ == "__main__":
    db.create_all()

    annotation_links = toolz.concat(create_note(f) for f in get_files())
    annotation_links = deque(annotation_links)   # force db update

    for annotation_id, dest_title in annotation_links:
        dest = Note.query.filter(Note.title == dest_title).first()
        if dest is None:
            source = Note.query.filter(Note.id == source_id).first()
            msg = "Unknown link to '{}' in {}".format(dest_title, source.title)
            raise ValueError(msg)

        a = Annotation.query.filter(Annotation.id == annotation_id).first()
        a.dest_id = dest.id
        db.session.add(a)

    db.session.commit()
