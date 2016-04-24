

class Runner():

    def __init__(self, project_handler, **config):
        self.project_handler = project_handler
        self.config = config

    def __call__(self, source_match, source_branch, target_branch):
        self.run(source_match, source_branch, target_branch)

    def run(self, *args, **kwargs):
        raise NotImplementedError


class Filter(Runner):

    def run(self, source_match, source_branch, target_branch):
        raise NotImplementedError


class Hook(Runner):

    def run(self, source_branch, target_branch, cancelled, conflicted):
        raise NotImplementedError
