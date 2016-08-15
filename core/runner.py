

class Runner():

    def __init__(self, push_handler, **config):
        self.push_handler = push_handler
        self.config = config

    def run(self, *args, **kwargs):
        raise NotImplementedError


class Filter(Runner):

    def run(self, source_match, source_branch, target_branch):
        raise NotImplementedError


class Hook(Runner):

    def run(self, source_branch, target_branch, conflicted):
        raise NotImplementedError
