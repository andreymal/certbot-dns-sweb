#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function

import sys
import time
import random
import getpass

from certbot_dns_sweb.sweb_client import SWebClient
from certbot_dns_sweb.sweb_api import SWebAPI

if sys.version_info.major != 2:
    raw_input = input


if len(sys.argv) >= 2:
    username = sys.argv[1]
else:
    username = raw_input("Username: ")


if len(sys.argv) >= 3:
    domain = sys.argv[2]
else:
    domain = raw_input("Domain to test: ")


if sys.stdin.isatty():
    password = getpass.getpass()
else:
    password = raw_input('Password: ')
    print()

if not password:
    print('Password is not set')
    sys.exit(1)


print("Authenticate on SpaceWeb...")
c = SWebClient(
    username=username,
    password=password,
    user_agent= "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/80.0.3987.87 Chrome/80.0.3987.87 Safari/537.36",
)
print("Successfully authenticated; api version", c.jsonrpc_api_version)
api = SWebAPI(c)

print("Showing all DNS records:")
time.sleep(2)  # I'm a human!
print()

for x in api.domains_dns_info(domain):
    print(x)
print()


print("Adding TXT record for _test-challenge.%s" % domain)
value = str(random.randrange(10 ** 8, 10 ** 9))
time.sleep(3)

edit_resp = api.domains_dns_edit_txt(
    domain=domain,
    action="add",
    subdomain="_test-challenge",
    value=value,
)

print("Response:", repr(edit_resp))

time.sleep(6)

del_resp = None

for x in api.domains_dns_info_find(
    domain=domain,
    subdomain="_test-challenge",
    type="TXT",
):
    if x["value"] == value:
        print("Removing TXT record for _test-challenge.%s" % domain)
        time.sleep(3)
        del_resp = api.domains_dns_edit_txt(
            domain=domain,
            action="del",
            subdomain="_test-challenge",
            index=x["index"],
        )
        print("Response:", repr(del_resp))
        break

if del_resp is None:
    print("We have a problem with domains_dns_info_find")

print("Done.")
