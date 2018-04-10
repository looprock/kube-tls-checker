FROM docker.ojointernal.com/images/kubectl:latest
MAINTAINER Doug Land <dland@ojolabs.com>

# change 7

copy requirements.txt /tmp/

RUN \
  apk update \
  && apk add python3 py-pip build-base python3-dev openssl-dev \
  && pip3 install -r /tmp/requirements.txt \
  && apk del build-base \
  && rm -rf /var/cache/apk/*

COPY ssl-checker.py /usr/local/bin
CMD /usr/bin/python3 /usr/local/bin/ssl-checker.py
