rst-readme:
	pandoc README.md -f markdown -t rst -s -o README.rst

build:
	python setup.py sdist bdist_wheel

release-test: clean rst-readme build
	twine upload -r pypitest dist/aws-autodiscovery-templater-*

release: clean rst-readme build
	twine upload -r pypi dist/aws-autodiscovery-templater-*

clean:
	rm -rf dist build *.egg-info