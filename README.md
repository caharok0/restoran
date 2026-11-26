# Ресторан

Невеликий сайт ресторану на Django: меню, відгуки, кошик, оформлення замовлень і керування меню для персоналу.

## Запуск

Встановіть пакети та підготуйте базу даних:

	python -m pip install -r requirements.txt
	python manage.py migrate

Запустіть сервер:

	python manage.py runserver

Відкрийте http://127.0.0.1:8000/.

## Перевірка

	python manage.py check
	python manage.py test