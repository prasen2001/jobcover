import ipaddress
import socket
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class UnsafeUrlError(ValueError):
    pass


def fetch_job_description(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise UnsafeUrlError("Enter a valid http or https job URL.")
    _assert_public_host(parsed.hostname)
    response = requests.get(
        url,
        timeout=12,
        allow_redirects=False,
        headers={"User-Agent": "JobCover/1.0 (+local resume assistant)"},
    )
    if 300 <= response.status_code < 400:
        raise UnsafeUrlError("Redirecting job links are not fetched for security; paste the final URL.")
    response.raise_for_status()
    content_type = response.headers.get("content-type", "")
    if "html" not in content_type:
        raise ValueError("The job link did not return an HTML page.")
    soup = BeautifulSoup(response.text[:2_000_000], "html.parser")
    for element in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        element.decompose()
    text = "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())
    if len(text) < 100:
        raise ValueError("The page did not contain enough readable job text. Paste the description instead.")
    return text[:50_000]


def _assert_public_host(hostname: str):
    if hostname.lower() in {"localhost", "localhost.localdomain"}:
        raise UnsafeUrlError("Local and private addresses are not allowed.")
    try:
        addresses = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrlError("The job link host could not be resolved.") from exc
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise UnsafeUrlError("Local and private addresses are not allowed.")

