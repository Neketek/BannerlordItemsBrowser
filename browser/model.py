from __future__ import annotations
import re
import yaml
import yaml.dumper
import yaml.loader
from xml.etree import ElementTree as XML
from xml.etree.ElementTree import Element as XMLNode
from typing import Tuple, Iterable, Dict, List
import os


ITEM_NAME_PARSE_RE = re.compile(r"\{=.+\}(.+)")
SOURCES_FILENAME = "sources.yml"


class Item:

    id: str
    name: str
    culture: str
    type: str
    material: str

    @classmethod
    def from_xml_node(cls, node: XMLNode):
        item = cls()
        item.id = cls.parse_id(node)
        item.name = cls.parse_name(node)
        item.culture = cls.parse_culture(node)
        item.type = cls.parse_type(node)
        item.material = cls.parse_material(node)
        return item
    
    @staticmethod
    def parse_name(node: XMLNode):
        name = node.attrib["name"]
        m = ITEM_NAME_PARSE_RE.match(name)
        if not m:
            return name
        return m.groups()[0]
    
    @staticmethod
    def parse_culture(node: XMLNode):
        culture = node.attrib.get("culture", "None")
        return culture.split(".")[-1].replace("_", " ").capitalize()
    
    @staticmethod
    def parse_type(node: XMLNode):
        type = node.attrib.get("Type") or node.attrib.get("crafting_template")
        if type is None:
            raise Exception(f"Can't find item type: {node.attrib['name']}")
        return type

    @staticmethod
    def parse_material(node: XMLNode):
        value = node.find("ItemComponent/Armor")
        if value is not None:
            return value.attrib["material_type"]
        return ""

    @staticmethod
    def parse_id(node: XMLNode):
        return node.attrib["id"]
    
    def update(self, item: Item):
        if self.id != item.id:
            raise Exception(f"Can't update items with different ids {self.id}!={item.id}")
        self.name = item.name
        self.culture = item.culture
        self.material = item.material
        self.type = item.type


class Model:
    sources: Tuple[str]
    items: Tuple[Item]
    cultures: Tuple[str]
    types: Tuple[str]
    materials: Tuple[str]

    def __init__(self) -> None:
        self.items = tuple()
        self.cultures = tuple()
        self.types = tuple()
        self.materials = tuple()
        self.sources = tuple()

    def __extract_categories(self):
        materials = set()
        cultures = set()
        types = set()
        for item in self.items:
            if item.material:
                materials.add(item.material)
            cultures.add(item.culture)
            types.add(item.type)
        self.cultures = tuple(sorted(cultures))
        self.types = tuple(sorted(types))
        self.materials = tuple(sorted(materials))
    
    def __load_dir(self, source_dirname, registry: Dict[str, Item]):
        items = list()
        for dirpath, dirnames, filenames in os.walk(source_dirname):
            for filename in filenames:
                filename = os.path.join(dirpath, filename)
                items.extend(self.__load_file(filename, registry))
        return items


    def __load_file(self, source_filename, registry: Dict[str, Item]):
            items = list()

            _, ext = os.path.splitext(source_filename)
            if ext != ".xml":
                return items
    
            root = XML.parse(source_filename).getroot()
            if root.tag != "Items":
                return items
    
            for node in root:
                item = Item.from_xml_node(node)
                copy = registry.get(item.id)
                if copy is not None:
                    copy.update(item)
                else:
                    registry[item.id] = item
                    items.append(item)

            return items

    def load(self, pathes: List[str]):
        pathes = set(pathes)
        registry: Dict[str, Item] = dict()
        items: List[Item] = list()
        for path in pathes:
            if os.path.isdir(path):
                items.extend(self.__load_dir(path, registry))
            elif os.path.isfile(path):
                items.extend(self.__load_file(path, registry))
        self.items = tuple(items)
        self.__extract_categories()
        self.sources = tuple(pathes)

    def save_sources(self, filename=SOURCES_FILENAME):
        with open(filename, "wt+") as f:
            yaml.safe_dump(self.sources, f)


    def load_from_saved_sources(self, filename=SOURCES_FILENAME):
        with open(filename, "rt") as f:
            sources = yaml.safe_load(f)
            self.load(sources)

    def filter(self, culture=None, type=None, material=None) -> Iterable[Item]:
        for item in self.items:
            if culture and culture != item.culture:
                continue
            if type and type != item.type:
                continue
            if material and material != item.material:
                continue
            yield item