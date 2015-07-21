
import markdown

class PoetryExtension(markdown.extensions.Extension):
    def extendMarkdown(self, md, md_globals):
        p = PoetryPreprocessor()
        md.preprocessors["poetry"] = p

class PoetryPreprocessor(markdown.preprocessors.Preprocessor):
    def _run(self, lines):
        in_poem = False
        for line in lines:
            if line.strip() == "<poem>":
                in_poem = True
                yield "<blockquote class='poem'>"
            elif not in_poem:
                yield line
            else:
                line = line.strip()
                if line == "</poem>":
                    in_poem = False
                    yield "</blockquote>"
                elif line.startswith(">>>"):
                    yield "<p> &mdash; {} </p>".format(line.split(">>>")[1])
                else:
                    yield "<p>{}</p>".format(line)

    def run(self, lines):
        return list(self._run(lines))

def makeExtension(*args, **kwargs):
    return PoetryExtension(*args, **kwargs)
