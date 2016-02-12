import argparse
import json
import os
from urlparse import urlparse
import re
import awsauthhelper as auth
from jinja2 import Template

__author__ = 'drews'


class TemplateCommand(argparse.Namespace):
    """
    Contains the code to generate the output from template and supplies filters for IPs
    """

    def __init__(self, **kwargs):
        self.filter_empty = False
        self.filter = None
        self.template_s3_uri = None
        self.template_path = None
        self.stdout = None
        self.destination_path = None
        self.send_output_handler = None
        self.vpc_ids = None
        super(TemplateCommand, self).__init__(**kwargs)

    def run(self):
        """
        Entrypoint to kick off the job to generate the templater
        :return:
        """
        credentials = auth.Credentials(**vars(self))
        if credentials.has_role():
            credentials.assume_role()

        #################
        # Set callbacks #
        #################

        # Set defaults in case of unforeseen bad runtime.
        send_output = self.bad_lambda
        load_template = self.bad_lambda

        # Generate output handler
        if self.send_output_handler:
            send_output = self.send_output_handler
        elif self.stdout:
            send_output = self.output_stdout
        elif self.destination_path:
            send_output = self.generate_output_file(self.destination_path)

        # Generate template loader
        if self.template_path:
            load_template = self.generate_file_template_load(self.template_path)
        elif self.template_s3_uri:
            load_template = self.generate_s3_template_loader(self.template_s3_uri)

        ##################
        # Business Logic #
        ##################

        # Perform the request
        response = TemplateRequest(
                filter_dict=self.filter,
                session=credentials.create_session(),
                vpc_ids=self.vpc_ids,
                remove_nones=self.filter_empty
        ).response

        # Fill in the template and out put it.
        raw_template = load_template()
        template = Template(raw_template)
        output = template.render(**response)

        return send_output(output)

    @staticmethod
    def output_stdout(content):
        """
        Send content to stdout. No closure required, so this is not a generator.
        :param str content: string to output
        :return:
        """
        print(content)

    @staticmethod
    def generate_output_file(path):
        """
        Generate a function to send the content to the file specified in 'path'
        :param path:
        :return:
        """

        def write_file(content):
            """
            Function to do write_file operation
            :param content:
            :return:
            """
            with open(path, 'w+') as output:
                output.write(content)

        return write_file

    @staticmethod
    def generate_s3_template_loader(uri):
        """
        Generate a function to load the template from the provided uri.
        :param str uri:
        :return:
        """

        def load_from_s3():
            """
            Function to read template from s3
            :return:
            """
            url_parts = urlparse(uri)

        return load_from_s3

    @staticmethod
    def generate_file_template_load(path):
        """
        Generate calleable to return the content of the template on disk
        :param path:
        :return:
        """
        path = os.path.expanduser(os.path.abspath(
                path
        ))

        def read_file():
            """
            Read file from path and return file contents
            :return:
            """
            with open(path) as template:
                return template.read()

        return read_file

    @staticmethod
    def bad_lambda(*args, **kwargs):
        """
        Callback used in even no lambda is supplied for output
        :param args:
        :param kwargs:
        :return:
        """
        raise RuntimeError(
                "Could not run callback with args='{args}',kwargs='{kwargs}'".format(args=args, kwargs=kwargs))


class TemplateRequest(object):
    """
    Do the request to the AWS api, and return a dict with the IP data.
    """

    def __init__(self, session, filter_dict=None, remove_nones=False, vpc_ids=None):
        """
        :rtype dict
        :param dict filter_dict: Filter for ec2 instances as defined in http://boto3.readthedocs.org/en/latest/reference
            /services/ec2.html#EC2.Client.describe_instances
        :param callable session: If you wish to overload the injection of the boto3 session, otherwise we use a default.
        """
        self.filter = filter_dict
        self.session = session
        self.vpc_ids = vpc_ids
        self.remove_nones = remove_nones

    @property
    def response(self):
        """
        Dictionary of public and private, hostnames and ips.
        :rtype: dict
        """
        describe_request_params = {}
        if self.filter is not None:
            if type(self.filter) is not dict:
                try:
                    filters = json.loads(self.filter)
                except TypeError:
                    filters = self._parse_cli_filters(self.filter)
            else:
                filters = self.filter

            describe_request_params['Filters'] = filters
        if self.vpc_ids is not None:
            if 'Filters' not in describe_request_params:
                describe_request_params['Filters'] = []
            describe_request_params['Filters'].append({
                'Name': 'vpc-id',
                'Values': self.vpc_ids.split(',')
            })
        reservations = self.session().client('ec2').describe_instances(**describe_request_params)

        return self._process_reservations(reservations)

    def _process_reservations(self, reservations):
        """
        Given a dict with the structure of a response from boto3.ec2.describe_instances(...),
        find the public/private ips.
        :param reservations:
        :return:
        """

        reservations = reservations['Reservations']

        private_ip_addresses = []
        private_hostnames = []
        public_ips = []
        public_hostnames = []
        for reservation in reservations:
            for instance in reservation['Instances']:
                private_ip_addresses.append(instance['PrivateIpAddress'])
                private_hostnames.append(instance['PrivateDnsName'])

                if 'PublicIpAddress' in instance:
                    public_ips.append(instance['PublicIpAddress'])
                elif not self.remove_nones:
                    public_ips.append(None)

                if ('PublicDnsName' in instance) & (not self.remove_nones):
                    public_hostnames.append(instance['PublicDnsName'])
                elif not self.remove_nones:
                    public_hostnames.append(None)

        return {
            'private': {
                'ips': private_ip_addresses,
                'hostnames': private_hostnames
            },
            'public': {
                'ips': public_ips,
                'hostnames': public_hostnames
            },
            'reservations': reservations
        }

    @staticmethod
    def _parse_cli_filters(filters):
        """
        Parse the filters from the CLI and turn them into a filter dict for boto.
        :param filters:
        :return:
        """
        parsed_filters = []
        for filter_entry in filters:
            filter_parts = re.match('^Name=(?P<name_value>[^,]+),Values=\[?(?P<key_values>[^\]]+)\]?', filter_entry)
            parsed_filters.append({
                'Name': filter_parts.group('name_value'),
                'Values': filter_parts.group('key_values').split(',')
            })
        return parsed_filters
