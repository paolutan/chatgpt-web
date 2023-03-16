FROM python:3.10
# Copy pre-built packages from builder stage

WORKDIR /app

COPY . /app
ENV PYTHONPATH "${PYTHONPATH}:/app"

RUN pip install -r requirements.txt

ENV FLASK_APP=server.py
ENV FLASK_DEBUG=true

EXPOSE 5001

CMD ["gunicorn", "-w", "2", "--timeout", "120", "--bind", "0.0.0.0:5001", "wsgi:app"]
