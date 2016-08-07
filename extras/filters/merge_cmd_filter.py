from runner import Filter


class MergeCmdFilter(Filter):

    def run(self, source_match, source_branch, target_branch):
        if '@merge' in self.push_handler.commits[0]['message']:
            return target_branch
        return None