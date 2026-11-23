# -*- coding: utf-8 -*-
"""需求雷达 · 日报生成（GitHub Actions 运行）"""
import json
import os
import urllib.request
from datetime import datetime

API = "https://api.deepseek.com/chat/completions"
MODEL = "deepseek-chat"
UA = {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}


def latest_collect():
    files = sorted((f for f in os.listdir("data") if f.startswith("collect-")), reverse=True)
    if not files:
        raise SystemExit("no collect file")
    with open(os.path.join("data", files[0]), encoding="utf-8") as f:
        return json.load(f)


def read_seed():
    p = os.path.join("data", "complaints.md")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read()
    return ""


def call_model(prompt):
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        return None
    body = json.dumps({
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是资深产品经理，擅长从热榜和用户抱怨里判断真实需求。"},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 4000,
    }).encode("utf-8")
    req = urllib.request.Request(API, data=body, headers={**UA, "Authorization": "Bearer " + key}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            j = json.loads(r.read().decode("utf-8"))
        return j["choices"][0]["message"]["content"]
    except Exception as e:
        print("model call failed:", e)
        return None


def fallback(c):
    lines = ["# 需求日报（规则版）· %s" % c["date"], ""]
    lines.append("> 未配置 DEEPSEEK_API_KEY 或调用失败，本版为规则生成。")
    lines.append("")
    lines.append("## 今日热度 · App Store 免费榜 Top10")
    for i, x in enumerate(c["charts"]["free"][:10], 1):
        lines.append("%d. %s" % (i, x))
    lines.append("")
    lines.append("## 微博热搜 Top10")
    for i, x in enumerate([t for t in c["hot"]["weibo"] if not t.startswith("[")][:10], 1):
        lines.append("%d. %s" % (i, x))
    lines.append("")
    lines.append("## 今日新差评抽样（%d 条）" % len(c["complaints"]))
    for r in c["complaints"][:20]:
        lines.append("- [%s] %s：%s" % (r["date"], r["app"], (r["title"] + " " + r["content"])[:80]))
    return "\n".join(lines)


def main():
    c = latest_collect()
    seed = read_seed()
    free = c["charts"]["free"][:20]
    paid = c["charts"]["paid"][:10]
    weibo = [t for t in c["hot"]["weibo"] if not t.startswith("[")][:20]
    bili = [t for t in c["hot"]["bili"] if not t.startswith("[")][:20]
    complaints = c["complaints"][:60]

    prompt = """你是一名资深产品经理。今天是 {date}。请基于以下材料生成《需求日报》。

【评分标准】每条候选按四个维度各打 0-3 分：证据强度（有原话/价格/日期）、痛点密度（同类抱怨多少）、付费或迁移信号（有人付费/榜位上升/新玩家）、可行动性（一周内能做一个最小交付验证）。再乘「触达系数」：与 20 岁广州大学生、AI 工具、内容创作、可接触的服务行业相关的保留，无关的砍掉。

【App Store 免费榜 Top20】
{free}

【App Store 付费榜 Top10】
{paid}

【微博热搜 Top20】
{weibo}

【B站排行榜 Top20】
{bili}

【最新 App 差评抽样（1-2 星）】
{complaints}

【已有的抱怨库（节选，用于找同类抱怨）】
{seed}

【输出要求】Markdown，结构：
# 需求日报 · {date}
## 一、今日 Top10 主流话题（每条：话题 / 热度位置 / 2 条同类抱怨原话 / 付费证据 / 你可以做的第一个小交付）
## 二、3 条小众观察（看增速和新面孔，不看绝对热度）
## 三、5 条待验证线索（一句话线索 + 验证动作）
## 四、今日判断（3 句话总结今天最值得注意的需求信号）
""".format(date=c["date"], free="\n".join(free), paid="\n".join(paid),
           weibo="\n".join(weibo), bili="\n".join(bili),
           complaints="\n".join("- [%s] %s: %s" % (r["date"], r["app"], (r["title"] + " " + r["content"])[:140]) for r in complaints),
           seed=seed[:3000])

    body = call_model(prompt)
    if not body:
        body = fallback(c)

    os.makedirs("digest", exist_ok=True)
    with open(os.path.join("digest", "%s.md" % c["date"]), "w", encoding="utf-8") as f:
        f.write(body)
    with open(os.path.join("digest", "最新.md"), "w", encoding="utf-8") as f:
        f.write(body)
    print("digest written:", c["date"], "chars:", len(body))


if __name__ == "__main__":
    main()
