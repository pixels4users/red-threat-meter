"""Explicit primary documents for resolving a case; never a complete news feed."""
from datetime import datetime
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .collect import allowed_url
from .common import clean_text, digest, instant, now


def parse_document(body, parser):
    soup = BeautifulSoup(body, "html.parser")
    if parser == "lv_mod":
        title = soup.select_one("h1")
        content = soup.select_one(".l-content-main .field--name-body")
        stamp = soup.select_one(".field--name-field-publishing-date-time")
        date = datetime.strptime(stamp.get_text(strip=True), "%d.%m.%Y") if stamp else None
    elif parser == "lv_vdd":
        article = soup.select_one("article.article-block")
        title = article.select_one("h1") if article else None
        content = article.select_one(".article-content") if article else None
        stamp = article.select_one("time[datetime]") if article else None
        date = datetime.strptime(stamp["datetime"], "%Y-%m-%d") if stamp else None
    else:
        raise ValueError("Unknown primary document parser")
    if not title or not content or not date:
        raise ValueError("Primary document title, date or body missing")
    for el in content.select("script,style,nav,form,iframe"):
        el.decompose()
    text = clean_text(content.get_text(" ", strip=True))
    if len(text) < 150:
        raise ValueError("Primary document body too short")
    if date.date() > instant(now()).astimezone(ZoneInfo("Europe/Riga")).date():
        raise ValueError("Future publication date")
    return {"title": clean_text(title.get_text(" ", strip=True)), "text": text,
            "text_kind": "article_body", "published_at": None,
            # A publisher's calendar day is not a midnight timestamp. Keep its
            # precision in the versioned source record instead of shifting the
            # date backwards when a Polish client renders Latvian midnight.
            "source_record": {"published_on": date.date().isoformat(),
                              "publication_date_precision": "day"}}


def collect_documents(source, fetcher):
    result = {"source_id": source["id"], "publisher": source["publisher"],
              "required": source["required"], "status": "error", "items": [], "errors": [],
              "window_complete": False, "scope": "selected_primary_documents_only",
              "source_definition_hash": digest(source)}
    urls = source["document_urls"]
    if len(urls) > source["max_items"]:
        result["errors"].append("Selected document limit exceeded")
    for url in urls[:source["max_items"]]:
        try:
            body, content_type, final, raw_ref = fetcher.get(allowed_url(url, source))
            result["items"].append({**parse_document(body, source["document_parser"]),
                                    "url": url, "raw_ref": raw_ref,
                                    "content_provenance": {"url": final, "raw_ref": raw_ref,
                                                           "content_type": content_type}})
        except Exception as exc:
            result["errors"].append(f"Primary document unavailable ({type(exc).__name__}): {url}")
    result.update(checked_at=now(), raw_refs=list(dict.fromkeys(fetcher.raw_refs)),
                  request_count=getattr(fetcher, "request_count", None),
                  retry_at=getattr(fetcher, "retry_at", None))
    result["status"] = ("partial" if result["items"] else "error") if result["errors"] else "ok"
    return result
