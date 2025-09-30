#!/usr/bin/env python3
import argparse
import os

import uvicorn

# Generate e.g. a self-signed cert using:
# openssl req -x509 -newkey rsa:4096 -nodes -keyout key.pem -out cert.pem -days 365 -subj "/CN=zooprocess.com"


def main():
    parser = argparse.ArgumentParser(description="Run ASGI app with Uvicorn over HTTPS")
    parser.add_argument(
        "--host",
        default=os.getenv("HOST", "0.0.0.0"),
        help="Bind host (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8443")),
        help="HTTPS port (default: 8443)",
    )
    parser.add_argument(
        "--proxy-headers",
        action="store_true",
        default=os.getenv("PROXY_HEADERS", "true").lower() == "true",
        help="Respect X-Forwarded-* headers",
    )
    parser.add_argument(
        "--forwarded-allow-ips",
        default=os.getenv("FORWARDED_ALLOW_IPS", "*"),
        help="Comma list of allowed proxy IPs; '*' to trust all",
    )

    # TLS-related
    parser.add_argument(
        "--certfile",
        default=os.getenv("SSL_CERTFILE", "/etc/certs/cert.pem"),
        help="Path to TLS cert",
    )
    parser.add_argument(
        "--keyfile",
        default=os.getenv("SSL_KEYFILE", "/etc/certs/key.pem"),
        help="Path to TLS key",
    )
    parser.add_argument(
        "--ca-certs",
        default=os.getenv("SSL_CA_CERTS"),
        help="Optional CA bundle for client certs",
    )
    parser.add_argument(
        "--ciphers",
        default=os.getenv("SSL_CIPHERS"),
        help="Optional OpenSSL cipher suite string",
    )

    args = parser.parse_args()

    uvicorn.run(
        app="main:app",
        host=args.host,
        port=args.port,
        reload=False,
        workers=1,
        proxy_headers=args.proxy_headers,
        forwarded_allow_ips=args.forwarded_allow_ips,
        ssl_certfile=args.certfile,
        ssl_keyfile=args.keyfile,
        ssl_ca_certs=args.ca_certs,
        ssl_ciphers=args.ciphers,
    )


if __name__ == "__main__":
    main()
