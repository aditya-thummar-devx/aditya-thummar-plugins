#!/usr/bin/env python3
"""
Reachability check for the listing's public URLs.

The privacy-policy, support and marketing URLs are public pages, so no
credential is involved. Guideline 2.1 requires "fully functional URLs", and a
dead support or privacy link is a common, avoidable rejection.

One thing this script is deliberately careful about: a 403 is NOT proof a page
is dead. Many hosts and CDNs block non-browser user agents. The script tries a
browser-like user agent, follows redirects, and reports the status code rather
than a verdict — the human confirms a suspicious one in a real browser.

Usage:
  python3 check-urls.py URL [URL ...]
  python3 check-urls.py --json URL [URL ...]
"""

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.request

BROWSER_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
              "AppleWebKit/605.1.15 (KHTML, like Gecko) "
              "Version/17.0 Safari/605.1.15")

PLACEHOLDER_HOSTS = ("localhost", "127.0.0.1", "example.com", "example.org",
                     "staging.", "yourdomain", "changeme", "todo")


def looks_placeholder(url):
    low = url.lower()
    return [h for h in PLACEHOLDER_HOSTS if h in low]


def _verified_context():
    """
    Prefer certifi's CA bundle when it is installed. Python on macOS often has
    no usable system trust store, which makes every https URL fail cert
    verification — a false "dead link" for a perfectly live page.
    """
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _request(url):
    return urllib.request.Request(url, method="GET", headers={
        "User-Agent": BROWSER_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    })


def _body_looks_placeholder(body):
    low = body.lower()
    return any(s in low for s in ("under construction", "coming soon", "lorem ipsum"))


def check(url, timeout=15):
    result = {"url": url, "ok": False, "status": None, "finalUrl": url,
              "note": None, "placeholder": looks_placeholder(url)}

    if not url.lower().startswith(("http://", "https://")):
        result["note"] = "not an http(s) URL"
        return result

    # A placeholder host is a finding no matter what it returns — a localhost or
    # example.com privacy URL in a real listing fails 2.1 even when it serves a
    # 200 from someone's dev machine.
    if result["placeholder"]:
        result["note"] = f"placeholder host ({', '.join(result['placeholder'])}) — not a real URL"
        # still probe, but ok stays false regardless

    ctx = _verified_context()
    try:
        with urllib.request.urlopen(_request(url), timeout=timeout, context=ctx) as resp:
            result["status"] = resp.status
            result["finalUrl"] = resp.geturl()
            body = resp.read(4096).decode("utf-8", "ignore")
            if not result["placeholder"]:
                result["ok"] = 200 <= resp.status < 300
                if result["ok"] and _body_looks_placeholder(body):
                    result["note"] = "reachable, but the page body looks like a placeholder"
                    result["ok"] = False
        return result
    except urllib.error.HTTPError as exc:
        result["status"] = exc.code
        if exc.code in (401, 403, 405, 406, 429):
            # Not a verdict: bot-blocking, not a missing page.
            result["note"] = (f"HTTP {exc.code} to an automated request — may still be "
                              f"live in a browser; confirm manually")
        else:
            result["note"] = f"HTTP {exc.code}"
        return result
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, ssl.SSLCertVerificationError):
            # Retry unverified. This is a reachability check, not a security
            # check: if the host answers, the URL is live, and a local cert
            # failure is almost always this machine's trust store, not the site.
            try:
                unverified = ssl._create_unverified_context()
                with urllib.request.urlopen(_request(url), timeout=timeout,
                                            context=unverified) as resp:
                    result["status"] = resp.status
                    result["finalUrl"] = resp.geturl()
                    if not result["placeholder"]:
                        result["ok"] = 200 <= resp.status < 300
                    result["note"] = ("reachable, but its TLS certificate could not be "
                                      "verified in this environment — usually a local "
                                      "Python cert-store issue on macOS, not a site "
                                      "problem; confirm in a browser")
                    return result
            except Exception as inner:
                result["note"] = f"TLS verification failed and retry unreachable: {inner}"
                return result
        result["note"] = f"unreachable: {reason}"
        return result
    except (TimeoutError, OSError) as exc:
        result["note"] = f"unreachable: {exc}"
        return result


def main():
    ap = argparse.ArgumentParser(description="Check the listing's public URLs are live.")
    ap.add_argument("urls", nargs="+")
    ap.add_argument("--json", dest="as_json", action="store_true")
    ap.add_argument("--timeout", type=int, default=15)
    args = ap.parse_args()

    results = [check(u, args.timeout) for u in args.urls]

    if args.as_json:
        print(json.dumps(results, indent=2))
        return 0

    for r in results:
        mark = "ok  " if r["ok"] else "??  " if r["note"] and "confirm" in r["note"] else "FAIL"
        print(f"[{mark}] {r['url']}")
        if r["finalUrl"] != r["url"]:
            print(f"        -> {r['finalUrl']}  ({r['status']})")
        elif r["status"]:
            print(f"        status {r['status']}")
        if r["placeholder"]:
            print(f"        placeholder host: {', '.join(r['placeholder'])}")
        if r["note"]:
            print(f"        {r['note']}")

    # Exit non-zero only on genuine failure, not on a needs-confirmation 403.
    hard_fail = any(not r["ok"] and not (r["note"] and "confirm" in r["note"])
                    for r in results)
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
