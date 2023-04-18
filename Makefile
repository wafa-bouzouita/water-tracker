PYTHON = $(shell command -v python 2> /dev/null)
VIRTUAL_ENV = .venv
STREAMLIT_MAIN_SCRIPT = app/main.py

clean:
	rm -rf ${VIRTUAL_ENV}

${VIRTUAL_ENV}:
	${PYTHON} -m venv ${VIRTUAL_ENV}
	. .venv/Scripts/activate
	pip install poetry

.PHONY: poetry-install
poetry-install: pyproject.toml poetry.lock
	. .venv/Scripts/activate
	poetry install


.PHONY: install
install:
	@${MAKE} -s ${VIRTUAL_ENV}
	@${MAKE} -s poetry-install

.PHONY: streamlit-run
streamlit-run:
	. .venv/Scripts/activate
	streamlit run ${STREAMLIT_MAIN_SCRIPT}
