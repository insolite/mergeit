from mergeit.extras.filters import RedmineFilter


class ResolveRedmineFilter(RedmineFilter):

    def run(self, source_match, source_branch, target_branch):
        if self.push_handler.commits and '@resolve' in self.push_handler.commits[0]['message']:
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