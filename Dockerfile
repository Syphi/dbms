FROM python:3.13.5-slim
WORKDIR /app/src
COPY requirements.txt ..
RUN pip install -r ../requirements.txt
COPY src/ .
ENV PYTHONPATH=/app
CMD ["python", "main.py"]
