.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

try:
	from urllib import pathname2url
except:
	from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

.PHONY: help
help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

.PHONY: clean
clean: clean-build clean-pyc clean-js ## remove build, Python, and js artifacts

.PHONY: clean-build
clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

.PHONY: clean-pyc
clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.PHONY: clean-js
clean-js: ## remove js file artifacts
	jlpm run clean:all

.PHONY: test
test: test-install test-python-lib test-js-lib ## test

.PHONY: test-install
test-install:
	pip install .
	jupyter lab build
	jupyter serverextension list
	jupyter labextension list
	python -m jupyterlab.browser_check

.PHONY: test-python-lib
test-python-lib: ## run python tests
	python -m pytest --basetemp=${ENVTMP} --cov=ballet

.PHONY: test-js-lib
test-js-lib: ## run js tests
	true  # TODO

.PHONY: lint
lint: ## check style with flake8 and isort
	flake8 server/ballet_submit_labextension
	isort -c --recursive server/ballet_submit_labextension

.PHONY: release
release: dist ## package and upload a release
	twine upload dist/*
	jlpm publish

.PHONY: test-release
test-release: dist ## package and upload a release on TestPyPI
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: dist
dist: clean ## builds source and wheel package
	python setup.py sdist
	python setup.py bdist_wheel
	ls -l dist

.PHONY: install
install: clean-build clean-pyc ## install the package to the active Python's site-packages
	pip install .
	jupyter lab build

.PHONY: install-test
install-test: clean-build clean-pyc ## install the package and test dependencies
	pip  install .[test]
	jupyter lab build

.PHONY: install-develop
install-develop: clean-build clean-pyc ## install the package in editable mode and dependencies for development
	pip install -e .[dev]
	jupyter serverextension enable --py ballet_submit_labextension
	jlpm
	jlpm build
	jupyter labextension link
	jlpm build
	jupyter lab build
