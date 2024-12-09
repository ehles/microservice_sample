import argparse
import random
import time
from flask import Flask, request, jsonify
import requests
from threading import Thread

app = Flask(__name__)

# Глобальные переменные для параметров
NODE_NAME = None
TIMEOUT = None
SERVICES = []


@app.route("/activate", methods=["POST"])
def activate():
    """Основной обработчик запросов."""
    data = request.json
    color = data.get("color", "white")
    if not color:
        return jsonify({"error": "Color not provided"}), 400

    # Отправляем запрос в web приложение
    web_response = send_to_web(color)
    if web_response.status_code != 200:
        return jsonify({"error": "Failed to send to web"}), 500

    # Пересылаем запрос на другие сервисы и обрабатываем их ответы
    errors = []
    threads = []
    responses = {}

    def query_service(service):
        try:
            response = requests.post(
                f"http://{service}/activate", json=data, timeout=TIMEOUT / 1000
            )
            responses[service] = response.status_code
        except requests.exceptions.Timeout:
            responses[service] = 502
        except requests.exceptions.RequestException as e:
            responses[service] = 500

    for service in SERVICES:
        thread = Thread(target=query_service, args=(service,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join(timeout=TIMEOUT / 1000)

    # Проверяем результаты
    if all(status == 200 for status in responses.values()):
        # Все сервисы ответили успешно
        send_to_web("green")
        time.sleep(0.1)
        send_to_web("white")
        return jsonify({"message": "All services responded successfully"}), 200
    else:
        # Ошибка от одного из сервисов или таймаут
        send_to_web("red")
        time.sleep(0.1)
        send_to_web("white")
        return jsonify(
            {"error": "One or more services failed", "responses": responses}
        ), 500


def send_to_web(color):
    """Отправляет запрос в web приложение для изменения цвета."""
    web_url = "http://127.0.0.1:5000/activate"  # Предполагаем, что web работает на localhost:5000
    payload = {"item": NODE_NAME, "color": color}
    try:
        return requests.post(web_url, json=payload)
    except requests.exceptions.RequestException as e:
        print(f"Failed to send to web: {e}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Microservice")
    parser.add_argument("-l", "--listen", required=True, help="listen address")
    parser.add_argument("-n", "--node", required=True, help="Node name")
    parser.add_argument("-t", "--timeout", type=int, default=200, help="Timeout (ms)")
    parser.add_argument(
        "-s", "--services", action="append", help="Addresses of X services", default=[]
    )

    args = parser.parse_args()

    NODE_NAME = args.node
    LISTEN = args.listen
    TIMEOUT = args.timeout
    SERVICES = args.services

    # Если сервисы X не заданы, отвечаем случайным результатом
    if not SERVICES:

        @app.route("/activate", methods=["POST"])
        def random_response():
            status = random.choice([200, 500, 502])
            if status == 200:
                send_to_web("green")
            else:
                send_to_web("red")
            time.sleep(0.1)
            send_to_web("white")
            return jsonify({"status": status}), status

    app.run(port=LISTEN)  # Запускаем сервер на порту 5001
