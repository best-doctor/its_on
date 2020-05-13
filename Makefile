test:
	ENV_FOR_DYNACONF=TESTING pytest -q

style:
	flake8 .

typos:
	rozental .

types:
	mypy .

check:
	make -j4 test style types
