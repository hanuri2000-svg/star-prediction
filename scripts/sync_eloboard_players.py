from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

OUT = Path("players.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MajhyeodorangPlayerSync/1.0; +https://hanuri2000-svg.github.io/star-prediction/)",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.5",
}
TIMEOUT = 20

SOURCES = [
    ("women_bj", "https://eloboard.com/women/bbs/board.php?bo_table=bj_list&page={page}", 10),
    ("men_bj", "https://eloboard.com/women/bbs/board.php?bo_table=bj_m_list&page={page}", 10),
    ("men_profile", "https://eloboard.com/men/bbs/board.php?bo_table=bj_list&page={page}", 10),
    ("men_recent", "https://eloboard.com/men/bbs/board.php?bo_table=bat&page={page}", 3),
    ("women_recent", "https://eloboard.com/women/bbs/board.php?bo_table=bat&page={page}", 3),
]

# 선수명 뒤에 붙는 P/T/Z 혹은 공백 뒤 P/T/Z를 인식한다.
RACE_RE = re.compile(r"^\s*([가-힣A-Za-z0-9_.·'()\-]{1,30}?)\s*([PTZ])\s*$")


def clean_name(name: str) -> str:
    name = re.sub(r"\s+", " ", name).strip()
    # 페이지 장식/라벨처럼 보이는 값 제거
    if len(name) < 1 or len(name) > 30:
        return ""
    if name.lower() in {"hot", "new", "best", "elo", "wins", "loss"}:
        return ""
    return name


def extract_players(html: str) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[tuple[str, str]] = []

    # 선수 리스트는 주로 a 태그, 전적표는 td/option에 이름+종족이 들어간다.
    for node in soup.select("a, td, option, strong, b"):
        text = node.get_text(" ", strip=True)
        if not text or len(text) > 50:
            continue
        m = RACE_RE.match(text)
        if not m:
            continue
        name = clean_name(m.group(1))
        race = m.group(2)
        if name:
            found.append((name, race))

    return found


def fetch(session: requests.Session, url: str) -> str:
    last_err: Exception | None = None
    for attempt in range(2):
        try:
            r = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            if not r.encoding or r.encoding.lower() == "iso-8859-1":
                r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except Exception as e:
            last_err = e
            if attempt == 0:
                time.sleep(2)
    raise RuntimeError(f"fetch failed: {url}: {last_err}")


def main() -> None:
    session = requests.Session()
    by_name: dict[str, set[str]] = defaultdict(set)
    source_hits: dict[str, int] = defaultdict(int)
    errors: list[str] = []

    for source_name, template, max_pages in SOURCES:
        empty_pages = 0
        for page in range(1, max_pages + 1):
            url = template.format(page=page)
            try:
                html = fetch(session, url)
                rows = extract_players(html)
            except Exception as e:
                errors.append(str(e))
                rows = []

            if not rows:
                empty_pages += 1
            else:
                empty_pages = 0

            for name, race in rows:
                by_name[name].add(race)
                source_hits[source_name] += 1

            # 서버 부담을 줄이기 위해 요청 간 간격을 둔다.
            time.sleep(0.8)
            if empty_pages >= 2:
                break

    conflicts = []
    players = []
    for name in sorted(by_name, key=lambda s: s.casefold()):
        races = sorted(by_name[name])
        if len(races) == 1:
            players.append({"name": name, "race": races[0]})
        else:
            # 동일 이름이 서로 다른 종족으로 잡힌 경우 오자동지정을 막기 위해 제외한다.
            conflicts.append({"name": name, "races": races})

    if len(players) < 30:
        raise RuntimeError(f"Too few players collected: {len(players)}; errors={errors[:3]}")

    payload = {
        "source": "EloBoard",
        "source_url": "https://eloboard.com/",
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "count": len(players),
        "players": players,
        "conflicts": conflicts,
        "sync": {
            "frequency": "daily",
            "request_delay_seconds": 0.8,
            "source_hits": dict(source_hits),
            "errors": errors[:20],
        },
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"synced {len(players)} players, conflicts={len(conflicts)}, errors={len(errors)}")


if __name__ == "__main__":
    main()
