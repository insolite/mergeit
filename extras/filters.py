import re
import unittest
import json
from urllib.parse import urljoin

import requests

from runner import Filter


class TestsFilter(Filter):

    def run(self, source_match, source_branch, target_branch):
        all_tests = unittest.TestLoader().discover(self.push_handler.config['path'], pattern='*.py')
        unittest.TextTestRunner().run(all_tests)


class RedmineFilter(Filter):

    def get_task(self, id):
        response = requests.get(urljoin(self.config['url'],
                                        '/issues/{}.json'.format(id)),
                                data={'key': self.config['api_key']})
        return json.loads(response.text)['issue']

    def update_task(self, id, data):
        response = requests.put(urljoin(self.config['url'],
                                        '/issues/{}.json'.format(id)),
                                json={'key': self.config['api_key'], 'issue': data})

    def get_statuses(self):
        response = requests.get(urljoin(self.config['url'],
                                        '/issue_statuses.json'),
                                data={'key': self.config['api_key']})
        return json.loads(response.text)['issue_statuses']


class VersionRedmineFilter(RedmineFilter):

    def run(self, source_match, source_branch, target_branch):
        task = self.get_task(source_match.groupdict()['task_id']) # TODO: compare commit message task with branch name?
        return target_branch.format(redmine_version=task['fixed_version']['name'])


class ResolveRedmineFilter(RedmineFilter):

    def run(self, source_match, source_branch, target_branch):
        if '@resolve' in self.push_handler.commits[0]['message']:
            statuses = self.get_statuses()
            resolved_status = None
            for status in statuses:
                if status['name'] == 'Resolved':
                    resolved_status = status
                    break
            if resolved_status:
                self.update_task(source_match.groupdict()['task_id'],
                                 {'status_id': resolved_status['id']})
        return target_branch


class NextVersionFilter(Filter):

    def get_version(self, branch):
        version_str = branch.lstrip('v') # FIXME: configurable branch pattern (not only "vX.X")
        try:
            version = float(version_str)
        except ValueError:
            return -1
        return version

    def run(self, source_match, source_branch, target_branch):
        branches = sorted(self.push_handler.get_branches(remote=True),
                          key=lambda x: self.get_version(x))
        try:
            return branches[branches.index(source_branch) + 1]
        except IndexError:
            return None


class MergeCmdFilter(Filter):

    def run(self, source_match, source_branch, target_branch):
        if '@merge' in self.push_handler.commits[0]['message']:
            return target_branch
        return None
