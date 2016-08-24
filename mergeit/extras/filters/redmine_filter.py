import json
from urllib.parse import urljoin

import requests

from mergeit.core.runner import Filter


class RedmineFilter(Filter):

    def get_url(self, url):
        return urljoin(self.config['url'], url)

    def get_task(self, task_id):
        response = requests.get(self.get_url('/issues/{}.json'.format(task_id)),
                                data={'key': self.config['api_key']})
        return json.loads(response.text)['issue']

    def update_task(self, task_id, data):
        requests.put(self.get_url('/issues/{}.json'.format(task_id)),
                     json={'key': self.config['api_key'], 'issue': data})
        # TODO: return response data

    def get_statuses(self):
        response = requests.get(self.get_url('/issue_statuses.json'),
                                data={'key': self.config['api_key']})
        return json.loads(response.text)['issue_statuses']