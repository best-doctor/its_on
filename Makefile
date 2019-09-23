test:
	PROJECT_ENV=TESTING pytest -q

style:
	flake8 .

typos:
	rozental .

types:
	mypy .

check:
	make -j4 test style types typos
