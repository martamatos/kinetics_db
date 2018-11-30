FROM python:3.7-alpine

RUN adduser -D microblog

WORKDIR /home/mrama/kineticsDB/microblog
COPY requirements.txt requirements.txt

RUN apk update && \
 apk add --virtual .build-deps gcc musl-dev postgresql-dev libffi-dev 

RUN pip install -r requirements.txt
RUN pip install gunicorn

COPY app app
COPY migrations migrations
COPY microblog.py config.py boot.sh ./
RUN chmod +x boot.sh

ENV FLASK_APP microblog.py

RUN chown -R microblog:microblog ./
USER microblog

EXPOSE 5000
ENTRYPOINT ["sh", "./boot.sh"]
