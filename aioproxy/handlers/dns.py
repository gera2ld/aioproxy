import os
from async_dns import TCP, types
from async_dns.resolver import ProxyResolver

resolver = None

def get_resolver():
    global resolver
    if resolver is None:
        resolver = ProxyResolver(proxies=[
            (None, os.environ.get('DNS_SERVER', '114.114.114.114').split(',')),
        ], protocol=TCP)
    return resolver
