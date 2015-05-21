import glob
import json
import shutil
import os

from dateutil.parser import parse as dateparse
from slugify import slugify_filename
import yaml

from commonplace import db, Note, Tag


def create_note(path):
    with open(os.path.join(path, "data.json")) as fin:
        data = json.load(fin)
    with open(os.path.join(path, "note.md")) as fin:
        text = fin.read().replace("\r\n", "\n")


    newpath = os.path.join("data/scholar", data["category"],
                           slugify_filename(data["title"]))
    fpath = os.path.join(path, "_files")
    fnewpath = os.path.join(newpath, "_files")

    if not os.path.exists(newpath):
        os.makedirs(newpath)

    if os.path.isdir(fpath):
        if os.path.isdir(fnewpath):
            shutil.rmtree(fnewpath)
        shutil.copytree(fpath, fnewpath)

    with open(os.path.join(newpath, "note.scholmd"), "w") as fout:
        fout.write("---\n")
        yaml.dump(data, fout, default_flow_style=False)
        fout.write("---\n")
        fout.write(text)

if __name__ == "__main__":
    db.create_all()
    for path in glob.glob("data/raw/*/*"):
        create_note(path)

    db.session.commit()
