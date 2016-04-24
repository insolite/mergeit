import re
import os
from importlib import import_module

from git import Repo
from git.exc import GitCommandError
from exceptions import MergeCancel

from runner import Runner


APPLICATION_NAME = 'mergeit'
DEFAULT_REMOTE = 'origin'


class PushHandler():

    def __init__(self, config, name, branch, uri, commits):
        self.config = config
        self.name = name
        self.branch = branch
        self.uri = uri
        self.commits = commits # TODO: generic format, not gitlab hook
        if os.path.exists(self.get_path()):
            self.repo = Repo(self.get_path())
        else:
            self.repo = Repo.clone_from(self.uri, self.get_path())
        self.filters = {}
        self.init_filters()

    def init_filters(self):
        """Import all configured filter modules"""
        for name, filter_data in self.config.get('filters_def', {}).items():
            filter_kwargs = filter_data.copy()
            module_name, class_name = filter_kwargs.pop('module').rsplit('.', 1)
            filter_class = getattr(import_module(module_name), class_name)
            if isinstance(filter_class, Runner):
                self.filters[name] = filter_class

    def fresh_checkout(self, target_branch):
        """Do a full reset of the working dir and checkout fresh branch from remote"""
        self.repo.remote().fetch()
        self.repo.git.reset('--hard')
        self.repo.git.clean('-df')
        try:
            self.repo.git.checkout(target_branch)
        except GitCommandError:
            self.repo.git.checkout(self.branch)
            self.repo.git.checkout('-b', target_branch)
        else:
            # self.repo.remote().pull(target_branch)
            self.repo.git.reset('--hard', '{}/{}'.format(self.repo.remote().name, target_branch))

    def merge_pair(self, source_match, target_branch, filter, hooks):
        """Execute pre-filters, merge source branch into target branch and execute post-filters"""
        try:
            for filter_name in filter:
                pre_filter = self.filters[filter_name](self)
                target_branch = pre_filter(source_match, self.branch, target_branch)
                if not target_branch:
                    break
            if target_branch:
                self.fresh_checkout(target_branch)
                try:
                    self.repo.git.merge(self.branch)
                except GitCommandError:
                    conflict = True
                else:
                    conflict = False
            else:
                raise MergeCancel
            for hook_name in hooks:
                hook = self.filters[hook_name](self, conflict)
                hook(source_match, self.branch, target_branch)
        except MergeCancel:
            pass
        else:
            self.repo.remote().push(target_branch)


    def handle(self):
        """Handle push event. Parse source branch for all patterns
        and run merge_pair() for all corresponding targets

        """
        for source_branch_regexp, target_rule in self.config['dependencies'].items():
            source_match = re.match(source_branch_regexp, self.branch)
            if source_match:
                for target_branch in target_rule['targets']:
                    self.merge_pair(source_match,
                                    target_branch,
                                    target_rule.get('filters', []),
                                    target_rule.get('hooks', []))

    def get_path(self):
        """Returns git repo merge workspace path"""
        return os.path.join(self.config['merge_workspace'], self.name)
