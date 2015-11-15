from argparse import ArgumentParser
import logging
import sys

from .watcher import LogWatcher


logger = logging.getLogger(__name__)


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = ArgumentParser()
    parser.add_argument('configuration_file', nargs='?')
    parser.add_argument('twoline_server', nargs='?')
    parser.add_argument('--loglevel', default='INFO')

    options = parser.parse_args(args)

    logging.basicConfig(level=logging.getLevelName(options.loglevel))

    manager = LogWatcher(options.configuration_file, options.twoline_server)
    manager.run()
