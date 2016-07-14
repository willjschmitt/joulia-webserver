FROM continuumio/anaconda
MAINTAINER William Schmitt (william@wschmitt.com)

ENV PYTHONUNBUFFERED 1

RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get install -y python-dev
RUN apt-get install -y libmysqlclient-dev

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/

RUN python manage.py migrate --noinput
RUN python manage.py collectstatic --noinput

CMD [ "python", "./main.py" ]

EXPOSE 8888