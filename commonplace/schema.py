from collections import deque
import datetime as dt
import re
import os

from slugify import slugify_filename
import subprocess

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
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    tags = db.relationship("Tag", secondary=tags,
                           backref=db.backref("notes", lazy="dynamic"))

    created = db.Column(db.DateTime, nullable=False, default=dt.datetime.now)
    updated = db.Column(db.DateTime, nullable=False, default=dt.datetime.now,
                        onupdate=dt.datetime.now)
    @property
    def path(self):
        return os.path.join('data/temp', self.category.name,
                            slugify_filename(self.title), "note.scholmd")

    @property
    def markdown(self):
        with open(self.path) as fin:
            return _annotate_begin.sub("", _annotate_end.sub("", fin.read()))

    @property
    def html(self):
        prev = 0
        s = deque()

        args=  ["scholdoc", "-t", "html", "--no-standalone", self.path]
        html = subprocess.check_output(args).decode()
        for match in _annotate.finditer(html):
            annotation = Annotation.query.get(int(match.group(1)))
            start, end = match.start(), match.end()

            s.append(self.text[prev:start])
            s.append("<mark>")
            s.append(match.group(2))
            s.append("</mark><span class='marginnote'>")
            s.append(annotation.text)
            s.append("</span>")

            prev = end
        s.append(html[prev:])
        return "".join(s)

    def offset(self, start):
        return sum(map(len, _annotate_begin.findall(self.text[:start]))) \
               + sum(map(len, _annotate_end.findall(self.text[:start])))


class Tag(db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, index=True)

class Category(db.Model):
    __tablename__ = "category"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, index=True)
    notes = db.relationship("Note", backref="category", lazy="dynamic")



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

        begin = "|@{}|".format(self.id)

        start = note.text.find(begin)
        end = note.text.find("|@|", start)
        offset = note.offset(start)

        return {
            "id": self.id,
            "text": self.text,
            "quote": note.markdown[start - offset: end - offset - len(begin)],
            "ranges": [{
                "start": "",
                "end": "",
                "startOffset": start - offset,
                "endOffset": end - offset - len(begin)
            }]
        }
