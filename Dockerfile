FROM python:3.6-alpine3.6

RUN adduser -D kinetics_db

WORKDIR /home/mrama/kineticsDB/kinetics_db
COPY requirements.txt requirements.txt

RUN apk update && \
 apk add --virtual .build-deps gcc g++ musl-dev postgresql-dev libffi-dev 

RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY app app
COPY migrations migrations
COPY data data
COPY kinetics_db.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP kinetics_db.py

RUN chown -R kinetics_db:kinetics_db ./
USER kinetics_db

EXPOSE 5000
ENTRYPOINT ["sh", "./boot.sh"]
