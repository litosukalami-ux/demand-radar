# -*- coding: utf-8 -*-
"""需求雷达 · 采集脚本（GitHub Actions 运行，标准库实现）"""
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
TIMEOUT = 25


def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read().decode("utf-8")


def get_json(url):
    return json.loads(get(url))


def fetch_charts():
    out = {"free": [], "paid": [], "errors": []}
    for key, path in (("free", "topfreeapplications"), ("paid", "toppaidapplications")):
        try:
            j = get_json("https://itunes.apple.com/cn/rss/%s/limit=50/json" % path)
            out[key] = [e["im:name"]["label"] for e in j["feed"]["entry"]]
        except Exception as e:
            out["errors"].append("charts/%s: %s" % (key, e))
    return out


def fetch_weibo_hot():
    try:
        j = get_json("https://weibo.com/ajax/side/hotSearch")
        return [x.get("note", "") for x in j["data"]["realtime"][:30] if x.get("note")]
    except Exception as e:
        return ["[weibo failed] " + str(e)[:80]]


def fetch_bili_rank():
    try:
        j = get_json("https://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all")
        return [x.get("title", "") for x in j["data"]["list"][:30] if x.get("title")]
    except Exception as e:
        return ["[bili failed] " + str(e)[:80]]


def app_search(term):
    try:
        j = get_json("https://itunes.apple.com/cn/search?term=%s&entity=software&limit=1" % urllib.parse.quote(term))
        return j["results"][0] if j.get("results") else None
    except Exception:
        return None


def app_reviews(app_id, pages=2):
    revs = []
    for p in range(1, pages + 1):
        try:
            j = get_json("https://itunes.apple.com/cn/rss/customerreviews/page=%d/id=%d/sortBy=mostRecent/json" % (p, app_id))
            for e in j.get("feed", {}).get("entry", []):
                revs.append({
                    "rating": int(e["im:rating"]["label"]),
                    "title": e["title"]["label"],
                    "content": e["content"]["label"],
                    "date": e["updated"]["label"][:10],
                })
        except Exception:
            pass
    return revs


def collect_complaints():
    terms = ["简历", "租房", "装修", "考研", "相亲", "副业", "留学", "体检", "求职", "健身", "减肥", "手机"]
    rows = []
    errors = []
    for term in terms:
        app = app_search(term)
        if not app:
            errors.append("search/%s: no app" % term)
            continue
        for r in app_reviews(app["trackId"]):
            if r["rating"] <= 2 and len(r["content"]) >= 10:
                rows.append({"app": app["trackName"], "term": term,
                             "rating": r["rating"], "title": r["title"],
                             "content": r["content"], "date": r["date"]})
    return rows, errors


def main():
    os.makedirs("data", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    charts = fetch_charts()
    hot = {"weibo": fetch_weibo_hot(), "bili": fetch_bili_rank()}
    complaints, errors = collect_complaints()
    payload = {
        "date": today,
        "charts": charts,
        "hot": hot,
        "complaints": complaints,
        "errors": charts.get("errors", []) + errors,
    }
    path = os.path.join("data", "collect-%s.json" % today)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print("date=%s charts=%d/%d weibo=%d bili=%d complaints=%d errors=%d" % (
        today, len(charts["free"]), len(charts["paid"]),
        len([x for x in hot["weibo"] if not x.startswith("[")]),
        len([x for x in hot["bili"] if not x.startswith("[")]),
        len(complaints), len(payload["errors"])))


if __name__ == "__main__":
    main()
