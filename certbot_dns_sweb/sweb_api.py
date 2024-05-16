from typing import Dict, List, Optional, cast

from .sweb_client import SWebClient


class SWebAPI:
    def __init__(self, client: SWebClient):
        self.client = client

    def jsonrpc(
        self,
        endpoint: str,
        method: str,
        params: Optional[Dict[str, object]] = None,
    ) -> object:
        return self.client.jsonrpc(endpoint, method, params)

    def domains_dns_info(self, domain: str) -> List[Dict[str, object]]:
        raw_result = self.jsonrpc(
            "domains/dns",
            "info",
            {"domain": domain},
        )
        return cast(List[Dict[str, object]], raw_result)

    def domains_dns_info_find(
        self,
        domain: str,
        subdomain: str,
        type: str,  # pylint: disable=redefined-builtin
        *,
        dns_info: Optional[List[Dict[str, object]]] = None,
    ) -> List[Dict[str, object]]:
        if dns_info is None:
            dns_info = self.domains_dns_info(domain)

        result: List[Dict[str, object]] = []
        find_main = bool(not subdomain or subdomain == "@")

        for item in dns_info:
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
        domain: str,
        action: str,
        subdomain: str,
        value: Optional[str] = None,
        index: Optional[int] = None,
    ) -> int:
        params: Dict[str, object] = {
            "domain": domain,
            "action": action,  # add/edit/del
            "subDomain": subdomain or "@",
        }

        if value is not None:
            params["value"] = value
        if index is not None:
            # required for edit and del
            params["index"] = index

        if action == "del":
            params["type"] = "TXT"

        raw_result = self.jsonrpc(
            "domains/dns",
            "editTxt",
            params,
        )
        return int(cast(int, raw_result))
