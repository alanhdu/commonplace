from collections import deque
import datetime as dt
import re

import subprocess

from . import db

tags = db.Table(
    "tags",
    db.Column("tag_id", db.Integer, db.ForeignKey("tag.id")),
    db.Column("note_id", db.Integer, db.ForeignKey("note.id"))
)

_annotate_begin = re.compile(r"\|@\d+\|")
_annotate_end = re.compile(r"\|@\|")
_annotate = re.compile(r"\|@(\d+)\|(.*?)\|@\|", re.DOTALL)


class Note(db.Model):
    __tablename__ = "note"
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String, nullable=False, unique=True, index=True)
    source = db.Column(db.String)
    category = db.Column(db.String, nullable=False, index=True)
    tags = db.relationship("Tag", secondary=tags,
                           backref=db.backref("notes", lazy="dynamic"))
    path = db.Column(db.String, nullable=False, unique=True)

    created = db.Column(db.Date, nullable=False)
    updated = db.Column(db.Date, nullable=False)

    @property
    def markdown(self):
        with open(self.path) as fin:
            s = fin.read()
        return _annotate_begin.sub("", _annotate_end.sub("", s))

    @property
    def html(self):
        s = deque()

        args = ["scholdoc", "-t", "html", "--no-standalone", self.path]
        html = subprocess.check_output(args).decode()
        prev = 0
        for match in _annotate.finditer(html):
            num = int(match.group(1))
            query = Annotation.query.filter(Annotation.source == self,
                                            Annotation.number == num)
            annotation = query.first()
            start, end = match.start(), match.end()

            s.append(html[prev:start])
            s.append("<span class='marginnote'>")
            s.append(annotation.text)
            s.append("</span><mark>")
            s.append(match.group(2))
            s.append("</mark>")

            prev = end
        s.append(html[prev:])
        html = "".join(s)

        for i in range(5, 0, -1):
            html = html.replace("<h{}".format(i), "<h{}".format(i + 1))

        return html

    def offset(self, start):
        return (sum(map(len, _annotate_begin.findall(self.text[:start]))) +
                sum(map(len, _annotate_end.findall(self.text[:start]))))

class Tag(db.Model):
    __tablename__ = "tag"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, index=True)

class Annotation(db.Model):
    __tablename__ = "annotation"
    __table_args__ = (db.UniqueConstraint("source_id", "number"), )

    id = db.Column(db.Integer, primary_key=True)

    created = db.Column(db.DateTime, nullable=False, default=dt.datetime.now)
    updated = db.Column(db.DateTime, nullable=False, default=dt.datetime.now,
                        onupdate=dt.datetime.now)

    number = db.Column(db.Integer, index=True)
    text = db.Column(db.Text)

    source_id = db.Column(db.Integer, db.ForeignKey("note.id"), index=True)
    source = db.relationship("Note", foreign_keys=source_id,
                             backref=db.backref("annotations"))

class Link(db.Model):
    __table__name = "link"

    id = db.Column(db.Integer, primary_key=True)

    source_id = db.Column(db.Integer, db.ForeignKey("note.id"), index=True)
    dest_id = db.Column(db.Integer, db.ForeignKey("note.id"), index=True)

    source = db.relationship("Note", foreign_keys=source_id,
                             backref=db.backref("outgoing_links"))
    source = db.relationship("Note", foreign_keys=dest_id,
                             backref=db.backref("incoming_links"))
