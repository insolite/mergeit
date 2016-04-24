from urllib.parse import urljoin

import requests

from runner import Hook


class GitlabHook(Hook):

    def create_merge_request(self, source, target, title):
        return requests.post(urljoin(self.config['url'],
                                     '/api/v3/projects/{}/merge_requests'.format(self.config['project_id'])),
                             headers={'PRIVATE-TOKEN': self.config['token']},
                             json=dict(id=self.config['project_id'],
                                       source_branch=source,
                                       target_branch=target,
                                       assignee_id=None, # FIXME: last commit user or smth
                                       title=title))


class MergeRequestGitlabHook(GitlabHook):

    def run(self, source_branch, target_branch, cancelled, conflicted):
        if not cancelled and conflicted:
            title = self.config['title'].format(source=source_branch, target=target_branch)
            self.create_merge_request(source_branch, target_branch, title)
