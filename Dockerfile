FROM python:3.9-slim-buster

COPY ./requirements.txt /home/li20/python/dso-testclient/requirements.txt
WORKDIR /home/li20/python/dso-testclient
RUN pip install -r ./requirements.txt

COPY . /home/li20/python/dso-testclient

WORKDIR /home/li20/python/dso-testclient/client
RUN chmod 777 /home/li20/python/dso-testclient/shell.sh
RUN chmod 777 /home/li20/python/dso-testclient/startTestclient.sh
RUN chmod 777 /home/li20/python/dso-testclient/startWebapp.sh

CMD ["/home/li20/python/dso-testclient/startTestclient.sh"]

