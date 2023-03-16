import json
import os
import traceback
import datetime

import dotenv
import requests
from flask import Flask, request, render_template, redirect, send_from_directory, jsonify, make_response
from langchain import FAISS
from langchain import VectorDBQA, HuggingFaceHub, Cohere, OpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings, HuggingFaceHubEmbeddings, CohereEmbeddings, \
	HuggingFaceInstructEmbeddings
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import (
	ChatPromptTemplate,
	SystemMessagePromptTemplate,
	HumanMessagePromptTemplate,
)

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


# handling CORS
@app.after_request
def after_request(response):
	response.headers.add('Access-Control-Allow-Origin', '*')
	response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
	response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
	response.headers.add('Access-Control-Allow-Credentials', 'true')
	return response


if __name__ == "__main__":
	app.run(debug=True, port=5001)
