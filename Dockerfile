FROM python:3.6.5
ENV PYTHONUNBUFFERED 1
RUN mkdir /app/
COPY requirements.txt /app/
WORKDIR /app
RUN pip install -r requirements.txt
