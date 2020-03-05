#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import time
import base64

try:
    from typing import Any, Optional, List, Dict
except ImportError:
    from acme.magic_typing import Any, Optional, List, Dict  # type: ignore

from .sweb_client import SWebError, SWebRPCError, SWebClient


class SWebAPI(object):
    def __init__(
        self,
        client,  # type: SWebClient
    ):
        self.client = client

    def jsonrpc(
        self,
        endpoint,  # type: str
        method,  # type: str
        params=None,  # type: Optional[Dict[str, Any]]
    ):
        # type: (...) -> Any
        return self.client.jsonrpc(endpoint, method, params)

    def domains_dns_info(self, domain):
        # type: (str) -> List[Dict[str, Any]]
        return list(self.jsonrpc(
            "domains/dns",
            "info",
            {"domain": domain},
        ))

    def domains_dns_info_find(
        self,
        domain,  # type: str
        subdomain,  # type: str
        type,  # type: str
        data=None,  # type: Any
    ):
        # type: (...) -> List[Dict[str, Any]]
        if data is None:
            data = self.domains_dns_info(domain)

        result = []  # type: List[Dict[str, Any]]
        find_main = bool(not subdomain or subdomain == "@")

        for item in data:
            # A/AAAA @/www
            if item["category"] == "zoneMain" and item["type"] == type:
                if item["name"] == subdomain or find_main and item["name"] in ("", "@"):
                    result.append(item)
                continue

            # A/AAAA/CNAME subdomain
            if item["category"] == "subdom" and item["type"] == type:
                if item["name"] == subdomain or find_main and item["name"] in ("", "@"):
                    result.append(item)
                continue

            # MX @/subdomain
            if type == "MX" and item["category"] == "mx":
                if item["name"] == subdomain or find_main and item["name"] in ("", "@"):
                    result.append(item)
                continue

            # TXT @
            if type == "TXT" and item["category"] == "mainTxt":
                if item["domain"] == subdomain or find_main and item["domain"] in ("", "@"):
                    result.append(item)
                continue

            # TXT subdomain
            if type == "TXT" and item["category"] == "subdomTxt":
                if item["domain"] == subdomain or find_main and item["domain"] in ("", "@"):
                    result.append(item)
                continue

        return result

    def domains_dns_edit_txt(
        self,
        domain,  # type: str
        action,  # type: str
        subdomain, # type: str
        value=None,  # type: Optional[str]
        index=None,  # type: Optional[int]
    ):
        # type: (...) -> int

        params = {
            "domain": domain,
            "action": action,  # add/edit/del
            "subDomain": subdomain or "@",
        }  # type: Dict[str, Any]

        if value is not None:
            params["value"] = value
        if index is not None:
            # required for edit and del
            params["index"] = index

        if action == "del":
            params["type"] = "TXT"

        return self.jsonrpc(
            "domains/dns",
            "editTxt",
            params,
        )

    def vh_ssl_index(self):
        # type: () -> Dict[str, Any]
        return dict(self.jsonrpc(
            "vh/ssl",
            "index",
        ))

    def vh_ssl_get_customer_ips(self):
        # type: () -> List[Dict[str, str]]
        return list(self.jsonrpc(
            "vh/ssl",
            "getCustomerIps",
        ))

    def vh_ssl_install_certificate(
        self,
        crt,  # type: bytes
        key,  # type: bytes
        ca_bundles=None,  # type: Optional[List[bytes]]
        domain=None,  # type: Optional[str]
        ip="sni",  # type: str
    ):
        # type: (...) -> int

        files = []  # type: List[Dict[str, str]]

        files.append({
            "name": "crt",
            "base64": "data:application/x-x509-ca-cert;base64," + base64.b64encode(crt).decode("ascii"),
        })
        files.append({
            "name": "key",
            "base64": "data:application/x-x509-ca-cert;base64," + base64.b64encode(key).decode("ascii"),
        })
        for ca in ca_bundles or []:
            files.append({
                "name": "ca-bundle",
                "base64": "data:application/x-x509-ca-cert;base64," + base64.b64encode(ca).decode("ascii"),
            })

        params = {
            "domain": domain or None,
            "ip": ip,
            "files": files,
        }  # type: Dict[str, Any]

        # if it returns 2, you should repeat this call
        return self.jsonrpc(
            "vh/ssl",
            "installCertificate",
            params
        )

    def vh_ssl_remove_certificate(
        self,
        certificate_id,  # type: str
    ):
        # type: (...) -> int
        return self.jsonrpc(
            "vh/ssl",
            "removeCertificate",
            {"certificateId": certificate_id},
        )

    def vh_ssl_delete_inactive_certificates(self, data=None):
        # type: (Any) -> List[Dict[str, Any]]
        removed = []  # type: List[Dict[str, Any]]
        if data is None:
            data = self.vh_ssl_index()["list"]
        for cert in data:
            if removed:
                time.sleep(3)
            if cert.get("status", "").strip().lower() == "не активен":
                removed.append(cert)
                result = self.vh_ssl_remove_certificate(cert["id"])
                if result not in (1, True):
                    raise SWebError("Failed to remove certificate: unexpected result {!r}".format(result))
        return removed
