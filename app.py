import argparse
import random
import time

from flask_cors import CORS
from flask import Flask
from flask import request
from flask import jsonify
import requests
from threading import Thread

app = Flask(__name__)
CORS(app)

NODE_NAME = None
TIMEOUT = None
SERVICES = []

COLOR_OK="#00ffcc"
COLOR_ERROR="#ff0066"
COLOR_DEFAULT="#003333"
COLOR_DISABLED="#1a1a1a"
COLOR_ACTIVE="#00ffcc"

@app.route("/activate", methods=["POST"])
def activate():
    """Основной обработчик запросов."""
    if not SERVICES:
        print("Responding randomly")
        status = random.choice([200,200,200,200,200,200, 500, 502])
        if status == 200:
            send_to_web("green")
        else:
            send_to_web("red")
        time.sleep(TIMEOUT/1000)
        send_to_web("white")
        return jsonify({"status": status}), status

    data = request.json
    color = data.get("color", "white")
    if not color:
        return jsonify({"error": "Color not provided"}), 400

    # Send request to web application (SSE for mermaid)
    web_response = send_to_web(color)
    if web_response.status_code != 200:
        return jsonify({"error": "Failed to send to web"}), 500

    # Send request to other services and process their responses
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

    # time.sleep(TIMEOUT/1000)

    # Check results
    if all(status == 200 for status in responses.values()):
        # All services responded successfully
        send_to_web("#00ffcc")
        time.sleep(0.2)
        send_to_web("white")
        return jsonify({"message": "All services responded successfully"}), 200
    else:
        # Error in one of the services
        send_to_web("red")
        time.sleep(0.2)
        send_to_web("white")
        return jsonify(
            {"error": "One or more services failed", "responses": responses}
        ), 500


def send_to_web(color):
    """Send request to the web application for changing the color."""

    # web listening on localhost:5000
    web_url = "http://127.0.0.1:5000/activate"
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
    app.run(port=LISTEN)  # Server listening
