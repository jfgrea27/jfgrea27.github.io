# /// script
# requires-python = ">=3.11"
# dependencies = ["markdown==3.7", "pymdown-extensions==10.12"]
# ///
"""Turn every site/**/index.md into index.html next to it, using template.html."""
import html
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).parent
SITE = ROOT / "site"
TEMPLATE = (ROOT / "template.html").read_text()

MATHJAX = '<script src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js" async></script>'
MERMAID = '<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11.4.1/dist/mermaid.esm.min.mjs"; mermaid.initialize({startOnLoad: true});</script>'


def read(path):
    """Split a file into (front matter dict, markdown body)."""
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip().strip('"')
    return meta, m.group(2)


def url(path):
    rel = path.parent.relative_to(SITE).as_posix()
    return "/" if rel == "." else f"/{rel}/"


def is_draft(meta):
    return meta.get("draft") == "true"


def slugify(text, sep):
    """Heading ids the way Hugo made them: '00 - Basic usage' -> '00---basic-usage'."""
    text = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    return "".join("-" if c == " " else c for c in text if c.isalnum() or c in " -_")


def render(md):
    """Markdown to HTML. Returns (html, needs_mermaid)."""
    mermaid = "```mermaid" in md
    md = re.sub(r"```mermaid\n(.*?)```", lambda m: '<pre class="mermaid">\n' + html.escape(m.group(1)) + "</pre>", md, flags=re.S)
    # markdown drops blank lines inside $$ blocks into separate paragraphs
    md = re.sub(r"\$\$(.*?)\$\$", lambda m: "$$" + re.sub(r"\n\s*\n", "\n", m.group(1)) + "$$", md, flags=re.S)
    # [text](sibling.md) -> ../sibling/
    md = re.sub(r"\]\(([\w-]+)\.md\)", r"](../\1/)", md)
    out = markdown.markdown(
        md,
        extensions=["fenced_code", "tables", "sane_lists", "toc", "pymdownx.arithmatex"],
        extension_configs={"pymdownx.arithmatex": {"generic": True}, "toc": {"slugify": slugify}},
    )
    return out, mermaid


def published(paths):
    """(path, meta) for each non-draft page."""
    for path in paths:
        meta, _ = read(path)
        if not is_draft(meta):
            yield path, meta


def link(path, meta):
    return f'<a href="{url(path)}">{html.escape(meta["title"])}</a>'


def series():
    """Post series newest first, each with its sub-posts in folder order."""
    found = published((SITE / "posts").glob("*/index.md"))
    ordered = sorted(found, key=lambda pm: (pm[1].get("date", ""), pm[0].parent.name), reverse=True)
    return [(path, meta, list(published(sorted(path.parent.glob("*/index.md"))))) for path, meta in ordered]


def sub_posts(children):
    if not children:
        return ""
    return "\n<ul>\n" + "\n".join(f"<li>{link(p, m)}</li>" for p, m in children) + "\n</ul>"


def posts_list(all_series):
    """Nested list of post series and their sub-posts."""
    items = []
    for path, meta, children in all_series:
        item = f'<li>{meta.get("date", "")} &mdash; {link(path, meta)}'
        if meta.get("summary"):
            item += f"<br>{html.escape(meta['summary'])}"
        items.append(item + sub_posts(children) + "</li>")
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def reading_order(all_series):
    """Every post in the order of the posts list: series, then its sub-posts."""
    return [pm for path, meta, children in all_series for pm in [(path, meta), *children]]


def prev_next(path, order):
    """'previous | next' links through the reading order."""
    paths = [p for p, _ in order]
    if path not in paths:
        return ""
    i = paths.index(path)
    parts = []
    if i > 0:
        parts.append("&larr; " + link(*order[i - 1]))
    if i < len(order) - 1:
        parts.append(link(*order[i + 1]) + " &rarr;")
    return "\n<hr>\n<p>" + " | ".join(parts) + "</p>"


def breadcrumb(path):
    """Link back to the parent series for sub-posts."""
    parent = path.parent.parent / "index.md"
    if path.parent.parent.parent.name != "posts" or not parent.exists():
        return ""
    meta, _ = read(parent)
    return f'<p><a href="{url(parent)}">&larr; {html.escape(meta["title"])}</a></p>\n'


def build(path, posts, order):
    meta, md = read(path)
    out = path.with_suffix(".html")
    if is_draft(meta):
        out.unlink(missing_ok=True)
        return
    body, mermaid = render(md)
    body = body.replace("<p>{{ posts }}</p>", posts)
    if path.parent.parent.name == "posts":
        body += sub_posts(list(published(sorted(path.parent.glob("*/index.md")))))
    body += prev_next(path, order)
    if not md.lstrip().startswith("# "):
        date = f"<p><small>{meta['date']}</small></p>\n" if meta.get("date") else ""
        body = f"{breadcrumb(path)}<h1>{html.escape(meta['title'])}</h1>\n{date}{body}"
    scripts = (MATHJAX if "arithmatex" in body else "") + (MERMAID if mermaid else "")
    page = TEMPLATE.replace("{{ title }}", html.escape(meta["title"])).replace("{{ scripts }}", scripts).replace("{{ content }}", body)
    out.write_text(page)
    print(f"built {out.relative_to(ROOT)}")


if __name__ == "__main__":
    all_series = series()
    posts = posts_list(all_series)
    order = reading_order(all_series)
    for path in sorted(SITE.rglob("index.md")):
        build(path, posts, order)
