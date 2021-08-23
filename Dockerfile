FROM python:3.7-alpine 

COPY . /home/li20/python/dso-testclient

WORKDIR /home/li20/python/dso-testclient/client
RUN chmod -o+x /home/li20/python/dso-testclient/client/dsoTest.sh
RUN chmod 777 /home/li20/python/dso-testclient/shell.sh
RUN chmod 777 /home/li20/python/dso-testclient/client/dsoApp.sh
RUN pip install -r ../requirements.txt

CMD ["/home/li20/python/dso-testclient/client/dsoApp.sh"]

