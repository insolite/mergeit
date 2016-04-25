import json
from urllib.parse import urljoin

import requests

from runner import Hook


class GitlabHook(Hook):

    def create_merge_request(self, source, target, title):
        response = requests.get(urljoin(self.config['url'],
                                        '/api/v3/projects/{}/users'.format(self.config['project_id'])),
                                headers={'PRIVATE-TOKEN': self.config['token']},
                                json=dict(id=self.config['project_id'],
                                          source_branch=source,
                                          target_branch=target,
                                          assignee_id=self.push_handler.commits[0]['author']['name'], # FIXME: last commit user or smth
                                          title=title))
        last_commit_user_id = None
        for user in json.loads(response.text):
            if user['username'] == self.push_handler.commits[0]['author']['name']:
                last_commit_user_id = user['id']
        response = requests.post(urljoin(self.config['url'],
                                     '/api/v3/projects/{}/merge_requests'.format(self.config['project_id'])),
                             headers={'PRIVATE-TOKEN': self.config['token']},
                             json=dict(id=self.config['project_id'],
                                       source_branch=source,
                                       target_branch=target,
                                       assignee_id=last_commit_user_id,
                                       title=title))
        return response


class MergeRequestGitlabHook(GitlabHook):

    def run(self, source_branch, target_branch, conflicted):
        if conflicted:
            title = self.config['title'].format(source=source_branch, target=target_branch)
            self.create_merge_request(source_branch, target_branch, title)
            # TODO: check response and raise exceptions
