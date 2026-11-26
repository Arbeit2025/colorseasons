# -*- coding: utf-8 -*-
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import app as cs

client = cs.app.test_client()
SEASON_KEYS = {"spring", "summer", "autumn", "winter"}


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.get_json()
    assert data["status"] == "ok"
    assert data["questions"] == 8
    assert data["seasons"] == 4


def test_index_ok_and_contains_data():
    r = client.get("/")
    assert r.status_code == 200
    html = r.get_data(as_text=True)
    assert "パーソナルカラー診断" in html
    # 質問データがページに埋め込まれている
    for q in cs.QUESTIONS:
        assert q["q"] in html
    # 4シーズンのベース名がすべて含まれている
    for base in ("イエベ春", "ブルベ夏", "イエベ秋", "ブルベ冬"):
        assert base in html
    for name in ("スプリング", "サマー", "オータム", "ウィンター"):
        assert name in html


def test_script_not_escaped():
    # render_template_string で JS が HTML エスケープされると診断が丸ごと死ぬ（過去の事故）。
    html = client.get("/").get_data(as_text=True)
    assert "&#39;" not in html
    assert "var ORDER = ['spring', 'summer', 'autumn', 'winter'];" in html
    assert "function judge()" in html


def test_questions_integrity():
    assert len(cs.QUESTIONS) == 8
    for q in cs.QUESTIONS:
        assert q["q"].strip()
        assert len(q["choices"]) == 4
        # 各質問の4択は4シーズンにちょうど1つずつ対応する
        assert {c["season"] for c in q["choices"]} == SEASON_KEYS
        assert all(c["label"].strip() for c in q["choices"])


def test_seasons_integrity():
    assert set(cs.SEASONS) == SEASON_KEYS
    expected_base = {
        "spring": "イエベ春",
        "summer": "ブルベ夏",
        "autumn": "イエベ秋",
        "winter": "ブルベ冬",
    }
    hex_re = re.compile(r"^#[0-9A-Fa-f]{6}$")
    for key, season in cs.SEASONS.items():
        assert season["base"] == expected_base[key]
        assert season["desc"].strip()
        assert season["weak"].strip()
        assert len(season["colors"]) == 12
        for color in season["colors"]:
            assert hex_re.match(color["hex"])
            assert color["name"].strip()


def test_tiebreak_order():
    assert cs.ORDER == ["spring", "summer", "autumn", "winter"]
