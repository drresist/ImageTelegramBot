###############################################
# Base Image
###############################################
FROM python:3.9-slim as python-base

WORKDIR app/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
