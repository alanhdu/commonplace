import glob
import json
import re
import os
import shutil

from dateutil.parser import parse as dateparse
from lxml import html, etree
from slugify import slugify_filename
import pypandoc

_link = re.compile(r"\[.*?\]\((.*?)\)", re.DOTALL)


def html2md(h):
    md = pypandoc.convert(h, "markdown", "html")
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
    with open(os.path.join(evernote, category, note_name + ".html")) as fin:
        root = html.fromstring(fin.read())

    meta, main = root.xpath("body/div")

    data = process_data(meta)
    data["title"] = root.xpath("head/title")[0].text
    data["category"] = category

    for a in main.xpath("//a"):
        if 'href' in a.attrib and files_path in a.attrib["href"]:
            href = a.attrib["href"].replace(files_path, "_files/")
            a.attrib["href"] = href

    for img in main.xpath("//img"):
        if 'src' in img.attrib and files_path in img.attrib["src"]:
            src = img.attrib["src"].replace(files_path, "_files/")
            img.attrib["src"] = src

    text = html2md(etree.tostring(main).decode())

    path = os.path.join("data/raw", category, slugify_filename(data["title"]))
    if not os.path.exists(path):
        os.makedirs(path)

    if os.path.isdir(os.path.join(evernote, category, files_path)):
        if os.path.isdir(path):
            shutil.rmtree(path)
        old_path = os.path.join(evernote, category, files_path)
        shutil.copytree(old_path, path + "/_files/")

    with open(os.path.join(path, "data.json"), "w") as fout:
        json.dump(data, fout, sort_keys=True, indent=4)
    with open(os.path.join(path, "note.md"), "w") as fout:
        fout.write(text)

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
