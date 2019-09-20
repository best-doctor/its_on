test:
	TESTING=True pytest -q

style:
	flake8 .

typos:
	rozental .

types:
	python scripts/run_mypy.py

check:
	make -j4 test style types typos
