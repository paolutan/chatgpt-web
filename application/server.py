import os
from flask import Flask, request, jsonify, make_response, Response
from application.chatgpt.chat_utils import model_config, chat_with_openai
from application import auth

app = Flask(__name__)


@app.route('/api/whoami/<name>', methods=['POST'])
@auth.need_authorization
def whoami(name):
    data = {
        "status": "Success",
        "data": name,
        "message": ""
    }
    return make_response(jsonify(data), 200)


@app.route('/api/session', methods=['POST'])
def session():
    try:
        auth_secret_key = os.getenv("AUTH_SECRET_KEY", None)
        has_auth = (auth_secret_key is not None) and (len(auth_secret_key) > 0)
        data = {"status": 'Success', "data": {'auth': has_auth}, "message": ""}
    except Exception as e:
        data = {"status": "Fail", "data": None, "message": e.args}
    return make_response(jsonify(data), 200)


@app.route('/api/verify', methods=['POST'])
def verify():
    try:
        parameters = request.get_json()
        token = parameters.get("token", "")
        auth_secret_key = os.getenv("AUTH_SECRET_KEY", None)
        if auth_secret_key and (not token):
            raise KeyError("Secret key is empty")
        if auth_secret_key != token:
            raise KeyError("'密钥无效 | Secret key is invalid'")
        data = {"status": "Success", "data": None, "message": "Verify successfully"}
    except Exception as e:
        data = {"status": 'Fail', "data": None, "message": e.args}
    return make_response(jsonify(data), 200)


@app.route('/api/config', methods=['POST'])
@auth.need_authorization
def config():
    try:
        data = model_config()
        res = {"status": "Success", "data": data, "message": "Verify successfully"}
    except Exception as e:
        res = {"status": "Fail", "data": None, "message": e.args}
    return make_response(jsonify(res), 200)


@app.route('/api/chat-process', methods=['POST'])
@auth.need_authorization
def chat_process():
    try:
        parameters = request.get_json()
        print(parameters)
        prompt = parameters.get("prompt", "")
        if not prompt:
            raise ValueError("Message can not be empty.")
        options = parameters.get("options", {})
        parent_message_id = options.get("parentMessageId", "")
        stream_response = chat_with_openai(prompt, parent_message_id=parent_message_id, need_save_db=True, stream=True)
        return Response(stream_response, content_type="application/octet-stream")
    except Exception as e:
        res = {"status": "Fail", "data": None, "message": e.args}
        return make_response(jsonify(res), 200)


# handling CORS
@app.after_request
def after_request(response):
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,AUTH_SECRET_KEY")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    response.headers.add("Access-Control-Allow-Credentials", "true")
    return response


if __name__ == "__main__":
    app.run(debug=True, port=5001, host="0.0.0.0")
