#!/usr/bin/env python

from bottle import run, route, request
from servicechecker import CheckerBase
from servicechecker.swagger import CheckService
from servicechecker.metrics import Metrics
from gevent import monkey; monkey.patch_all()  # noqa
import gevent
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.exposition import generate_latest
import urllib3


class MetricsCollection(list):
    def collect(self):
        for x in self:
            yield x


class Prometheus(Metrics):
    def __init__(self, **config):
        self.metrics = MetricsCollection()
        self.hostname = config.get('hostname')

    def send(self, delta, tags):
        gmf = GaugeMetricFamily(
            'service_checker_request_duration_seconds',
            [x[1] for x in tags if x[0] == 'path'][0],
            labels=[x[0] for x in tags]
        )
        gmf.add_metric(value=delta.total_seconds(), labels=[x[1] for x in tags])
        self.metrics.append(gmf)

    def _get_tags_for(self, url):
        url = urllib3.util.parse_url(url)
        return [('path', url.path), ('host', url.host)]


def get_metrics(host_ip, base_url, spec_url='/?spec', timeout=5):
    checker = CheckService(
        host_ip,
        base_url,
        timeout,
        spec_url,
        metrics_manager=Prometheus(hostname=host_ip)
    )
    # Spawn the downloaders
    checks = [
        {
            'ep': ep,
            'data': data,
            'job': gevent.spawn(checker._check_endpoint, ep, data)
        } for ep, data in checker.get_endpoints()
    ]
    gevent.joinall([v['job'] for v in checks], CheckerBase.nrpe_timeout - 2)
    return checker.metrics_manager.metrics


@route('/v1/metrics')
def metrics():
    timeout = request.query.timeout if request.query.timeout else 5
    spec_url = request.query.spec_url if request.query.spec_url else '/?spec'
    metrics = get_metrics(request.query.host_ip, request.query.base_url, spec_url, timeout)
    return generate_latest(metrics)


def main():
    # Possible port allocation collision
    # https://github.com/prometheus/prometheus/wiki/Default-port-allocations
    run(host='localhost', port='9220')


if __name__ == '__main__':
    main()
