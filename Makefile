python-package:
	python3 -m build

# With additional README (ugly hack; better solutions out there?)
distribution-package:	python-package
	${RM} -rf dist/* build/*
	mkdir -p build/lib/fake_super
	cp README.md build/lib/fake_super/
	python3 -m build

pypi:	distribution-package test
	twine upload dist/*

test:	tests
tests:
	${MAKE} -c sample test

.PHONY: python-package distribution-package pypi tests test
