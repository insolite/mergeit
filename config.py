import yaml


class ConfigSource():

    def get(self):
        raise NotImplementedError


class YamlFileConfigSource(ConfigSource):

    def __init__(self, filename):
        self.filename = filename

    def get(self):
        return yaml.load(open(self.filename).read())


class Config():

    def __init__(self, config_source):
        super().__init__()
        self.data = {}
        self.config_source = config_source
        self.reload()

    def __getitem__(self, item):
        return self.data[item]

    def __setitem__(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def reload(self):
        config = self.config_source.get()
        try:
            self.data = config
        except KeyError:
            self.data = {}
