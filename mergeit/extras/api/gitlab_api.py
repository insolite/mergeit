import json
from urllib.parse import urljoin

import requests


class GitlabApi:

    def __init__(self, url, project_id, token):
        self.url = url
        self.project_id = project_id
        self.token = token

    def get_url(self, url):
        return urljoin(self.url, url)

    def get_last_commit_user_id(self, commits):
        response = requests.get(self.get_url('/api/v3/projects/{}/users'.format(self.project_id)),
                                headers={'PRIVATE-TOKEN': self.token})
        last_commit_user_id = None
        if commits:
            for user in json.loads(response.text):
                if user['username'] == commits[0]['author']['name']:
                    last_commit_user_id = user['id']
        return last_commit_user_id

    def create_merge_request(self, source, target, title, last_commit_user_id=None):
        response = requests.post(self.get_url('/api/v3/projects/{}/merge_requests'.format(self.project_id)),
                                 headers={'PRIVATE-TOKEN': self.token},
                                 json=dict(id=self.project_id,
                                           source_branch=source,
                                           target_branch=target,
                                           assignee_id=last_commit_user_id,
                                           title=title))
        return response
