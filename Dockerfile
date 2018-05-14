FROM microsoft/azure-functions-python3.6:latest

ENV host:logger:consoleLoggingMode=always

COPY . /home/site/wwwroot

RUN cd /home/site/wwwroot && pip install -r requirements.txt
