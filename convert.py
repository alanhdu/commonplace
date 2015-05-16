import glob
import json
import os
import shutil

from dateutil.parser import parse as dateparse
from html2text import html2text
from lxml import html, etree
import toolz
from slugify import slugify_filename

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

def process(note_name, evernote="data/_evernote_raw"):
    files_path = note_name + "_files/"
    with open(os.path.join(evernote, note_name + ".html")) as fin:
        root = html.fromstring(fin.read())

    meta, main = root.xpath("body/div")

    data = process_data(meta)
    data["title"] = root.xpath("head/title")[0].text
    data["category"] = "misc"

    for a in main.xpath("//a"):
        if 'href' in a.attrib and files_path in a.attrib["href"]:
            href = a.attrib["href"].replace(files_path, "_files/")
            a.attrib["href"] = href

    for img in main.xpath("//a"):
        if 'src' in img.attrib and files_path in img.attrib["src"]:
            src = img.attrib["src"].replace(files_path, "_files/")
            img.attrib = src

    if "source" in data:
        div = main.xpath("div")[0]
        if div.text is not None:
            data["text"] = div.text
        elif div.xpath("div"):
            text = etree.tostring(div.xpath("div")[0]).decode()
            data["text"] = html2text(text)
        else:
            data["text"] = ""
        data["clip"] = html2text(etree.tostring(div).decode())
    else:
        data["text"] = html2text(etree.tostring(main).decode())

    path = os.path.join("data/raw", 'misc', slugify_filename(data["title"]))
    if not os.path.exists(path):
        os.makedirs(path)

    with open(os.path.join(path, "data.json"), "w") as fout:
        json.dump(data, fout)

    if os.path.isdir(os.path.join(evernote, files_path)):
        newpath = os.path.join(path, "_files/")
        if os.path.isdir(newpath):
            shutil.rmtree(newpath)
        shutil.copytree(os.path.join(evernote, files_path),
                        os.path.join(path, "_files/"))
            

if __name__ == "__main__":
    for fname in glob.glob("data/_evernote_raw/*.html"):
        fname = os.path.split(fname)[-1]
        note_name = os.path.splitext(fname)[0]

        if note_name == "Evernote_index":
            continue

        try:
            process(note_name)
        except:
            print(note_name)
            raise