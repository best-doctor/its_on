test:
	ENV_FOR_DYNACONF=TESTING pytest -q --cov=its_on --cov-report=xml

style:
	flake8 .
	mdl README.md

typos:
	rozental .

types:
	mypy .

check:
	make -j4 test style types
