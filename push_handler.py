import logging
import re
import os
from importlib import import_module

from git import Repo
from git.exc import GitCommandError
from exceptions import MergeCancel

from logging_extras import ContextAdapter
from runner import Filter, Hook


APPLICATION_NAME = 'mergeit'
DEFAULT_REMOTE = 'origin'


class PushHandler():

    def __init__(self, config, name, branch, uri, commits):
        self.config = config
        self.name = name
        self.branch = branch
        self.uri = uri
        self.commits = commits # TODO: generic format, not gitlab hook
        self.logger = ContextAdapter(logging.getLogger(__name__),
                                     dict(repo=self.name,
                                          source=self.branch))
        self.repo = self.get_repo()
        self.filters = {}
        self.hooks = {}
        self.init_runners()

    def get_repo(self):
        path = self.get_path()
        if os.path.exists(path):
            self.logger.info('found_repo')
            return Repo(path)
        self.logger.info('cloning_repo')
        return Repo.clone_from(self.uri, path)

    def init_runners(self):
        """Import all configured filter modules"""
        self.logger.info('configuring_runners')
        for config_key, runner_base_class, dst in (('filters_def', Filter, self.filters), # TODO: refactor it
                                                   ('hooks_def', Hook, self.hooks)):
            for name, runner_data in self.config.get(config_key, {}).items():
                runner_kwargs = runner_data.copy()
                module_name, class_name = runner_kwargs.pop('module').rsplit('.', 1)
                module = import_module(module_name)
                runner_class = getattr(module, class_name)
                if issubclass(runner_class, runner_base_class):
                    dst[name] = runner_class(self, **runner_kwargs)

    def fresh_checkout(self, target_branch):
        """Do a full reset of the working dir and checkout fresh branch from remote"""
        self.logger.debug('fetch')
        self.repo.remote().fetch()
        self.logger.debug('reset')
        self.repo.git.reset('--hard')
        self.logger.debug('clean')
        self.repo.git.clean('-df')
        try:
            self.logger.debug('checkout', branch=target_branch)
            self.repo.git.checkout(target_branch)
        except GitCommandError:
            self.logger.debug('checkout_failed')
            self.logger.debug('checkout', branch=self.branch)
            self.repo.git.checkout(self.branch)
            self.logger.debug('checkout_b', branch=target_branch)
            self.repo.git.checkout('-b', target_branch)
        else:
            target = '{}/{}'.format(self.repo.remote().name, target_branch)
            self.logger.debug('reset', branch=target)
            # self.repo.remote().pull(target_branch)
            self.repo.git.reset('--hard', target)

    def merge(self, target_branch):
        """Merge self.branch into target_branch"""
        self.logger.info('merge_start', target=target_branch)
        self.logger.info('checkout', branch=target_branch)
        self.fresh_checkout(target_branch)
        try:
            self.repo.git.merge('{}/{}'.format(self.repo.remote(), self.branch))
        except GitCommandError:
            conflict = True
        else:
            conflict = False
        self.logger.info('merge_end', target=target_branch, conflict=conflict)
        return conflict

    def process_merge_pair(self, source_match, target_branch, filters, hooks):
        """Execute pre-filters, merge source branch into target branch and execute post-filters"""
        self.logger.info('merge_pair', target=target_branch)
        try:
            self.logger.info('filters_start')
            for filter_name in filters:
                self.logger.info('running_filter', name=filter_name)
                target_branch = self.filters[filter_name].run(source_match, self.branch, target_branch)
                self.logger.info('new_target_branch', target=target_branch)
                if not target_branch:
                    break
            self.logger.info('filters_end', target=target_branch)
            if target_branch:
                conflict = self.merge(target_branch)
            else:
                raise MergeCancel
            self.logger.info('hooks_start')
            for hook_name in hooks:
                self.logger.info('running_hook', name=hook_name)
                self.hooks[hook_name].run(self.branch, target_branch, conflict)
            self.logger.info('hooks_end')
        except MergeCancel:
            self.logger.info('merge_cancel', target=target_branch)
        else:
            self.logger.info('push', branch=target_branch)
            self.repo.remote().push(target_branch)

    def handle(self):
        """Handle push event. Parse source branch for all patterns
        and run merge_pair() for all corresponding targets

        """
        self.logger.info('handle')
        global_filters = self.config.get('filters', [])
        global_hooks = self.config.get('hooks', [])
        variables = self.config.get('variables', {})
        for source_branch_regexp, target_rule in self.config['dependencies'].items():
            source_branch_regexp = source_branch_regexp.format(**variables)
            source_match = re.match(source_branch_regexp, self.branch)
            self.logger.info('source_match', match=bool(source_match), regexp=source_branch_regexp)
            if source_match:
                for target_branch in target_rule['targets']:
                    target_branch = target_branch.format(**variables)
                    self.process_merge_pair(source_match,
                                            target_branch,
                                            global_filters + target_rule.get('filters', []),
                                            global_hooks + target_rule.get('hooks', []))

    def get_path(self):
        """Returns git repo merge workspace path"""
        return os.path.join(self.config['merge_workspace'], self.name)

    def get_branches(self, remote=False):
        self.repo.remote().fetch()
        branches = [re.match(r'[\s\*]+{}(.+)'.format(r'origin\/' if remote else ''), branch).group(1)
                    for branch in self.repo.git.branch(*(['-r'] if remote else [])).split('\n')]
        return branches
