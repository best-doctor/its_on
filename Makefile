style:
	flake8 .

typos:
	rozental .

types:
	mypy .

check:
	make -j4 style types typos
