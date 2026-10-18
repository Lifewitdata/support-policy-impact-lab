.PHONY: setup run test app notebooks
setup:
	python -m pip install -r requirements.txt
	python -m pip install -e . --no-deps
run:
	python -m support_policy.pipeline
test:
	python -m pytest -q
app:
	python -m streamlit run app/app.py
notebooks:
	python scripts/execute_notebooks.py
