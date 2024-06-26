.PHONY: help clean clean-build clean-pyc dist install develop

PYTHON?=python3
PIP?=pip3
FIND?=find

help:
	@echo "certbot-dns-sweb"
	@echo
	@echo "clean - remove all build and Python artifacts"
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "dist - package"
	@echo "install - install the package to the active Python's site-packages"
	@echo "develop - install the package for development as editable"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	rm -fr .tox/
	rm -fr *.egg-info
	rm -fr *.egg

clean-pyc:
	$(FIND) . -name '*.pyc' -exec rm -f {} +
	$(FIND) . -name '*.pyo' -exec rm -f {} +
	$(FIND) . -name '*~' -exec rm -f {} +
	$(FIND) . -name '__pycache__' -exec rm -fr {} +

dist: clean
	$(PYTHON) -m build --no-isolation
	ls -lh dist

install: clean
	$(PIP) install .

develop:
	$(PIP) install --upgrade --upgrade-strategy eager -e ".[dev]"
