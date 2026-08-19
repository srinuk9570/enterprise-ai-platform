# Requirements management Makefile

.PHONY: install install-dev install-prod install-test freeze clean

install:
	pip install -r requirements/base.txt

install-dev:
	pip install -r requirements/dev.txt

install-prod:
	pip install -r requirements/prod.txt

install-test:
	pip install -r requirements/test.txt

install-all:
	pip install -r requirements/dev.txt
	pip install -r requirements/test.txt

freeze:
	bash requirements/freeze.sh

outdated:
	pip list --outdated

upgrade:
	pip install --upgrade -r requirements/base.txt

upgrade-all:
	pip install --upgrade -r requirements/dev.txt

clean:
	pip uninstall -y -r requirements/dev.txt || true
	pip uninstall -y -r requirements/test.txt || true

check:
	pip check

tree:
	pipdeptree

security:
	safety check -r requirements/base.txt
	safety check -r requirements/prod.txt