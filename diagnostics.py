"""Diagnostics script to test robots.txt and page fetching in CI."""

from http_utils import can_fetch, fetch_url

URLS = [
    "https://www.koupalistebrno.cz/robots.txt",
    "https://riviera.starez.cz/robots.txt",
    "https://www.kravihora-brno.cz/kryta-plavecka-hala",
    "https://riviera.starez.cz/",
]

SNIPPET_LEN = 200


def main():
    results = []

    for url in URLS:
        print(f"\n{'='*60}")
        print(f"Testing: {url}")
        print(f"{'='*60}")

        allowed = can_fetch(url)
        print(f"  can_fetch: {allowed}")

        content = fetch_url(url)
        if content is not None:
            snippet = content[:SNIPPET_LEN].replace("\n", " ")
            print(f"  fetch_url: OK ({len(content)} chars)")
            print(f"  snippet: {snippet}...")
        else:
            print("  fetch_url: FAILED (None)")

        results.append((url, allowed, content is not None))

    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    for url, allowed, fetched in results:
        status = "✓" if fetched else "✗"
        print(f"  {status} {url}  (can_fetch={allowed}, fetched={fetched})")

    all_ok = all(fetched for _, _, fetched in results)
    print(f"\nOverall: {'ALL PASSED' if all_ok else 'SOME FAILED'}")
    return all_ok


if __name__ == "__main__":
    main()