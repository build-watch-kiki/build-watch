"""Readiness probe for the API container."""

from urllib.request import urlopen


def main() -> None:
    urlopen("http://127.0.0.1:8000/health", timeout=3).close()


if __name__ == "__main__":
    main()
