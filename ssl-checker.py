#!/usr/bin/env python
import multiprocessing
from kubernetes import client, config
import logging
import sys
import socket
import logging
import ssl
import datetime
import os
from bottle import Bottle, request, abort, response

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

app = Bottle()

kube_context = os.environ.get('context', None)
notify = os.environ.get('notify', 30)
kubeconfig = os.environ.get('kubeconfig', '/k8s/kubeconfig')

if not kube_context:
    sys.exit("ERROR: you must set the 'context' environment variable!")

def ssl_expiry_datetime(hostname):
    ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'

    context = ssl.create_default_context()
    conn = context.wrap_socket(
        socket.socket(socket.AF_INET),
        server_hostname=hostname,
    )
    # 3 second timeout because Lambda has runtime limitations
    conn.settimeout(1.0)

    conn.connect((hostname, 443))
    ssl_info = conn.getpeercert()
    # parse the string from the certificate into a Python datetime object
    return datetime.datetime.strptime(ssl_info['notAfter'], ssl_date_fmt)

def ssl_valid_time_remaining(hostname):
    """Get the number of days left in a cert's lifetime."""
    expires = ssl_expiry_datetime(hostname)
    logging.debug(
        "SSL cert for %s expires at %s",
        hostname, expires.isoformat()
    )
    return expires - datetime.datetime.utcnow()

def ssl_expires_in(hostname, buffer_days=notify):
    """Check if `hostname` SSL cert expires is within `buffer_days`.

    Raises `AlreadyExpired` if the cert is past due
    """
    logging.debug("checking: %s" % hostname)
    try:
        remaining = ssl_valid_time_remaining(hostname)

        # if the cert expires in less than two weeks, we should reissue it
        if remaining < datetime.timedelta(days=0):
            # cert has already expired - uhoh!
            raise AlreadyExpired("Cert expired %s days ago" % remaining.days)
        elif remaining < datetime.timedelta(days=buffer_days):
            # expires sooner than the buffer
            return (hostname, 1)
        else:
            # everything is fine
            return (hostname, 0)
    except:
        logging.debug("Unable to read SSL certificate for %s!" % (hostname))
        return (hostname, 1)

def getkubehosts():
    tls_hosts = []
    config.load_kube_config(config_file=kubeconfig, context=kube_context)
    v1 = client.ExtensionsV1beta1Api()
    ret = v1.list_ingress_for_all_namespaces(watch=False)
    for i in ret.items:
      if i.spec.tls:
        for h in i.spec.tls:
            if h.hosts:
               for host in h.hosts:
                   host = host.replace('*.', 'foo.')
                   tls_hosts.append(host)
    return tls_hosts

def getsites():
    pool = multiprocessing.Pool(processes=8)
    pool_outputs = pool.map(ssl_expires_in, getkubehosts())
    pool.close()
    pool.join()
    return dict(pool_outputs)

@app.get('/metrics')
def main():
    response.content_type = 'text/plain; ; version=0.0.4'
    str = ''
    hosts = getsites()
    for h in hosts.keys():
        str += "# HELP site tls error / certificate expires in %d days.\n" % (notify)
        str += "# TYPE ssl_checker_expiration count\n"
        str += "ssl_checker_expiration{site=\"%s\"} %s\n" % (h, hosts[h])
    return str

@app.get('/')
def home():
    return '<a href="/metrics">metrics</a><br>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port='18080', server='tornado', reloader=False)
