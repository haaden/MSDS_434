install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

test:
	python3 -m pytest -vv test_app.py

format:
	black *.py

lint:
	pylint --disable=R,C app.py

all: install lint test