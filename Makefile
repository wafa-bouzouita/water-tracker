GLOBAL_PYTHON := $(shell command -v python 2> /dev/null)
GLOBAL_POETRY := $(shell command -v poetry 2> /dev/null)
VIRTUAL_ENV := .venv
HOOKS := .git/hooks
DOTENV := .env
ifeq ($(OS), Windows_NT)
	BIN = ${VIRTUAL_ENV}/Scripts/
else
	BIN = ${VIRTUAL_ENV}/bin/
endif
STREAMLIT_MAIN_SCRIPT = app/main.py

# Main Targets

clean:
	rm -rf ${VIRTUAL_ENV}
	rm -rf ${HOOKS}

${DOTENV}:
	cp ${DOTENV}.template ${DOTENV}

# Poetry targets

check-poetry:
	@if [ -z $(GLOBAL_POETRY) ]; then echo "Poetry is not installed on your global python. Use 'make install-poetry' to install Poetry on your global python."; exit 2 ;fi

install-poetry:
	curl -sSL https://install.python-poetry.org | ${GLOBAL_PYTHON} -

${VIRTUAL_ENV}:
	${GLOBAL_PYTHON} -m venv ${VIRTUAL_ENV}

.PHONY: poetry-install
poetry-install: pyproject.toml poetry.lock
	${MAKE} -s check-poetry
	${GLOBAL_POETRY} install --only main --ansi

.PHONY: install
install:
	${MAKE} -s ${DOTENV}
	${MAKE} -s ${VIRTUAL_ENV}
	${MAKE} -s poetry-install

.PHONY: streamlit-run
streamlit-run:
	${MAKE} -s install
	${BIN}streamlit run ${STREAMLIT_MAIN_SCRIPT}

# Development Targets

.PHONY: poetry-install-dev
poetry-install-dev: pyproject.toml poetry.lock
	${MAKE} -s check-poetry
	${GLOBAL_POETRY} install --ansi

.PHONY: hooks_install
hooks-install: .pre-commit-config.yaml
	${BIN}pre-commit install

.PHONY: install
install-dev:
	${MAKE} -s ${DOTENV}
	${MAKE} -s ${VIRTUAL_ENV}
	${MAKE} -s poetry-install-dev
	${MAKE} -s hooks-install

.PHONY: test
test:
	${MAKE} -s install-dev
	${BIN}pytest
