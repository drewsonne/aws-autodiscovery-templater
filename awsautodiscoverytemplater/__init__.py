import argparse
from awsautodiscoverytemplater.auth import AWSArgumentParser
from awsautodiscoverytemplater.command import TemplateCommand

__author__ = 'drews'


def parse_cli_args_into():
    """
    Creates the cli argparser for application specifics and AWS credentials.
    :param namespace_class: Class to instantiate and inject cli options into
    :return: A dict of values from the cli arguments
    :rtype: TemplaterCommand
    """
    cli_arg_parser = argparse.ArgumentParser(parents=[
        AWSArgumentParser(default_role_session_name='aws-autodiscovery-templater')
    ])
    main_parser = cli_arg_parser.add_argument_group('AWS Autodiscovery Templater')

    # template_location = main_parser.add_mutually_exclusive_group(required=True)
    main_parser.add_argument('--template-path', help='Path to the template to fill variables into.', required=True)
    # template_location.add_argument('--template-s3-uri', help='S3 URI to the template to fill variables into.')

    # output = main_parser.add_mutually_exclusive_group(required=True)
    # output.add_argument('--destination-path',
    #                     help='Destination for the source once the template has been rendered.')
    main_parser.add_argument('--stdout', help='Prints a json object containing the retrieves resources',
                             action='store_true',
                             default=False, required=True)

    main_parser.add_argument('--vpc-ids',
                             help='Optionally restrict the filtering to a particular list of IPs. Comma seperated list of vpc-ids.',
                             action='store_true', default=None)

    main_parser.add_argument('--filter',
                             help='Filter for ec2 instances as defined in http://boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_instances',
                             default=None,
                             nargs='+')
    main_parser.add_argument('--filter-empty',
                             help='By default, missing values are returned as null to keep private/public ip/hostname sets of equal length. This removes null values from the filter',
                             action='store_true', default=False)

    return cli_arg_parser.parse_args(namespace=TemplateCommand())
