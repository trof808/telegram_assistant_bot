.PHONY: build run dev stop logs clean

# Сборка образа
build:
	docker-compose build

# Запуск в продакшн режиме
run:
	docker-compose up -d

# Запуск в режиме разработки (с volumes)
dev:
	docker-compose up --build

# Запуск локально с автоперезагрузкой
dev-local:
	python dev.py

# Остановка контейнеров
stop:
	docker-compose down

# Просмотр логов
logs:
	docker-compose logs -f bot

# Пересборка с нуля
rebuild:
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d

# Очистка
clean:
	docker-compose down -v
	docker system prune -f