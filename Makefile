package:
	${RM} -f dist/*
	./setup.py sdist bdist_wheel

pypi:	package
	twine upload dist/*
