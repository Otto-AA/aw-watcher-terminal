import unittest
from aw_watcher_terminal import main, config, message_handler

"""Outdated
import argparse
import logging
from aw_watcher_terminal.main import init_message_parser, parse_pipe_message


class TestPipeMessageParser(unittest.TestCase):
    # TODO: Update depending on specification
    sample_message = '--command ls --path /home/ --shell bash \
                      --shell-version 1.2.3'
    valid_messages = [
        '--command ls',
        '--command "ls" --path "/home/"',
        '--command "echo \\"Hello \\\\\\"World\\\\\\"\\""'
    ]
    invalid_messages = [
        '--flawed message',
        '--command "echo \\\"Hello World\\\\""'
    ]

    def setUp(self):
        init_message_parser()

    def test_valid_messages(self):
        for message in self.valid_messages:
            self.assertEqual(argparse.Namespace,
                             type(parse_pipe_message(message)))

    def test_invalid_messages(self):
        for message in self.invalid_messages:
            self.assertEqual(None, parse_pipe_message(message))

    def test_parsed_namespace(self):
        parsed = parse_pipe_message(self.sample_message)
        self.assertEqual('ls', parsed.command)
        self.assertEqual('/home/', parsed.path)
        self.assertEqual('bash', parsed.shell)
        self.assertEqual('1.2.3', parsed.shell_version)
"""

if __name__ == '__main__':
    unittest.main()
