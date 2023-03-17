import os
import dotenv
from flask import Flask, request, jsonify, make_response
from application.chatgpt.constants import model_config

# loading the .env file
dotenv.load_dotenv()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER = "inputs"
app.config['CELERY_BROKER_URL'] = os.getenv("CELERY_BROKER_URL")
app.config['CELERY_RESULT_BACKEND'] = os.getenv("CELERY_RESULT_BACKEND")
app.config['MONGO_URI'] = os.getenv("MONGO_URI")


@app.route('/api/whoami/<name>', methods=['GET', 'POST'])
def whoami(name):
	data = {
		"code": 200,
		"result": name,
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
		data = {"status": 'Fail', "data": None, "message": e.args}
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
		data = {"status": 'Success', "data": None, "message": "Verify successfully"}
	except Exception as e:
		data = {"status": 'Fail', "data": None, "message": e.args}
	return make_response(jsonify(data), 200)


@app.route('/api/config', methods=['POST'])
def config():
	try:
		data = model_config()
		res = {"status": 'Success', "data": data, "message": "Verify successfully"}
	except Exception as e:
		res = {"status": 'Fail', "data": None, "message": e.args}
	return make_response(jsonify(res), 200)


@app.route('/api/chat-process', methods=['POST'])
def chat_process():
	parameters = request.get_json()
	token = parameters.get("prompt", "")
	options = parameters.get("options", {})
	first_chunk = True
	message = """In this example, we define a Flask route that returns a streaming response. We create a Python generator function called generate() that yields the HTML content in chunks using the yield keyword. The generator function is passed as the response body to the Response constructor, which creates a streaming response with the content_type set to "text/html" and the status set to 200."""

	res = make_response(jsonify({}), 200)
	res.headers['Content-type'] = 'application/octet-stream'
	return res


# handling CORS
@app.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,AUTH_SECRET_KEY')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
	response.headers.add('Access-Control-Allow-Credentials', 'true')
	return response


if __name__ == "__main__":
	app.run(debug=True, port=5001)
