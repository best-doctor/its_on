test:
	TESTING=True pytest -q

style:
	flake8 .

typos:
	rozental .

types:
	mypy .

check:
	make -j4 test style types typos
