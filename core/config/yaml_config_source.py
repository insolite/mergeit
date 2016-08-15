import yaml
from core.config.config_source import ConfigSource


class YamlFileConfigSource(ConfigSource):

    def __init__(self, filename):
        self.filename = filename

    def get(self):
        return yaml.load(open(self.filename).read())