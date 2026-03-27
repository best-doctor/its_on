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

lock-export:
	pdm export --without dev --without darwin -o requirements.txt
	pdm export --without default --without darwin -o requirements_dev.txt
	pdm export --without default --without dev -o requirements_darwin.txt

lock:
	pdm lock --update-reuse
	make lock-export

install-dev:
ifeq ($(UNAME),Darwin)
	pip install --no-deps -r requirements.txt -r requirements_dev.txt -r requirements_darwin.txt
else
	pip install --no-deps -r requirements.txt -r requirements_dev.txt
endif
