import os
import re

from structlog import get_logger
from git import Repo
from git.exc import GitCommandError


class RepoManager():

    def __init__(self, name, uri, merge_workspace):
        self.name = name
        self.uri = uri
        self.merge_workspace = merge_workspace
        self.logger = get_logger(repo=self.get_name())
        self.repo = self.get_repo()

    def get_repo(self):
        path = self.get_path()
        if os.path.exists(path):
            self.logger.info('found_repo')
            return Repo(path)
        self.logger.info('cloning_repo')
        return Repo.clone_from(self.uri, path)

    def fresh_checkout(self, target, source):
        """Do a full reset of the working dir and checkout fresh branch from remote"""
        self.logger.debug('fetch')
        self.fetch()
        self.logger.debug('reset')
        self.repo.git.reset('--hard')
        self.logger.debug('clean')
        self.repo.git.clean('-df')
        try:
            self.logger.debug('checkout', branch=target)
            self.repo.git.checkout(target)
        except GitCommandError:
            self.logger.debug('checkout_failed')
            self.logger.debug('checkout', branch=source)
            self.repo.git.checkout(source)
            self.logger.debug('checkout_b', branch=target)
            self.repo.git.checkout('-b', target)
        else:
            target = '{}/{}'.format(self.repo.remote().name, target)
            self.logger.debug('reset', branch=target)
            # self.repo.remote().pull(target_branch)
            self.repo.git.reset('--hard', target)

    def merge(self, source, target):
        """Merge self.branch into target_branch"""
        self.logger.info('merge_start', target=target)
        self.logger.info('checkout', branch=target)
        self.fresh_checkout(target, source)
        try:
            self.repo.git.merge('{}/{}'.format(self.repo.remote(), source))
        except GitCommandError:
            conflict = True
        else:
            conflict = False
        self.logger.info('merge_end', target=target, conflict=conflict)
        return conflict

    def get_name(self):
        return self.name

    def get_path(self):
        """Returns git repo merge workspace path"""
        return os.path.join(self.merge_workspace, self.get_name())

    def get_branches(self, remote=False, fetch=True):
        if fetch:
            self.fetch()
        branches = [
            re.match(r'.*[\s\*]+{}(.+)'.format(r'origin\/' if remote else ''),
                     branch).group(1)
            for branch in
            self.repo.git.branch(*(['-r'] if remote else [])).split('\n')]
        return branches

    def push(self, branch):
        self.repo.remote().push(branch)

    def fetch(self):
        self.repo.remote().fetch()
