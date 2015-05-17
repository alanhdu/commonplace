import glob
import hashlib
import json
import re
import os
import shutil

from dateutil.parser import parse as dateparse
from html2text import html2text
from lxml import html, etree
import toolz
from slugify import slugify_filename

_link = re.compile(r"\[.*?\]\((.*?)\)", re.DOTALL)

def html2md(h):
    md = html2text(h)
    for match in _link.finditer(md):
        s = match.group(1)
        md = md.replace(s, s.replace("\n", "").replace(" ", "%20"))

    return md.strip()

def process_data(meta):
    data = {}
    for node in meta.xpath("table/tr"):
        key, value = node.text_content().split(":", maxsplit=1)

        if key == "Created":
            data["created"] = dateparse(value).ctime()
        elif key == "Updated":
            data["updated"] = dateparse(value).ctime()
        elif key == "Tags":
            data["tags"] = value.split(", ")
        elif key == "Source":
            data["source"] = value
        elif key in {"Author", "Location"}:
            pass
        else:
            raise KeyError(key + " not handled") 
    return data

def process(note_name, category="misc", evernote="data/_evernote_raw"):
    files_path = note_name + "_files/"
    fpath = "/static/files/" + hashlib.md5(note_name.encode()).hexdigest() + "/"
    with open(os.path.join(evernote, category, note_name + ".html")) as fin:
        root = html.fromstring(fin.read())

    meta, main = root.xpath("body/div")

    data = process_data(meta)
    data["title"] = root.xpath("head/title")[0].text
    data["category"] = category

    for a in main.xpath("//a"):
        if 'href' in a.attrib and files_path in a.attrib["href"]:
            href = a.attrib["href"].replace(files_path, fpath)
            a.attrib["href"] = href

    for img in main.xpath("//img"):
        if 'src' in img.attrib and files_path in img.attrib["src"]:
            src = img.attrib["src"].replace(files_path, fpath)
            img.attrib["src"] = src

    clip = None
    if "source" in data:
        div = main.xpath("div")[0]
        if div.text is not None:
            text = div.text
        elif div.xpath("div"):
            text = etree.tostring(div.xpath("div")[0]).decode()
            text = html2md(text)
        else:
            text = ""
        clip = html2md(etree.tostring(div).decode())
    else:
        text = html2md(etree.tostring(main).decode())

    path = os.path.join("data/raw", category, slugify_filename(data["title"]))
    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.isdir(os.path.join(evernote, category, files_path)):
        newpath = "thinker" + fpath
        if os.path.isdir(newpath):
            shutil.rmtree(newpath)
        shutil.copytree(os.path.join(evernote, category, files_path),
                        newpath)
        data["fpath"] = fpath

    with open(os.path.join(path, "data.json"), "w") as fout:
        json.dump(data, fout, sort_keys=True, indent=4)
    with open(os.path.join(path, "note.md"), "w") as fout:
        fout.write(text)
    if clip is not None:
        with open(os.path.join(path, "clip.md"), "w") as fout:
            fout.write(clip)

if __name__ == "__main__":
    for fname in glob.glob("data/_evernote_raw/*/*.html"):
        path, fname = os.path.split(fname)
        __, category = os.path.split(path)
        note_name = os.path.splitext(fname)[0]

        if note_name.lower() == category.lower() + "_index":
            continue

        try:
            process(note_name, category=category)
        except:
            print(note_name)
            raise
