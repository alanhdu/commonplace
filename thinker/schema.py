import glob

from bulbs.neo4jserver import Graph, Config, NEO4J_URI
from bulbs.model import Node, Relationship
from bulbs.property import String, DateTime
from bulbs.utils import current_datetime

config = Config(NEO4J_URI, "neo4j", "testing")
graph = Graph(config)

class Tag(Node):
    element_type = "tag"
    name = String(nullable=False)

class Notes(Node):
    element_type = "note"

    title = String(nullable=False, indexed=True)
    text = String(nullable=False, indexed=True)
    category = String(nullable=False, default="misc", indexed=True)

    created = DateTime(default=current_datetime, nullable=False)
    updated = DateTime(default=current_datetime, nullable=False)

    source = String(nullable=True)
    clip = String(nullable=True, indexed=True)
    fpath = String(nullable=True)

class About(Relationship):
    label = "about"
    created = DateTime(default=current_datetime, nullable=False)

class Linked(Relationship):
    label = "linked"
    created = DateTime(default=current_datetime, nullable=False)
