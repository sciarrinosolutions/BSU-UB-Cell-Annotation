"""Check the help pages in web/help/ for broken links.

Reports:
  - links between help pages to missing pages or missing #sections
  - links from the app (web/index.html, web/*.js) to missing help pages or sections
  - help pages that aren't in the menu list in help.js, or menu entries with no file
  - help pages without a "Last reviewed" date

Run on its own, or automatically at the end of build_index.py.

Usage:
    python pipeline/check_help.py
"""

import re
import sys
from html.parser import HTMLParser

from common import ROOT

WEB = ROOT / "web"
HELP = WEB / "help"
APP_LINK = re.compile(r"""["'](help/[\w.-]+\.html(?:#[\w-]+)?)["']""")


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.hrefs.append(attrs["href"])


def parse(path):
    p = PageParser()
    p.feed(path.read_text(encoding="utf-8"))
    return p


def check():
    problems = []
    pages = {f.name: parse(f) for f in sorted(HELP.glob("*.html"))}

    def resolve(target, where):
        file, _, anchor = target.partition("#")
        if file not in pages:
            problems.append(f"{where}: links to missing help page {file}")
        elif anchor and anchor not in pages[file].ids:
            problems.append(f"{where}: links to missing section #{anchor} in {file}")

    # Links within and between help pages.
    for name, page in pages.items():
        for href in page.hrefs:
            if re.match(r"^(https?:|mailto:|\.\./)", href):
                continue
            target = href if not href.startswith("#") else f"{name}{href}"
            resolve(target, f"help/{name}")
        if "Last reviewed" not in (HELP / name).read_text(encoding="utf-8"):
            problems.append(f"help/{name}: no 'Last reviewed' date")

    # Links from the app into the help.
    for src in [WEB / "index.html", *sorted(WEB.glob("*.js"))]:
        for target in APP_LINK.findall(src.read_text(encoding="utf-8")):
            resolve(target.removeprefix("help/"), src.name)

    # The menu list in help.js must match the files.
    menu = set(re.findall(r'\["([\w.-]+\.html)"', (HELP / "help.js").read_text(encoding="utf-8")))
    for name in sorted(set(pages) - menu):
        problems.append(f"help/{name}: not listed in the help.js menu")
    for name in sorted(menu - set(pages)):
        problems.append(f"help.js: menu lists {name}, which doesn't exist")

    return pages, problems


def main():
    pages, problems = check()
    if problems:
        print(f"Help check: {len(problems)} problem(s) in {len(pages)} pages:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print(f"Help check: {len(pages)} pages, no broken links.")


if __name__ == "__main__":
    main()
