.PHONY: build build_cython install build_dist test clean

MODULE := kola
PIP_MODULE := KoiLang

all: clean build lint build_dist
refresh: clean develop test lint

build_lexer: kola/lex.yy.c build

kola/lex.yy.c: kola/kolalexer.l
	flex kola/kolalexer.l
	mv lex.yy.c kola/lex.yy.c -f -u

build_cython:
	USE_CYTHON=true python setup.py build_ext --inplace

build:
	python setup.py build_ext --inplace

install: build
	python setup.py install

develop: build
	python setup.py develop

build_dist: test
	python setup.py sdist bdist_wheel

lint:
	flake8 ${MODULE}/ tests/ --count --max-line-length=127 --extend-ignore=W293,E402

test:
	python -m unittest

clean:
	rm -rf build
	rm -rf dist
	rm -rf ${PIP_MODULE}.egg-info

uninstall:
	pip uninstall ${PIP_MODULE} -y || true
