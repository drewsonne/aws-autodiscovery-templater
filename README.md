# aws-autodiscovery-templater

[![Code Issues](https://www.quantifiedcode.com/api/v1/project/7eb81e9532ea405599b212e754ef1ee3/badge.svg)](https://www.quantifiedcode.com/app/project/7eb81e9532ea405599b212e754ef1ee3)

[![PyPI version](https://badge.fury.io/py/aws-auth-helper.svg)](https://badge.fury.io/py/aws-auth-helper)

Auto discovery in AWS can be tricky for legacy applications. Due to time or complexity, it's not always possible to write
auto discovery code to let applications find each other in an elastic/scaling environment. Sometimes, listing the
ips/hosts for hosts in a config file will be enough, and that's what this script does.

# Installation
Installation is simply

    $ pip install aws-autodiscovery-templater

# Usage

## CLI

The easiest way is to use the included cli tool (although there is a small python library which you can use). This project
uses the [jinja2 templating engine](http://jinja.pocoo.org/docs/dev/), so you can find details there about how to write templates.
The following variables are passed to the templating engine:

    {
        "private": {
            "ips": [...],
            "hostnames": [...]
        },
        "public": {
            "ips": [...],
            "hostnames": [...]
        },
        "reservations": {
            ...
        }
    }

The first two entries, contain an array of strings for public and private, ips and hostnames.
The reservations entry contains the raw output from [EC2.Client.describe_instances](boto3.readthedocs.org/en/latest/reference/services/ec2.html#EC2.Client.describe_instances).

From this, we can create a template that looks like this

    # /path/to/config.yaml
    {% if private['ips'] %}
    private_ips:{% for ip in private['ips'] %}
      - {{ ip }}{% endfor %}{% endif %}

We'll be using this template in the following examples.

_Note:_ Before you run any of this, you need to have either your AWS credentials set up in
`~/.aws/{config,credentials}`, or in `AWS_*` environment variables.

### Example run

    $ aws-autodiscovery-templater \
      --template-path /path/to/config.yaml \ # Path to jina2 formatted template
      --profile my-aws-profile \                 # AWS credentials as defined in ~/.aws/credentials
      --stdout \                                 # Print result to stdout
      --filter-empty                             # Don't include null/missing values (eg. not all machines have public IPs

### Filtering instances
More importantly, you can filter instances based on their tags. This filter is a json objectstructured in the same
manner as described in [aws ec2 describe-instances](http://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html),
excluding the root `["Reservations"]` key.

    $ aws-autodiscovery-templater \
      --template-path /path/to/config.yaml \
      --profile my-aws-profile \
      --stdout \
      --filter-empty
      --filter "Name=tag:Application,Values=[mongodb,mongodb-master]"
     private_ips:
       - 10.0.0.20
       - 10.0.0.10
       - 10.0.0.30


## Python

To handle credentials in an encapsulated predictable way, `aws-autodiscovery-templater` takes a function which generates a `boto3.session.Session` object.

### Authentication

To handle credentials, you can either use the built in helper class:

	from awsautodiscoverytemplater import auth
  
 	argparser = AWSArgumentParser(default_role_session_name='aws_templater')
 	credentials_args = vars(argparser.parseargs())
 
 	credentials = auth.Credentials(**credentials_args)
	if credentials.has_role():
		credentials.assume_role()
	session_generator = credentials.create_session()

Or you can use a function/lambda to return a boto3 session object

	session_generator = lambda region=None: boto3.session.Session(region_name=region) 
	
Or even just pass the generic boto3 object in

	session_generator = lambda region=None: boto3

### Requesting
All the templater does is make a request, parse the results into a particular format, and then make those accessible to the Jinja2 Template.

	>>> from awsautodiscoverytemplater.command import TemplateCommand
	
	>>> command = TemplateCommand(
	>>> 	filter=[{
    >>>     	"Name": "tag:Name",
    >>>     	"Values": ["Mongo-Master","Mongo-Slave"]
    >>>     },{
    >>>     	"Name": " aws:cloudformation:stack-name",
    >>>     	"Values": ["Production"]
    >>>     }],
    >>>     # This will return the template after being rendered
    >>>     send_output_handler=lambda template: template,
    >>>     template_path = "/var/lib/myapp/autodiscovery.config.template",
	>>> )
	
	>>> config_txt = command.run()
	[my_config]
	hosts:
		- 10.0.0.0
		- 10.0.0.1
		- 10.0.0.2

# Inline help:

For more details, have a look at the --help option

    $ aws-autodiscovery-templater --help
    usage: aws-autodiscovery-templater [-h]
                                       [--aws-access-key-id AWS_ACCESS_KEY_ID]
                                       [--aws-secret-access-key AWS_SECRET_ACCESS_KEY]
                                       [--aws-session-token AWS_SESSION_TOKEN]
                                       [--region REGION] [--profile PROFILE]
                                       [--role ROLE] [--auth-debug]
                                       [--role-session-name ROLE_SESSION_NAME]
                                       --template-path TEMPLATE_PATH --stdout
                                       [--vpc-ids] [--filter FILTER]
                                       [--filter-empty]

    optional arguments:
      -h, --help            show this help message and exit

    AWS credentials:
      --aws-access-key-id AWS_ACCESS_KEY_ID
                            AWS access key
      --aws-secret-access-key AWS_SECRET_ACCESS_KEY
                            Access and secret key variables override credentials
                            stored in credential and config files
      --aws-session-token AWS_SESSION_TOKEN
                            A session token is only required if you are using
                            temporary security credentials.
      --region REGION       This variable overrides the default region of the in-
                            use profile, if set.
      --profile PROFILE     This can be the name of a profile stored in a
                            credential or config file, or default to use the
                            default profile.
      --role ROLE           Fully qualified role arn to assume
      --auth-debug          Enter debug mode, which will print credentials and
                            then exist at `create_session`.
      --role-session-name ROLE_SESSION_NAME
                            If you have assigned a role, set a --role-session-name

    AWS Autodiscovery Templater:
      --template-path TEMPLATE_PATH
                            Path to the template to fill variables into.
      --stdout              Prints a json object containing the retrieves
                            resources
      --vpc-ids             Optionally restrict the filtering to a particular list
                            of IPs. Comma seperated list of vpc-ids.
      --filter FILTER       Filter for ec2 instances as defined in http://boto3.re
                            adthedocs.org/en/latest/reference/services/ec2.html#EC
                            2.Client.describe_instances
      --filter-empty        By default, missing values are returned as null to
                            keep private/public ip/hostname sets of equal length.
                            This removes null values from the filter
