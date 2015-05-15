import glob
import json
import os
import shutil

from dateutil.parser import parse as dateparse
from html2text import html2text
from lxml import html, etree
import toolz
from slugify import slugify_filename

def process_metadata(meta):
    metadata = {}
    for node in meta.xpath("table/tr"):
        key, value = node.text_content().split(":", maxsplit=1)

        if key == "Created":
            metadata["created"] = dateparse(value).ctime()
        elif key == "Updated":
            metadata["updated"] = dateparse(value).ctime()
        elif key == "Tags":
            metadata["tags"] = value.split(", ")
        elif key == "Source":
            metadata["source"] = value
        elif key in {"Author", "Location"}:
            pass
        else:
            raise KeyError(key + " not handled") 
    return metadata

def process(note_name, evernote="data/_evernote_raw"):
    files_path = note_name + "_files/"
    with open(os.path.join(evernote, note_name + ".html")) as fin:
        root = html.fromstring(fin.read())

    title = slugify_filename(root.xpath("head/title")[0].text)
    meta, data = root.xpath("body/div")

    metadata = process_metadata(meta)

    for a in data.xpath("//a"):
        if 'href' in a.attrib and files_path in a.attrib["href"]:
            href = a.attrib["href"].replace(files_path, "_files/")
            a.attrib["href"] = href

    for img in data.xpath("//a"):
        if 'src' in img.attrib and files_path in img.attrib["src"]:
            src = img.attrib["src"].replace(files_path, "_files/")
            img.attrib = src

    if "source" in metadata:
        div = data.xpath("div")[0]
        if div.text is not None:
            text = div.text
        elif div.xpath("div"):
            text = etree.tostring(div.xpath("div")[0]).decode()
            text = html2text(text)
        else:
            text = ""
        metadata["clip"] = html2text(etree.tostring(div).decode())
    else:
        text = html2text(etree.tostring(data).decode())

    title = slugify_filename(title)

    path = os.path.join("data/raw", 'misc', title)
    if not os.path.exists(path):
        os.makedirs(path)

    with open(os.path.join(path, "notes.md"), "w") as fout:
        fout.write(text)
    with open(os.path.join(path, "metadata.json"), "w") as fout:
        new = toolz.keyfilter(lambda u: u != "clip", metadata)
        json.dump(new, fout)
    if "clip" in metadata:
        with open(os.path.join(path, "clip.md"), "w") as fout:
            fout.write(metadata["clip"])

    if os.path.isdir(os.path.join(evernote, files_path)):
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
