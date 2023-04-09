.PHONY: build build_cython install build_dist test docs clean

MODULE := kola
PIP_MODULE := KoiLang

all: clean build lint build_dist
refresh: clean develop test lint

build_lexer: kola/lex.yy.c build

kola/lex.yy.c: kola/kolalexer.l
	flex kola/kolalexer.l

build_cython:
	USE_CYTHON=true python setup.py build_ext --inplace

build:
	python setup.py build_ext --inplace

install:
	python setup.py install

run:
	python -m kola

develop:
	python setup.py develop

build_dist:
	python setup.py sdist bdist_wheel

lint:
	flake8 ${MODULE}/ tests/ --exclude __init__.py --count --max-line-length=127 --extend-ignore=W293,E402

test:
	python -m unittest

uninstall:
	pip uninstall ${PIP_MODULE} -y || true

docs:
	cd docs/api && make html

clean:
	rm -rf build
	rm -rf dist
	rm -rf ${PIP_MODULE}.egg-info
