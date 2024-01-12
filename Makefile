build:
	docker compose build
up-build:
	docker-compose up -d --build
up:
	docker-compose up -d
down:
	docker-compose down
restart:
	make down
	make up
build-prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml build
up-prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
restart-prod:
	make down
	make up-prod
migrations:
	docker exec -it tron_parser_faucet-python_1 python manage.py makemigrations
migrate:
	docker exec -it tron_parser_faucet-python_1 python manage.py migrate
shell:
	docker exec -it tron_parser_faucet-python_1 python manage.py shell
initialize-database-testnet:
	docker exec -it tron_parser_faucet-python_1 python manage.py initialize_database --network testnet
initialize-database-mainnet:
	docker exec -it tron_parser_faucet-python_1 python manage.py initialize_database --network mainnet