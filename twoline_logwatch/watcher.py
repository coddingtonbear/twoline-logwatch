import copy
import json
import logging
from multiprocessing import Process, Queue
import re
import select
import subprocess
import time

import requests


logger = logging.getLogger(__name__)


def get_processed_patterns(patterns):
    processed = {}

    for pattern_regex, message_template in patterns.items():
        processed[re.compile(pattern_regex)] = message_template

    return processed


def watcher_thread(filepath, raw_patterns, queue):
    patterns = get_processed_patterns(raw_patterns)

    command = 'tail --max-unchanged-stats=5 -F %s' % filepath
    logger.debug("Executing command: %s", command)
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    poller = select.poll()
    poller.register(proc.stdout)

    try:
        while True:
            if poller.poll(1):
                line = proc.stdout.readline()
                try:
                    for regex, message_template in patterns.items():
                        match = regex.match(line)
                        if match:
                            message = copy.deepcopy(message_template)
                            message['message'] = message['message'].format(
                                **match.groupdict()
                            )
                            logger.info("Line matches: %s", line)
                            queue.put(message)
                        else:
                            logger.debug("Line does not match: %s", line)
                except:
                    logger.exception(
                        "An error was encountered while processing the "
                        "logger line %s.",
                        line,
                    )
            else:
                time.sleep(0.1)
    except Exception as e:
        logger.exception('Fatal error encountered: %s', e)


class LogWatcher(object):
    def __init__(self, configuration_file, twoline_server):
        self._configuration_file = configuration_file
        self._twoline_server = twoline_server

        self.config = self.load_configuration()
        self.queue = Queue()

    def load_configuration(self):
        with open(self._configuration_file, 'r') as in_:
            return json.loads(in_.read())

    def send_message(self, message, meta=None):
        if meta is None:
            meta = {}

        message_name = 'logwatcher'
        if 'message_name' in meta:
            message_name = meta['message_name']

        payload = json.dumps(message)

        logger.debug("Sending payload: %s", payload)

        requests.put(
            self._twoline_server + '/message/%s/' % message_name,
            data=payload
        )

    def run(self):
        processes = []

        for to_watch, patterns in self.config['files'].items():
            proc = Process(
                target=watcher_thread,
                args=(
                    to_watch,
                    patterns,
                    self.queue,
                )
            )
            proc.start()
            processes.append(proc)

        self.processes = processes

        while True:
            message = self.queue.get()

            if 'meta' in message:
                meta = message.pop('meta')
            else:
                meta = {}

            self.send_message(message, meta)
