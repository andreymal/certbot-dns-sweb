import logging
import random
import time
from typing import Any, Callable, List, Optional, cast

from certbot.plugins import dns_common
from certbot.plugins.dns_common import CredentialsConfiguration

from .sweb_api import SWebAPI
from .sweb_client import SWebClient

logger = logging.getLogger(__name__)


class Authenticator(dns_common.DNSAuthenticator):
    """DNS Authenticator for SpaceWeb"""

    description = "Obtain certificates using a DNS TXT record (if you are using SpaceWeb for DNS)."

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.credentials: Optional[CredentialsConfiguration] = None
        self._client: Optional[SWebAPI] = None
        self._my_tokens: List[str] = []

    @classmethod
    def add_parser_arguments(
        cls,
        add: Callable[..., None],
        default_propagation_seconds: int = 1200,
    ) -> None:
        super().add_parser_arguments(add, default_propagation_seconds)
        add("credentials", help="SpaceWeb credentials INI file.")

    def more_info(self) -> str:
        return (
            "This plugin configures a DNS TXT record to respond to a dns-01 challenge "
            "using the SpaceWeb unofficial API."
        )

    def _setup_credentials(self) -> None:
        self.credentials = self._configure_credentials(
            "credentials",
            "SpaceWeb credentials INI file",
            required_variables={
                "username": "SpaceWeb username",
                "password": "SpaceWeb password",
            },
        )

    @classmethod
    def _get_subdomain(cls, domain: str, validation_name: str) -> str:
        # ("example.com", "_acme-challenge.example.com") -> "_acme-challenge"
        if validation_name == domain or validation_name.endswith("." + domain):
            return validation_name[: -(len(domain) + 1)] or "@"
        return validation_name

    def _i_am_human(self, tm: float = 5.0, rnd: float = 1.15) -> None:
        t = tm
        n = int(rnd * 100)
        if n:
            t += random.randrange(-n, n + 1) / 100.0

        # https://www.youtube.com/watch?v=fsF7enQY8uI
        time.sleep(t)

    def _drop_old_txt(self, domain: str, validation_name: str) -> int:
        subdomain = self._get_subdomain(domain, validation_name)
        removed_count = 0
        while True:
            self._i_am_human()
            old_txt = self._get_client().domains_dns_info_find(
                domain=domain,
                subdomain=subdomain,
                type="TXT",
            )
            old_txt = [x for x in old_txt if x["value"] not in self._my_tokens]
            if not old_txt:
                break

            x = old_txt[-1]
            logger.info(
                "Removing outdated TXT record for %s (%d left)",
                validation_name,
                len(old_txt),
            )
            self._i_am_human()
            self._get_client().domains_dns_edit_txt(
                domain=domain,
                action="del",
                subdomain=subdomain,
                index=cast(int, x["index"]),
            )
            removed_count += 1

        logger.info("Removed %d old TXT records", removed_count)
        return removed_count

    def _perform(self, domain: str, validation_name: str, validation: str) -> None:
        assert self.credentials is not None  # mypy hint

        self._my_tokens.append(validation)

        if self.credentials.conf("drop_old_txt") == "1":
            self._drop_old_txt(domain, validation_name)

        logger.info("Adding TXT record for %s", validation_name)
        self._i_am_human()
        self._get_client().domains_dns_edit_txt(
            domain=domain,
            action="add",
            subdomain=self._get_subdomain(domain, validation_name),
            value=validation,
        )

    def _cleanup(self, domain: str, validation_name: str, validation: str) -> None:
        subdomain = self._get_subdomain(domain, validation_name)

        self._i_am_human()
        for x in self._get_client().domains_dns_info_find(
            domain=domain,
            subdomain=subdomain,
            type="TXT",
        ):
            if x["value"] == validation:
                logger.info("Removing TXT record for %s", validation_name)
                self._i_am_human()
                self._get_client().domains_dns_edit_txt(
                    domain=domain,
                    action="del",
                    subdomain=subdomain,
                    index=cast(int, x["index"]),
                )
                break

    def _get_client(self) -> SWebAPI:
        if self._client is not None:
            return self._client

        assert self.credentials is not None  # mypy hint

        logger.info("Authenticate on SpaceWeb...")
        c = SWebClient(
            username=self.credentials.conf("username") or "",
            password=self.credentials.conf("password") or "",
            user_agent=self.credentials.conf("user_agent"),
        )
        logger.info("Successfully authenticated; api version %s", c.jsonrpc_api_version)
        self._client = SWebAPI(c)
        return self._client
