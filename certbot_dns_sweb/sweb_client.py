#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import json
import random
from datetime import datetime

import requests

try:
    from typing import Any, Optional, Dict
except ImportError:
    from acme.magic_typing import Any, Optional, Dict  # type: ignore

try:
    # Python 3
    from urllib.parse import urljoin
except ImportError:
    # Python 2
    from urlparse import urljoin  # type: ignore


class SWebError(Exception):
    pass


class SWebRPCError(SWebError):
    def __init__(self, code, message, data=None):
        # type: (int, str, Any) -> None
        super(SWebRPCError, self).__init__(message)
        self.code = code
        self.message = message
        self.data = data


class SWebClient(object):
    JSONRPC_BASE_URL = "https://cp.sweb.ru/"
    JSONRPC_ORIGIN = "https://cp.sweb.ru"
    JSONRPC_REFERRER = "https://cp.sweb.ru/main"

    AUTH_PAGE_URL = "https://mcp.sweb.ru/main/auth/"
    AUTH_SUBMIT_URL = "https://mcp.sweb.ru/main/auth_submit/"
    AUTH_REDIRECT_TO_URL = "//mcp.sweb.ru/main/index/"
    AUTH_SUCCESS_LOCATION_URL = "https://cp.sweb.ru/"

    def __init__(
        self,
        username,  # type: str
        password,  # type: str
        user_agent=None,  # type: Optional[str]
        lazy_login=False,  # type: bool
    ):
        # type: (...) -> None
        import certbot_dns_sweb

        self.username = username
        self.password = password

        self._je = json.JSONEncoder(ensure_ascii=True)
        self._jsonrpc_api_version = ""
        self._jsonrpc_user = ""
        self._jsonrpc_dt = datetime.now()
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": user_agent or "Mozilla/5.0; certbot-dns-sweb/{}".format(certbot_dns_sweb.__version__),
        })

        if not lazy_login:
            self.login()

    @property
    def jsonrpc_api_version(self):
        # type: () -> str
        return self._jsonrpc_api_version

    def login(self):
        # type: () -> None

        # Grab cookies
        self._session.get(self.AUTH_PAGE_URL)
        darksecret = str(self._session.cookies.get("darksecret", ""))  # type: ignore

        # send form
        resp = self._session.post(
            self.AUTH_SUBMIT_URL,
            data={
                "login": self.username,
                "password": self.password,
                "new_panel": "1",
                "to": self.AUTH_REDIRECT_TO_URL,
                "savepref": "",
                "darksecret": darksecret,
            },
            headers={
                "Referer": self.AUTH_PAGE_URL,
                "Accept": "text/html, */*",
            }
        )

        if resp.url != self.AUTH_SUCCESS_LOCATION_URL:
            raise SWebError("Failed to log in (unexpected redirect {!r})".format(resp.url))

        # get jsonrpc api version
        ver_script_url = ""
        for script_url in re.findall(r'<script[^>]+src="([^"]+)"[^>]*?>', resp.text, flags=re.U | re.I):
            if "main~version." in script_url:
                ver_script_url = urljoin(resp.url, script_url)
                break
        if ver_script_url:
            ver_resp = self._session.get(ver_script_url)
            ver = re.findall(r'return *"(1\..+?)"', ver_resp.text, flags=re.U)
            if not ver:
                ver = re.findall(r"return *'(1\..+?)'", ver_resp.text, flags=re.U)
            if ver:
                self._jsonrpc_api_version = ver[-1]
        if not self._jsonrpc_api_version:
            raise SWebError(
                "Failed to get JSONRPC_API_VERSION (tried to get script {!r})".format(ver_script_url)
            )

        # get jsonrpc login
        rpc_resp = dict(self.jsonrpc("account", "getLoginAndType"))
        self._jsonrpc_user = rpc_resp["login"]
        self._jsonrpc_dt = datetime.now()

    def random_string(self, l):
        # type: (int) -> str

        return "".join(
            random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
            for _ in range(l)
        )

    def gen_jsonrpc_id(self):
        # type: () -> str

        # mimic the js behavior
        dt = self._jsonrpc_dt
        return "{}{}{}{}{}{}.{}".format(
            dt.year,
            dt.month - 1,  # sic!
            dt.day,
            dt.hour,
            dt.minute,
            dt.second,
            self.random_string(10),
        )

    def jsonrpc(
        self,
        endpoint,  # type: str
        method,  # type: str
        params=None,  # type: Optional[Dict[str, Any]]
    ):
        # type: (...) -> Any
        if not self._jsonrpc_api_version:
            raise SWebError("Missing JSONRPC_API_VERSION (forgot to log in?)")
        data = {
            "jsonrpc": "2.0",
            "version": self._jsonrpc_api_version,
            "id": self.gen_jsonrpc_id(),
            "user": self._jsonrpc_user,
            "method": method,
            "params": params or {},  # В некоторых местах панели почему-то передаётся [] вместо {}
        }
        if not data["user"]:
            data.pop("user")

        resp = self._session.post(
            self.JSONRPC_BASE_URL + endpoint,
            data=self._je.encode(data).encode("utf-8"),
            headers={
                "Referer": self.JSONRPC_REFERRER,
                "Origin": self.JSONRPC_ORIGIN,
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded",  # Не знаю почему, но так отправляет js
            }
        )

        json_data = dict(resp.json())
        if "error" in json_data:
            raise SWebRPCError(
                code=json_data["error"]["code"],
                message=json_data["error"]["message"],
                data=json_data["error"].get("data"),
            )

        return json_data["result"]
