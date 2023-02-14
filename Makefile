PORT ?= 8000
start:
	poetry run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app --preload
dev:
	poetry run flask --app page_analyzer:app run
debug:
	poetry run flask --app page_analyzer:app --debug run
lint:
	poetry run flake8
install:
	poetry install	