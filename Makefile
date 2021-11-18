python-package:
	python3 -m build

# With additional README (ugly hack; better solutions out there?)
distribution-package:	python-package
	${RM} -rf dist/* build/*
	mkdir -p build/lib/dnstemple
	cp README.md build/lib/dnstemple/
	python3 -m build

pypi:	distribution-package test
	twine upload dist/*

test:	tests
tests:
	flake8
	tox
	${MAKE} -C sample test

.PHONY: python-package distribution-package pypi tests test
