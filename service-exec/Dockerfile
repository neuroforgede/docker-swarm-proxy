FROM docker:24.0.2-cli
RUN apk add python3 py-pip
WORKDIR /code
COPY service_exec.py service_exec.py
RUN pip3 install docker
RUN pip3 install dnspython
ENTRYPOINT ["/bin/python3"]