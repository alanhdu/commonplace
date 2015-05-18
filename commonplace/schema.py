from collections import deque
import datetime as dt
import re

from flask import url_for
import markdown

from . import db

tags = db.Table("tags",
            db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
            db.Column("note_id", db.Integer, db.ForeignKey("note.id")))

_annotate_begin = re.compile(r"\|@\d+\|")
_annotate_end = re.compile(r"\|@\|")
_annotate = re.compile(r"\|@(\d+)\|(.*?)\|@\|", re.DOTALL)

class Note(db.Model):
    __tablename__ = "note"
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String, nullable=False, unique=True)
    text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String, nullable=False, default="misc")

    created = db.Column(db.DateTime, nullable=False, default=dt.datetime.now)
    updated = db.Column(db.DateTime, nullable=False, default=dt.datetime.now,
                        onupdate=dt.datetime.now)

    source = db.Column(db.String, nullable=True)
    fpath = db.Column(db.String, nullable=True, unique=True)

    tags = db.relationship("Tag", secondary=tags,
                           backref=db.backref("notes", lazy="dynamic"))

    @property
    def markdown(self):
        return _annotate_begin.sub("", _annotate_end.sub("", self.text))

    @property
    def html(self):
        prev = 0
        s = deque()
        for match in _annotate.finditer(self.text):
            annotation = Annotation.query.get(int(match.group(1)))
            start, end = match.start(), match.end()

            s.append(self.text[prev:start])
            s.append("<mark>")
            s.append(match.group(2))
            s.append("</mark><span class='marginnote'>")
            s.append(annotation.text)
            s.append("</span>")

            prev = end
        s.append(self.text[prev:])

        return markdown.markdown("".join(s))

    def offset(self, start):
        return sum(map(len, _annotate_begin.findall(self.text[:start]))) \
               + sum(map(len, _annotate_end.findall(self.text[:start])))



class Tag(db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, index=True)

class Annotation(db.Model):
    __tablename__ = "annotation"

    id = db.Column(db.Integer, primary_key=True)

    created = db.Column(db.DateTime, nullable=False, default=dt.datetime.now)
    updated = db.Column(db.DateTime, nullable=False, default=dt.datetime.now,
                        onupdate=dt.datetime.now)

    source_id = db.Column(db.Integer, db.ForeignKey("note.id"), index=True)
    ref_id = db.Column(db.Integer, db.ForeignKey("note.id"), nullable=True)

    number = db.Column(db.Integer, index=True)
    text = db.Column(db.Text)

    source = db.relationship("Note", foreign_keys=source_id,
                          backref=db.backref("annotations"))
    ref = db.relationship("Note", foreign_keys=ref_id,
                           backref=db.backref("incoming"))

    def to_annotatejs(self):
        note = self.source
        start = note.text.find("|@{}|".format(self.id))
        end = note.text.find("|@|", start)
        offset = note.offset(start)

        return {
            "id": self.id,
            "text": self.text,
            "quote": note.markdown[start - offset: end - offset],
            "ranges": [{
                "start": "",
                "end": "",
                "startOffset": start - offset,
                "endOffset": end- - offset 
            }]
        }
