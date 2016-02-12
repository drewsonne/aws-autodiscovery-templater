# coding=utf-8
"""
Entrypoint allowing command to be run
"""
from awsautodiscoverytemplater import parse_cli_args_into

__author__ = 'drews'


def run():
    """
    Entrypoint for cli utility
    :return:
    """
    templater = parse_cli_args_into()
    templater.run()


if __name__ == '__main__':
    run()
