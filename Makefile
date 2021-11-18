python-package:
	python3 -m build

distribution-package:
	${RM} -rf dist/* build/*
	python3 -m build

pypi:	distribution-package test
	twine upload dist/*

test:	tests
tests:
	flake8
	tox
	${MAKE} -C sample test

.PHONY: python-package distribution-package pypi tests test
