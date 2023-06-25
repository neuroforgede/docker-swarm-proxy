FROM --platform=${BUILDPLATFORM:-linux/amd64} docker:24.0.2-cli
RUN apk add python3 py-pip
WORKDIR /code
COPY proxy.py proxy.py
RUN pip3 install docker
RUN pip3 install dnspython
ENTRYPOINT ["python3", "proxy.py"]
