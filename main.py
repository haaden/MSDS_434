import os

from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route('/')
def hello_world():
    name = request.args.get('name', 'World')
    return jsonify({'message': 'Hello {name}!'})


if __name__ == "__main__":
    app.run(port=8080, host='0.0.0.0')