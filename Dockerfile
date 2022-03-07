FROM python:3.8-alpine
MAINTAINER Begmuhammadov Bahromjon
RUN mkdir expense_app
WORKDIR /expense_app
ADD . .
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client && \
    apk add --update --no-cache --virtual .tmp-deps \
        build-base postgresql-dev musl-dev && \
    /opt/venv/bin/pip install -r requirements.txt && \
    apk del .tmp-deps && \
    chmod +x entrypoint.sh && \
    chmod +x migrate.sh && \
    adduser --disabled-password --no-create-home expense_app_user
ENV PATH="/opt/venv/bin:$PATH"
USER expense_app_user