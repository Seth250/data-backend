cp .env.example .env

cp docker-compose.override.yaml.example docker-compose.override.yaml

docker compose up --build
