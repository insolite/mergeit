from mergeit.core.runner import Filter


class NextVersionFilter(Filter):

    def get_version(self, branch):
        version_str = branch.lstrip('v') # FIXME: configurable branch pattern (not only "vX.X")
        try:
            version = float(version_str)
        except ValueError:
            return -1
        return version

    def run(self, source_match, source_branch, target_branch):
        branches = sorted(self.push_handler.repo_manager.get_branches(remote=True),
                          key=lambda x: self.get_version(x))
        try:
            return branches[branches.index(source_branch) + 1]
        except IndexError:
            return None