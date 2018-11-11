FROM python:3.6.5
ENV PYTHONUNBUFFERED 1
RUN mkdir /app/
COPY requirements.txt /app/
WORKDIR /
RUN pip install -r /app/requirements.txt
