MAKEFLAGS += --always-make

VERSION := $(shell python3 -c "from xkits_file.attribute import __package_vers__; print(__package_vers__)")

all: build test


release: all
	if [ -n "${VERSION}" ]; then \
		git tag -a v${VERSION} -m "release v${VERSION}"; \
		git push origin --tags; \
	fi

version:
	@echo ${VERSION}


clean-cover:
	rm -rf cover .coverage coverage.xml htmlcov
clean-tox:
	rm -rf .stestr .tox
clean: build-clean test-clean clean-cover clean-tox


upload:
	python3 -m pip install --upgrade xpip-upload
	xpip-upload --config-file .pypirc dist/*


build-prepare:
	python3 -m pip install --upgrade -r requirements.txt
build-clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf build dist *.egg-info
build: build-prepare build-clean
	python3 -m build --sdist --wheel


install:
	python3 -m pip install --force-reinstall --no-deps dist/*.whl
uninstall:
	python3 -m pip uninstall -y xkits-file
reinstall: uninstall install


test-prepare:
	python3 -m pip install --upgrade mock pylint flake8 pytest pytest-cov
pylint:
	pylint $(shell git ls-files xkits_file/*.py xkits_fileviewer/*.py)
flake8:
	flake8 xkits_file xkits_fileviewer --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 xkits_file xkits_fileviewer --count --exit-zero --max-complexity=25 --max-line-length=127 --statistics
pytest:
	pytest --cov=xkits_file --cov=xkits_fileviewer --cov-report=term-missing --cov-report=xml --cov-report=html --cov-config=.coveragerc --cov-fail-under=100
pytest-clean:
	rm -rf .pytest_cache
test: test-prepare pylint flake8 pytest
test-clean: pytest-clean
