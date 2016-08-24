from mergeit.core.runner import Hook
from mergeit.extras.api.gitlab_api import GitlabApi


class ConflictMergeRequestGitlabHook(Hook):

    def __init__(self, push_handler, **config):
        super().__init__(push_handler, **config)
        # TODO: DI
        self.gitlab_api = GitlabApi(self.config['url'],
                                    self.config['project_id'],
                                    self.config['token'])

    def run(self, source_branch, target_branch, conflicted):
        if conflicted:
            title = self.config['title'].format(source=source_branch, target=target_branch)
            last_commit_user_id = self.gitlab_api.get_last_commit_user_id(self.push_handler.commits)
            self.gitlab_api.create_merge_request(source_branch, target_branch, title, last_commit_user_id)
            # TODO: check response and raise exceptions
