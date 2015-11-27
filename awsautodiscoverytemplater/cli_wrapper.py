from awsautodiscoverytemplater import parse_cli_args_into

__author__ = 'drews'


def run():
    templater = parse_cli_args_into()
    templater.run()

if __name__ == '__main__':
    run()