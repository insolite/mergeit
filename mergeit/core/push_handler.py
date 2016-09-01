import re
from importlib import import_module

from structlog import get_logger

from .safe_dict import SafeDict
from .exceptions import MergeCancel


DEFAULT_REMOTE = 'origin'


class PushHandler():

    def __init__(self, config, branch, commits, repo_manager):
        self.config = config
        self.branch = branch
        self.commits = commits # TODO: generic format, not gitlab hook
        self.repo_manager = repo_manager
        self.logger = get_logger(source=self.branch)
        self.filters = {}
        self.hooks = {}
        self.init_runners()

    def init_runners(self):
        """Import all configured filter modules"""
        self.logger.info('configuring_runners')
        variables = self.config.get('variables', {})
        for config_key, dst in (('filters_def', self.filters), # TODO: refactor it
                                ('hooks_def', self.hooks)):
            for name, runner_data in self.config.get(config_key, {}).items():
                runner_kwargs = runner_data.copy()
                module_name, class_name = runner_kwargs.pop('module').rsplit('.', 1)
                module = import_module(module_name)
                runner_class = getattr(module, class_name)
                runner_kwargs = {key: val.format(**SafeDict(variables)) if isinstance(val, str) else val
                                 for key, val in runner_kwargs.items()}
                dst[name] = runner_class(self, **runner_kwargs)

    def process_merge_pair(self, source_match, target_branch, filters, hooks):
        """Execute pre-filters, merge source branch into target branch and execute post-filters"""
        self.logger.info('merge_pair', target=target_branch)
        try:
            self.logger.info('filters_start')
            for filter_name in filters:
                self.logger.info('running_filter', name=filter_name)
                target_branch = self.filters[filter_name].run(source_match, self.branch, target_branch)
                self.logger.info('new_target_branch', target=target_branch)
                if not target_branch:
                    break
            self.logger.info('filters_end', target=target_branch)
            if target_branch:
                conflict = self.repo_manager.merge(self.branch, target_branch)
            else:
                raise MergeCancel
            self.logger.info('hooks_start')
            for hook_name in hooks:
                self.logger.info('running_hook', name=hook_name)
                self.hooks[hook_name].run(self.branch, target_branch, conflict)
            self.logger.info('hooks_end')
        except MergeCancel:
            self.logger.info('merge_cancel', target=target_branch)
        else:
            self.logger.info('push', branch=target_branch)
            self.repo_manager.push(target_branch)

    def handle(self):
        """Handle push event. Parse source branch for all patterns
        and run merge_pair() for all corresponding targets

        """
        self.logger.info('handle')
        global_filters = self.config.get('filters', [])
        global_hooks = self.config.get('hooks', [])
        variables = self.config.get('variables', {})
        for source_branch_regexp, target_rule in self.config['dependencies'].items():
            source_branch_regexp = source_branch_regexp.format(**SafeDict(variables))
            source_match = re.match(source_branch_regexp, self.branch)
            self.logger.info('source_match', match=bool(source_match), regexp=source_branch_regexp)
            if source_match:
                for target_branch in target_rule['targets']:
                    target_branch = target_branch.format(**SafeDict(variables))
                    self.process_merge_pair(source_match,
                                            target_branch,
                                            global_filters + target_rule.get('filters', []),
                                            global_hooks + target_rule.get('hooks', []))
