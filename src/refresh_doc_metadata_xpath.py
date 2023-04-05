import re
from layman.common.metadata import PROPERTIES
from layman.layer.micka.csw import METADATA_PROPERTIES as LAYER_PROPERTIES
from layman.map.micka.csw import METADATA_PROPERTIES as MAP_PROPERTIES


def main():
    path_to_doc = '/code/doc/metadata.md'

    prop_names = set(PROPERTIES.keys())

    with open(path_to_doc, encoding="utf-8") as file:
        md_lines = file.readlines()

    prop_pattern = re.compile(r"^###\s*([a-z0-9_]+)\s*$")

    md_lines_out = []

    prop_name = None
    layer_xpath = False
    map_xpath = False
    for line in md_lines:
        prop_match = prop_pattern.match(line)
        if prop_match:
            if prop_name is not None:
                assert layer_xpath == (
                    prop_name in LAYER_PROPERTIES), f"{layer_xpath}, {prop_name in LAYER_PROPERTIES}, {prop_name}"
                assert map_xpath == (
                    prop_name in MAP_PROPERTIES), f"{map_xpath}, {prop_name in MAP_PROPERTIES}, {prop_name}"
                prop_names = prop_names - {prop_name}
            prop_name = prop_match.group(1)
            layer_xpath = False
            map_xpath = False
            # print(f"prop_name={prop_name}")
        # prop = PROPERTIES[prop_name]
        if prop_name and line.startswith("XPath for Layer:"):
            # print(f"line.startswith('XPath for Layer:': {line}")
            layer_prop = LAYER_PROPERTIES[prop_name]
            line = f"XPath for Layer: `{layer_prop['xpath_parent']}{layer_prop['xpath_property'][1:]}{layer_prop['xpath_extract'][1:]}`\n"
            layer_xpath = True
        elif prop_name and line.startswith("XPath for Map:"):
            # print(f"line.startswith('XPath for Map:': {line}")
            map_prop = MAP_PROPERTIES[prop_name]
            line = f"XPath for Map: `{map_prop['xpath_parent']}{map_prop['xpath_property'][1:]}{map_prop['xpath_extract'][1:]}`\n"
            map_xpath = True
        md_lines_out.append(line)

    if prop_name is not None:
        assert layer_xpath == (
            prop_name in LAYER_PROPERTIES), f"{layer_xpath}, {prop_name in LAYER_PROPERTIES}, {prop_name}"
        assert map_xpath == (prop_name in MAP_PROPERTIES), f"{map_xpath}, {prop_name in MAP_PROPERTIES}, {prop_name}"
        prop_names = prop_names - {prop_name}

    assert len(prop_names) == 0

    with open(path_to_doc, 'w', encoding="utf-8") as file:
        for line in md_lines_out:
            file.write(line)


if __name__ == "__main__":
    main()
