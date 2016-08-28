import argparse

from mergeit.core.push_handler import PushHandler
from mergeit.core.shell import MergeitShell
from mergeit.core.config.config import Config
from mergeit.core.config.yaml_config_source import YamlFileConfigSource
from mergeit.scripts.common import init_logging


def run(project_config):
    config = Config(YamlFileConfigSource(project_config))
    shell = MergeitShell(config=config, push_handler_factory=PushHandler, forward=False)
    try:
        shell.cmdloop()
    except KeyboardInterrupt:
        print()


def main():
    parser = argparse.ArgumentParser(description='mergeit shell')
    parser.add_argument('-c', '--config', type=str, help='Config file')
    parser.add_argument('-l', '--log', type=str, default='/var/log/mergeit',
                        help='Logs dir')
    args = parser.parse_args()
    init_logging(args.log)
    run(args.config)


if __name__ == '__main__':
    main()
