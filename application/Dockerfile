FROM python:3.10
# Copy pre-built packages from builder stage

WORKDIR /chatgpt-web

COPY ./application /chatgpt-web/application
ENV PYTHONPATH "${PYTHONPATH}:/chatgpt-web"

WORKDIR /chatgpt-web/application
RUN pip install -r requirements.txt

ENV TZ=Asia/Shanghai

ENV FLASK_APP=server.py
ENV FLASK_DEBUG=true

EXPOSE 5001

CMD [ "gunicorn", "-c", "gunicorn_conf.py", "server:app" ]
