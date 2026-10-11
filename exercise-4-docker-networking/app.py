from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/about", methods=["GET"])
def about():
    return jsonify({
        "name": "Simple REST API",
        "version": "1.0",
        "description": "This is a simple REST API built with Flask."
    })

if __name__ == "__main__":
    # 0.0.0.0 = listen on all interfaces, so Docker's port forward can reach us
    app.run(host="0.0.0.0", port=5001, debug=True)
