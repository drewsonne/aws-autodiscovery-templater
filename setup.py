from setuptools import setup, find_packages

setup(
    name='aws-autodiscovery-templater',
    version='1.0.0',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=['boto3','jinja2'],
    entry_points='''
[console_scripts]
aws-autodiscovery-templater=awsautodiscoverytemplater.cli_wrapper:run
    ''',
    author_email='drew.sonne@gmail.com',
    author='Drew J. Sonne',
    url='https://github.com/drewsonne/aws-autodiscovery-templater',
    download_url = 'https://github.com/drewsonne/aws-autodiscovery-templater/tarball/1.0.0', # I'll explain this in a second
)
