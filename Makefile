.PHONY: up down migrate makemigrations shell test celery

up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose exec backend python manage.py migrate

makemigrations:
	docker compose exec backend python manage.py makemigrations

shell:
	docker compose exec backend python manage.py shell

superuser:
	docker compose exec backend python manage.py createsuperuser

test:
	docker compose exec backend python manage.py test

celery:
	docker compose exec celery-worker celery -A config inspect active

logs:
	docker compose logs -f backend celery-worker
