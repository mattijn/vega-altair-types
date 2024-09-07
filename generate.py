"""
```bash
git clone https://github.com/vega/altair.git
cd altair
python -m venv .venv
source .venv/bin/activate
pip install -e ".[all, dev]" 
pip install pyvis
```
"""

from pathlib import Path
from typing import Any
import json
import itertools as it

import altair as alt
from tools.schemapi.utils import SchemaInfo


def load_schema(fp: Path, /) -> dict[str, Any]:
    """Reads and returns the root schema from ``fp``."""
    with fp.open(encoding="utf8") as f:
        root_schema = json.load(f)
    return root_schema


rootschema = load_schema(Path("altair/vegalite/v5/schema/vega-lite-schema.json"))

definitions: dict[str, SchemaInfo] = {}

for name in rootschema["definitions"]:
    schema = SchemaInfo({"$ref": "#/definitions/" + name}, rootschema=rootschema)
    definitions[name] = schema

# Key is the name of a definition and the value is a unique list of names of definitions
# that are children of the key definition.
graph: dict[str, list[str]] = {}


def get_children(schema_info: SchemaInfo) -> set[str]:
    children: set[str] = set()

    for prop_info in it.chain(
        schema_info.properties.values(),
        schema_info.anyOf,
        [schema_info.child(schema_info.items)] if schema_info.items else [],
    ):
        if prop_info.refname and prop_info.is_reference():
            children.add(prop_info.refname)
        else:
            children.update(get_children(prop_info))

    return children


for name, schema in definitions.items():
    graph[name] = list(get_children(schema))

with Path(f"VL v{alt.VEGALITE_VERSION} - Types.json").open("w") as f:
    json.dump(graph, f, indent=2)
from pyvis.network import Network

net = Network(select_menu=True, filter_menu=True, directed=True)
nodes_to_exclude = set()

for node in graph:
    if node not in nodes_to_exclude:
        net.add_node(node, label=node, title=node)

for node, edges in graph.items():
    if node not in nodes_to_exclude:
        for edge in edges:
            if edge not in nodes_to_exclude:
                net.add_edge(node, edge)
net.show_buttons(filter_=['physics'])
net.save_graph(f"VL v{alt.VEGALITE_VERSION} - Types graph.html")
