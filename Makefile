PYTHON = $(shell command -v python 2> /dev/null)
VIRTUAL_ENV = .venv
HOOKS = .git/hooks
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

${VIRTUAL_ENV}:
	${PYTHON} -m venv ${VIRTUAL_ENV}
	${BIN}python -m pip install poetry

.PHONY: poetry-install
poetry-install: pyproject.toml poetry.lock
	${BIN}poetry install --only main --ansi

.PHONY: install
install:
	${MAKE} -s ${VIRTUAL_ENV}
	${MAKE} -s poetry-install

.PHONY: streamlit-run
streamlit-run:
	${MAKE} -s install
	${BIN}streamlit run ${STREAMLIT_MAIN_SCRIPT}

# Development Targets

.PHONY: poetry-install-dev
poetry-install-dev: pyproject.toml poetry.lock
	${BIN}poetry install --ansi

.PHONY: hooks_install
hooks-install: .pre-commit-config.yaml
	${BIN}pre-commit install

.PHONY: install
install-dev:
	${MAKE} -s ${VIRTUAL_ENV}
	${MAKE} -s poetry-install-dev
	${MAKE} -s hooks-install
