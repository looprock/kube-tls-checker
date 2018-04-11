FROM alpine:latest
MAINTAINER Doug Land <dland@ojolabs.com>

copy requirements.txt /tmp/

RUN \
  apk update \
  && apk add python3 py-pip build-base python3-dev libffi-dev openssl-dev ca-certificates bash py-requests \
  && pip3 install -r /tmp/requirements.txt \
  && apk del build-base \
  && rm -rf /var/cache/apk/*

COPY ssl-checker.py /usr/local/bin
CMD /usr/bin/python3 /usr/local/bin/ssl-checker.py
