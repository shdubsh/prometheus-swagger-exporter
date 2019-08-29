#!/usr/bin/env python


from bottle import run, route, request
from servicechecker import CheckerBase
from servicechecker.swagger import CheckService
from gevent import monkey; monkey.patch_all()  # noqa
import gevent
from contextlib import contextmanager
from datetime import datetime
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.exposition import generate_latest


class MetricsCollection(list):
    def collect(self):
        for x in self:
            yield x

    # python2.7 does not have clear()
    def clear(self):
        del self[:]


METRICS = MetricsCollection()


@contextmanager
def timing(label, hostname):
    start = datetime.utcnow()
    yield
    delta = datetime.utcnow() - start
    gmf = GaugeMetricFamily(
        'service_checker_request_duration_seconds',
        label,
        labels=['path', 'host']
    )
    gmf.add_metric(value=delta.total_seconds(), labels=[label, hostname])
    METRICS.append(gmf)


def execute_check(host_ip, base_url, spec_url='/?spec', timeout=5):
    METRICS.clear()
    checker = CheckService(host_ip, base_url, timeout, spec_url)
    # Spawn the downloaders
    checks = [
        {
            'ep': ep,
            'data': data,
            'job': gevent.spawn(checker._check_endpoint, ep, data, timing)
        } for ep, data in checker.get_endpoints()
    ]
    gevent.joinall([v['job'] for v in checks], CheckerBase.nrpe_timeout - 2)


@route('/v1/metrics')
def metrics():
    timeout = request.query.timeout if request.query.timeout else 5
    spec_url = request.query.spec_url if request.query.spec_url else '/?spec'
    execute_check(request.query.host_ip, request.query.base_url, spec_url, timeout)
    return generate_latest(METRICS)


if __name__ == '__main__':
    run(host='localhost', port='8080')
