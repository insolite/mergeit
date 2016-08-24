from mergeit.extras.filters import RedmineFilter


class VersionRedmineFilter(RedmineFilter):

    def run(self, source_match, source_branch, target_branch):
        task = self.get_task(source_match.groupdict()['task_id']) # TODO: compare commit message task with branch name?
        return target_branch.format(redmine_version=task['fixed_version']['name'])