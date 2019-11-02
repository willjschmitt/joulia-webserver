FROM python:3.5
MAINTAINER William Schmitt (william@wschmitt.com)

RUN apt-get update
RUN apt-get install -y build-essential
RUN apt-get install -y python-dev
RUN apt-get install -y libmysqlclient-dev

RUN npm install -g bower

RUN mkdir /code
ADD . /code/
WORKDIR /code
RUN pip install -r requirements.txt

ENTRYPOINT ["/bin/bash"]
CMD ["./deploy.sh"]

EXPOSE 8888