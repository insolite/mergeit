from mergeit.extras.api.gitlab_api import GitlabApi
from mergeit.core.runner import Filter


class MergeRequestGitlabFilter(Filter):

    def __init__(self, push_handler, **config):
        super().__init__(push_handler, **config)
        self.gitlab_api = GitlabApi(self.config['url'],
                                    self.config['project_id'],
                                    self.config['token'])

    def run(self, source_match, source_branch, target_branch):
        title = self.config['title'].format(source=source_branch, target=target_branch)
        user_id = (self.config['user_id']
                   if 'user_id' in self.config else
                   self.gitlab_api.get_last_commit_user_id(self.push_handler.commits))
        self.gitlab_api.create_merge_request(source_branch, target_branch, title, user_id)
        return None
