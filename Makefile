test:
	ENV_FOR_DYNACONF=TESTING python -m pytest

coverage:
	ENV_FOR_DYNACONF=TESTING python -m pytest --cov=its_on --cov-report=xml

style:
	flake8 .

readme:
	mdl README.md

typos:
	rozental .

types:
	mypy .

check:
	make -j4 test style types
