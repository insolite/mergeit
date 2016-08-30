import os

import yaml

from .config_source import ConfigSource


def yaml_include(loader, node):
    path = node.value
    if loader:
        path = os.path.join(os.path.dirname(loader.name), path)
    with open(path) as inputfile:
        return yaml.load(inputfile)

yaml.add_constructor("!include", yaml_include)


class YamlFileConfigSource(ConfigSource):

    def __init__(self, filename):
        self.filename = filename

    def get(self):
        return yaml.load(open(self.filename))
