FROM ubuntu:18.04                                                                                                                                                                                                  

RUN apt update && apt install -y ssh=1:7.6p1-4ubuntu0.3 && apt install -y python3=3.6.7-1~18.04 && apt install -y python3-pip=9.0.1-2.3~ubuntu1.18.04.1 && apt install -y net-tools=1.60+git20161116.90da8a0-1ubuntu1 && apt install -y inotify-tools=3.14-2 && DEBIAN_FRONTEND=noninteractive apt install -y tzdata=2019c-0ubuntu0.18.04 && ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime && dpkg-reconfigure -f noninteractive tzdata

RUN pip3 install flask-restful==0.3.7 uwsgi==2.0.17.1 psycopg2-binary==2.8.2

RUN mkdir -p /etc/j4j/J4J_Orchestrator

RUN adduser --disabled-password --gecos '' orchestrator

RUN chown orchestrator:orchestrator /etc/j4j/J4J_Orchestrator

USER orchestrator

COPY --chown=orchestrator:orchestrator ./app /etc/j4j/J4J_Orchestrator/app

COPY --chown=orchestrator:orchestrator ./app.py /etc/j4j/J4J_Orchestrator/app.py

COPY --chown=orchestrator:orchestrator ./scripts /etc/j4j/J4J_Orchestrator

COPY --chown=orchestrator:orchestrator ./uwsgi.ini /etc/j4j/J4J_Orchestrator/uwsgi.ini

WORKDIR /etc/j4j/J4J_Orchestrator

CMD /etc/j4j/J4J_Orchestrator/start.sh
