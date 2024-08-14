import json
import random
import re
from datetime import datetime, timezone
from typing import Dict, Optional, cast
from urllib.parse import urljoin, urlparse

import requests


class SWebError(Exception):
    pass


class SWebRPCError(SWebError):
    def __init__(self, code: int, message: str, data: object = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class SWebClient:
    AUTH_PAGE_URL = "https://mcp.sweb.ru/main/auth/"
    AUTH_SUBMIT_URL = "https://mcp.sweb.ru/main/auth_submit/"
    AUTH_SUCCESS_LOCATION_URLS = {
        "https://cp.sweb.ru",
        "https://cp.sweb.ru/main",
        "https://vps.sweb.ru",
        "https://vps.sweb.ru/main",
    }

    def __init__(
        self,
        username: str,
        password: str,
        *,
        user_agent: Optional[str] = None,
        lazy_login: bool = False,
    ):
        self.username = username
        self.password = password

        if user_agent is None:
            import importlib.metadata  # pylint: disable=import-outside-toplevel

            ver = importlib.metadata.version("certbot_dns_sweb")
            user_agent = f"Mozilla/5.0; certbot-dns-sweb/{ver}"

        self._je = json.JSONEncoder(ensure_ascii=True)

        self._jsonrpc_base_url = "https://cp.sweb.ru/"
        self._jsonrpc_origin = "https://cp.sweb.ru"
        self._jsonrpc_referrer = "https://cp.sweb.ru/main/"
        self._jsonrpc_api_version = ""
        self._jsonrpc_user = ""
        self._jsonrpc_dt = datetime.now(timezone.utc)

        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": user_agent,
            },
        )

        if not lazy_login:
            self.login()

    @property
    def jsonrpc_api_version(self) -> str:
        return self._jsonrpc_api_version

    def login(self) -> None:
        # Grab cookies
        self._session.get(self.AUTH_PAGE_URL)
        darksecret = str(self._session.cookies.get("darksecret", ""))

        # send form
        resp = self._session.post(
            self.AUTH_SUBMIT_URL,
            data={
                "login": self.username,
                "password": self.password,
                "new_panel": "1",
                "savepref": "",
                "darksecret": darksecret,
            },
            headers={
                "Referer": self.AUTH_PAGE_URL,
                "Accept": "text/html,*/*",
            },
        )

        if resp.url.rstrip("/") not in self.AUTH_SUCCESS_LOCATION_URLS:
            raise SWebError(f"Failed to log in (unexpected redirect {resp.url!r})")

        domain = urlparse(resp.url).netloc
        self._jsonrpc_base_url = f"https://{domain}/"
        self._jsonrpc_origin = f"https://{domain}"
        self._jsonrpc_referrer = f"https://{domain}/main/"

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
            raise SWebError(f"Failed to get JSONRPC_API_VERSION (tried to parse script {ver_script_url!r})")

        # get jsonrpc login
        rpc_resp = cast(Dict[str, object], self.jsonrpc("account", "getProperties"))
        self._jsonrpc_user = str(rpc_resp["login"])
        self._jsonrpc_dt = datetime.now(timezone.utc)

    def random_string(self, l: int) -> str:
        return "".join(
            random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for _ in range(l)
        )

    def gen_jsonrpc_id(self) -> str:
        # mimic the js behavior
        dt = self._jsonrpc_dt
        # pylint: disable=consider-using-f-string
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
        endpoint: str,
        method: str,
        params: Optional[Dict[str, object]] = None,
    ) -> object:
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
            self._jsonrpc_base_url + endpoint,
            data=self._je.encode(data).encode("utf-8"),
            headers={
                "Referer": self._jsonrpc_referrer,
                "Origin": self._jsonrpc_origin,
                "Accept": "application/json, text/plain, */*",
                # js-код зачем-то использует url-кодирование, но всё работает и так, так что ладно, наверное?
                "Content-Type": "application/json",
            },
        )

        json_data = dict(resp.json())
        if "error" in json_data:
            raise SWebRPCError(
                code=json_data["error"]["code"],
                message=json_data["error"]["message"],
                data=json_data["error"].get("data"),
            )

        return json_data["result"]
