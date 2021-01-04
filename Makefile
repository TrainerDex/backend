PYTHON ?= python3.8

ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

# Python Code Style
reformat:
	$(PYTHON) -m black $(ROOT_DIR)
stylecheck:
	$(PYTHON) -m black --check $(ROOT_DIR)
stylediff:
	$(PYTHON) -m black --check --diff $(ROOT_DIR)

# Migrations
makemigrations:
	$(PYTHON) manage.py makemigrations --noinput community trainerdex

# Tranlations
makemessages:
	$(PYTHON) manage.py makemessages --all --ignore=env/* --noinput

# Development environment
newenv:
	virtualenv --python=`which $(PYTHON)` env
	$(MAKE) syncenv
syncenv:
	env/bin/pip install -U pip
	env/bin/pip install -Ur ./requirements-dev.txt
