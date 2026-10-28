import os

from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/api/health")
def health():
    return jsonify(
        status="healthy",
        regno=os.environ.get("REGNO", "not-set"),
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
