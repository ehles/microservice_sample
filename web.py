import time

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from flask import Response

app = Flask(__name__)

# Состояние диаграммы
diagram_state = {
    "UI": {"color": "white"},
    "D": {"color": "white"},
    "P": {"color": "white"},
    "H": {"color": "white"},
    "V": {"color": "white"},
    "T": {"color": "white"},
    "TM": {"color": "white"},
    "DS": {"color": "white"},
}

# Messsage flow for clients
clients = []


def event_stream():
    """Generate events for clients."""
    while True:
        time.sleep(1)
        # Send empty message to keep connection alive
        yield "data: ping\n\n"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/diagram")
def get_diagram():
    diagram = "flowchart LR\n"
    diagram += "    UI --> D\n"
    diagram += "    D --> P\n"
    diagram += "    P --> V\n"
    diagram += "    P --> H\n"
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
    """Create SSE connection."""

    def stream():
        q = []
        clients.append(q)
        try:
            while True:
                if q:
                    yield q.pop(0)  # Send message from queue
                time.sleep(0.1)  # Wait for new message
        finally:
            clients.remove(q)

    return Response(stream(), content_type="text/event-stream")


@app.route("/activate", methods=["POST"])
def activate():
    """Process request to change element state."""
    data = request.json
    item = data.get("item")
    color = data.get("color", "black")

    if item in diagram_state:
        diagram_state[item]["color"] = color

        # Notify clients about state change
        for client in clients:
            client.append("data: update\n\n")
        return jsonify({"message": f"{item} updated to {color}"}), 200
    else:
        return jsonify({"error": "Invalid item"}), 400


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
