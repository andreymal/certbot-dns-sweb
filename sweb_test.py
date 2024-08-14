import getpass
import random
import sys
import time
from typing import cast

from certbot_dns_sweb.sweb_api import SWebAPI
from certbot_dns_sweb.sweb_client import SWebClient

if len(sys.argv) >= 2:
    username = sys.argv[1]
else:
    username = input("Username: ")


if len(sys.argv) >= 3:
    domain = sys.argv[2]
else:
    domain = input("Domain to test: ")


if sys.stdin.isatty():
    password = getpass.getpass()
else:
    password = input("Password: ")
    print()

if not password:
    print("Password is not set")
    sys.exit(1)


print("Authenticate on SpaceWeb...")
c = SWebClient(
    username=username,
    password=password,
    user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
)
print("Successfully authenticated; api version", c.jsonrpc_api_version)
api = SWebAPI(c)

print("Showing all DNS records:")
time.sleep(2)  # I'm a human!
print()

for x in api.domains_dns_info(domain):
    print(x)
print()


print(f"Adding TXT record for _test-challenge.{domain}")
value = str(random.randrange(10**8, 10**9))
time.sleep(3)

edit_resp = api.domains_dns_edit_txt(
    domain=domain,
    action="add",
    subdomain="_test-challenge",
    value=value,
)

print("Response:", repr(edit_resp))

print("Press Enter to remove the TXT record")
input()

del_resp = None

for x in api.domains_dns_info_find(
    domain=domain,
    subdomain="_test-challenge",
    type="TXT",
):
    if x["value"] == value:
        print(f"Removing TXT record for _test-challenge.{domain}")
        time.sleep(3)
        del_resp = api.domains_dns_edit_txt(
            domain=domain,
            action="del",
            subdomain="_test-challenge",
            index=cast(int, x["index"]),
        )
        print("Response:", repr(del_resp))
        break

if del_resp is None:
    print("We have a problem with domains_dns_info_find")

print("Done.")
