from flask import Flask, render_template, request, jsonify, Response
import time
import threading

app = Flask(__name__)

# Состояние диаграммы
diagram_state = {
    "UI": {"color": "black"},
    "D": {"color": "black"},
    "P": {"color": "black"},
    "V": {"color": "black"},
    "T": {"color": "black"},
    "TM": {"color": "black"},
    "DS": {"color": "black"},
}

# Поток сообщений для клиентов
clients = []


def event_stream():
    """Генерация событий для клиентов."""
    while True:
        time.sleep(1)
        yield "data: ping\n\n"  # Отправляем "пустое" событие, чтобы клиент оставался подключен


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/diagram")
def get_diagram():
    diagram = "flowchart LR\n"
    diagram += "    UI --> D\n"
    diagram += "    D --> P\n"
    diagram += "    P --> V\n"
    diagram += "    V --> T\n"
    diagram += "    V --> DS\n"
    diagram += "    V --> TM\n"

    for node, props in diagram_state.items():
        diagram += f'    {node}["{node}"]:::custom_{node}\n'

    styles = "\n".join(
        [
            f'classDef custom_{node} fill:{props["color"]},stroke:#333,stroke-width:2;'
            for node, props in diagram_state.items()
        ]
    )
    diagram += styles
    return jsonify({"diagram": diagram})


@app.route("/events")
def sse():
    """Устанавливаем соединение для SSE."""

    def stream():
        q = []
        clients.append(q)  # Добавляем клиента в общий список
        try:
            while True:
                if q:
                    yield q.pop(0)  # Отправляем клиенту новое сообщение
                time.sleep(0.1)  # Периодическая проверка
        finally:
            clients.remove(q)  # Удаляем клиента при завершении соединения

    return Response(stream(), content_type="text/event-stream")


@app.route("/activate", methods=["POST"])
def activate():
    """Обрабатываем запрос на изменение элемента."""
    data = request.json
    item = data.get("item")
    color = data.get("color", "black")

    if item in diagram_state:
        diagram_state[item]["color"] = color

        # Уведомляем клиентов об изменении состояния
        for client in clients:
            client.append("data: update\n\n")
        return jsonify({"message": f"{item} updated to {color}"}), 200
    else:
        return jsonify({"error": "Invalid item"}), 400


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
