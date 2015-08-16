""" Wrapper around Ruby asciidoctor functionality """

import subprocess
import json
import re

from dateutil.parser import parse as dateparse

converter = "asciidoctor"
metadata_regex = re.compile(r"^:(.*?): *(.*)$")


class AsciiDoc():
    def __init__(self, path):
        self.path = path           # keep for debugging purposes
        with open(path) as fin:
            self.text = fin.read()

    def parse(self):
        self.metadata = {}
        self.metadata["title"] = self.text[:self.text.find("\n")]

        if not self.metadata["title"].startswith("="):
            raise RuntimeError("{} does not have a title".format(self.path))
        self.metadata["title"] = self.metadata["title"][1:].strip()

        for line in self.text.split("\n"):
            m = metadata_regex.match(line)
            if m is not None:
                name, data = m.groups()
                if name == "tags":
                    data = json.loads(data)
                elif name in {"created", "updated"}:
                    data = dateparse(data)

                self.metadata[name] = data if data else None

    def to_html(self) -> str:
        p = subprocess.Popen([converter, "--out-file", "-", self.path],
                             stdout = subprocess.PIPE)
        stdout, __ = p.communicate(timeout=2)
        return stdout.decode("utf-8")
