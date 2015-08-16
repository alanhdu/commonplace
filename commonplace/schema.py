from asciidoc import AsciiDoc
from . import db

tags = db.Table("note_tag_mapping",
                db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
                db.Column("note_id", db.Integer, db.ForeignKey("note.id")))

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String, nullable=False, unique=True, index=True)
    source = db.Column(db.String)
    category = db.Column(db.String, nullable=False, index=True)
    tags = db.relationship("Tag", secondary=tags,
                           backref=db.backref("notes", lazy="dynamic"))
    path = db.Column(db.String, nullable=False, unique=True)

    created = db.Column(db.Date, nullable=False)

    def to_html(self) -> str:
        doc = AsciiDoc(self.path)
        return doc.to_html()


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, index=True)
