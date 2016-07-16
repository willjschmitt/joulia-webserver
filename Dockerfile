FROM continuumio/anaconda
MAINTAINER William Schmitt (william@wschmitt.com)

ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get install -y python-dev
RUN apt-get install -y libmysqlclient-dev

RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install -r requirements.txt

CMD ["sh", "./deploy.sh"]

EXPOSE 8888