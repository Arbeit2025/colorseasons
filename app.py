# colorseasons - パーソナルカラー診断
# 8つの質問に答えると、似合う色のグループ（春・夏・秋・冬の4シーズン）を
# 診断する単一ファイルFlaskアプリ。診断ロジックはすべてページ内の
# JavaScriptで動き、サーバーはページと /healthz を返すだけ。
import json

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

# 同点のときの優先順位（この順で最初に最大値になったシーズンを採用する）
ORDER = ["spring", "summer", "autumn", "winter"]

QUESTIONS = [
    {"q": "肌の色味は、どちらに近いですか？",
     "choices": [
         {"label": "黄みがかった、温かみのある肌色", "season": "spring"},
         {"label": "ピンクみのある、涼しげな肌色", "season": "summer"},
         {"label": "黄みが強く、マットで落ち着いた肌色", "season": "autumn"},
         {"label": "ピンクみが強く、透けるような肌色", "season": "winter"},
     ]},
    {"q": "日焼けすると、どうなりますか？",
     "choices": [
         {"label": "赤くなって、なかなか焼けない", "season": "summer"},
         {"label": "小麦色に焼けて、秋には元に戻る", "season": "spring"},
         {"label": "赤くなり、焼けてもすぐ白く戻る", "season": "winter"},
         {"label": "しっかり茶色く焼けて、定着しやすい", "season": "autumn"},
     ]},
    {"q": "瞳の色は、どちらに近いですか？",
     "choices": [
         {"label": "深いダークブラウン", "season": "autumn"},
         {"label": "明るい茶色・琥珀色", "season": "spring"},
         {"label": "黒に近く、つやがある", "season": "winter"},
         {"label": "柔らかいこげ茶・グレーっぽい茶色", "season": "summer"},
     ]},
    {"q": "地毛の色は、どちらに近いですか？",
     "choices": [
         {"label": "つやのある黒髪", "season": "winter"},
         {"label": "明るめの茶色・栗色", "season": "spring"},
         {"label": "柔らかいダークブラウン・グレージュ", "season": "summer"},
         {"label": "深みのあるダークブラウン", "season": "autumn"},
     ]},
    {"q": "手のひらの色は、どちらに近いですか？",
     "choices": [
         {"label": "黄みのあるピーチ色", "season": "spring"},
         {"label": "黄みが強く、落ち着いた色", "season": "autumn"},
         {"label": "ピンクみのある薄い色", "season": "summer"},
         {"label": "ピンクみが強く、青白い色", "season": "winter"},
     ]},
    {"q": "似合うと感じるアクセサリーは？",
     "choices": [
         {"label": "柔らかなシルバー・パール", "season": "summer"},
         {"label": "マットなゴールド・べっ甲", "season": "autumn"},
         {"label": "つやのある明るいゴールド", "season": "spring"},
         {"label": "シャープなシルバー・プラチナ", "season": "winter"},
     ]},
    {"q": "白目と黒目のコントラスト（境目の強さ）は？",
     "choices": [
         {"label": "はっきり強く、シャープな印象", "season": "winter"},
         {"label": "柔らかく、優しい印象", "season": "summer"},
         {"label": "キラキラと明るい印象", "season": "spring"},
         {"label": "深く、落ち着いた印象", "season": "autumn"},
     ]},
    {"q": "似合うと感じるリップの色は？",
     "choices": [
         {"label": "テラコッタ・深みのあるレッド", "season": "autumn"},
         {"label": "フューシャ・鮮やかなレッド", "season": "winter"},
         {"label": "コーラルピンク・オレンジ系", "season": "spring"},
         {"label": "ローズピンク・青みピンク", "season": "summer"},
     ]},
]

SEASONS = {
    "spring": {
        "name": "スプリング",
        "base": "イエベ春",
        "desc": "明るく温かみのある色が似合うタイプ。黄みのある鮮やかな色で、肌がいきいきと元気に見えます。軽やかでクリアな色を選ぶと、持ち前の華やかさが引き立ちます。",
        "colors": [
            {"hex": "#FFF6E9", "name": "アイボリー"},
            {"hex": "#FFB59E", "name": "ピーチ"},
            {"hex": "#FF7E67", "name": "コーラルピンク"},
            {"hex": "#FF6F61", "name": "コーラルレッド"},
            {"hex": "#FFA552", "name": "アプリコット"},
            {"hex": "#FFD93D", "name": "イエロー"},
            {"hex": "#A9CE4F", "name": "イエローグリーン"},
            {"hex": "#7FDBC0", "name": "ミントグリーン"},
            {"hex": "#3FBFB2", "name": "ターコイズ"},
            {"hex": "#6EC6E8", "name": "アクアブルー"},
            {"hex": "#D9A066", "name": "ライトキャメル"},
            {"hex": "#E8C39E", "name": "ウォームベージュ"},
        ],
        "weak": "くすんだ色や暗い色は、顔色が沈んで見えがちです。青みの強い寒色や、黒・グレーなどの重い色も苦手な傾向があります。",
    },
    "summer": {
        "name": "サマー",
        "base": "ブルベ夏",
        "desc": "涼しげで柔らかな色が似合うタイプ。青みのある淡い色で、肌に透明感が出て上品な印象になります。ソフトで優しい色合いが、エレガントさを引き立てます。",
        "colors": [
            {"hex": "#F7F5F0", "name": "オフホワイト"},
            {"hex": "#F4C6D4", "name": "パウダーピンク"},
            {"hex": "#E79FB2", "name": "ローズピンク"},
            {"hex": "#C8A2C8", "name": "ライラック"},
            {"hex": "#C5B3E0", "name": "ラベンダー"},
            {"hex": "#A8C8E8", "name": "スカイブルー"},
            {"hex": "#BCD4EA", "name": "パウダーブルー"},
            {"hex": "#BFE3D0", "name": "ミント"},
            {"hex": "#CFCFCF", "name": "ソフトグレー"},
            {"hex": "#93A5BB", "name": "ブルーグレー"},
            {"hex": "#54678F", "name": "ソフトネイビー"},
            {"hex": "#8E6A92", "name": "プラム"},
        ],
        "weak": "黄みの強い色や、濃く鮮やかすぎる色は浮いて見えがちです。オレンジやマスタードなどの、こってりした暖色も苦手な傾向があります。",
    },
    "autumn": {
        "name": "オータム",
        "base": "イエベ秋",
        "desc": "深く豊かな色が似合うタイプ。黄みのある、こっくりした色で、肌が落ち着いてゴージャスな印象になります。アースカラーや深みのある色が、大人っぽさを引き立てます。",
        "colors": [
            {"hex": "#F3E5CF", "name": "クリーム"},
            {"hex": "#B98A44", "name": "キャメル"},
            {"hex": "#C1613F", "name": "テラコッタ"},
            {"hex": "#B5523C", "name": "ブリックレッド"},
            {"hex": "#DFA320", "name": "マスタード"},
            {"hex": "#C9A227", "name": "ゴールド"},
            {"hex": "#6B7043", "name": "オリーブグリーン"},
            {"hex": "#94865A", "name": "カーキ"},
            {"hex": "#556B2F", "name": "モスグリーン"},
            {"hex": "#175E54", "name": "ディープティール"},
            {"hex": "#722F37", "name": "ワインレッド"},
            {"hex": "#5C4033", "name": "ダークブラウン"},
        ],
        "weak": "青みの強いパステルカラーや、鮮やかすぎる原色は浮いて見えがちです。薄く淡い色だけだと、物足りなく見えることもあります。",
    },
    "winter": {
        "name": "ウィンター",
        "base": "ブルベ冬",
        "desc": "鮮やかでシャープな色が似合うタイプ。青みのある、はっきりした色で、肌が際立って凛とした印象になります。モノトーンやビビッドカラーが、華やかさを引き立てます。",
        "colors": [
            {"hex": "#FFFFFF", "name": "ピュアホワイト"},
            {"hex": "#1A1A1A", "name": "ブラック"},
            {"hex": "#454545", "name": "チャコールグレー"},
            {"hex": "#CFE8F5", "name": "アイスブルー"},
            {"hex": "#4169E1", "name": "ロイヤルブルー"},
            {"hex": "#202A5E", "name": "ネイビー"},
            {"hex": "#CE2029", "name": "トゥルーレッド"},
            {"hex": "#E4007C", "name": "ショッキングピンク"},
            {"hex": "#C0267C", "name": "フューシャ"},
            {"hex": "#800020", "name": "バーガンディ"},
            {"hex": "#5E2B97", "name": "パープル"},
            {"hex": "#0E8A67", "name": "エメラルドグリーン"},
        ],
        "weak": "黄みの強い色や、くすんだ中間色は顔色がくすんで見えがちです。ベージュやカーキなどの、濁った暖色も苦手な傾向があります。",
    },
}

CSS = """
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: linear-gradient(135deg, #ffe9e4 0%, #fdf6d8 28%, #e2f2e4 52%, #ddebfb 76%, #e6def5 100%);
  background-attachment: fixed;
  color: #3a3340;
  font-family: "Hiragino Kaku Gothic ProN", "Hiragino Sans", "Yu Gothic", "YuGothic", sans-serif;
  line-height: 1.8; min-height: 100vh;
}
header { text-align: center; padding: 2.4rem 1rem 0.2rem; }
header h1 { font-size: 1.7rem; letter-spacing: 0.18em; margin: 0; font-weight: 700; }
header p { color: #6d6474; font-size: 0.88rem; letter-spacing: 0.08em; margin: 0.35rem 0 0; }
main { max-width: 640px; margin: 0 auto; padding: 1.2rem 1rem 3rem; }
.card {
  background: rgba(255, 255, 255, 0.94); border-radius: 18px;
  box-shadow: 0 10px 32px rgba(90, 70, 110, 0.14);
  padding: 1.9rem 1.5rem 1.7rem; margin-top: 1.2rem;
}
.lead { text-align: center; font-size: 0.98rem; }
.season-dots { text-align: center; font-size: 1.5rem; letter-spacing: 0.5em; margin: 0.6rem 0 1rem; }
.progress-wrap { margin-bottom: 1.1rem; }
.progress-label { font-size: 0.82rem; color: #8a8093; text-align: right; letter-spacing: 0.1em; }
.progress-bar { height: 8px; background: #eee7f2; border-radius: 999px; overflow: hidden; }
.progress-fill { height: 100%; background: linear-gradient(90deg, #f6a8b8, #f7cf5f, #8fce9b, #7aa7e8); border-radius: 999px; transition: width 0.3s ease; }
.question { font-size: 1.15rem; font-weight: 700; margin: 0.4rem 0 1.1rem; }
.choices { display: grid; gap: 0.65rem; }
.choice {
  font-family: inherit; text-align: left; background: #fbf8fc; color: #3a3340;
  border: 1.5px solid #ddd2e6; border-radius: 12px; padding: 0.8rem 1rem;
  font-size: 0.98rem; cursor: pointer; width: 100%;
}
.choice:hover { border-color: #b494d8; background: #f4ecfb; }
.btn {
  font-family: inherit; display: inline-block; background: #574b66; color: #fff; border: none;
  border-radius: 999px; padding: 0.75rem 2.1rem; font-size: 1rem; letter-spacing: 0.1em;
  cursor: pointer; text-decoration: none;
}
.btn:hover { background: #6f6084; }
.center { text-align: center; }
.result-season { text-align: center; margin-bottom: 0.4rem; }
.result-season .en { color: #9a8cae; letter-spacing: 0.35em; font-size: 0.8rem; text-transform: uppercase; }
.result-season .big { font-size: 2rem; font-weight: 700; letter-spacing: 0.08em; margin: 0.2rem 0; }
.result-desc { font-size: 0.97rem; }
h2.sub { font-size: 1rem; letter-spacing: 0.12em; border-bottom: 2px solid #e7ddf0; padding-bottom: 0.3rem; margin: 1.5rem 0 0.8rem; }
.palette { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.55rem; }
.swatch { border-radius: 10px; overflow: hidden; border: 1px solid #e2d9ea; }
.swatch .chip { height: 44px; }
.swatch .cname { font-size: 0.68rem; text-align: center; padding: 0.22rem 0.1rem; background: #fff; line-height: 1.35; }
.weak { font-size: 0.94rem; }
.score-row { display: flex; align-items: center; gap: 0.6rem; font-size: 0.85rem; margin: 0.3rem 0; }
.score-row .sname { width: 5.2em; color: #6d6474; }
.score-track { flex: 1; height: 9px; background: #eee7f2; border-radius: 999px; overflow: hidden; }
.score-fill { height: 100%; border-radius: 999px; }
footer { text-align: center; color: #8a8093; font-size: 0.78rem; padding: 0 1rem 2rem; }
@media (max-width: 480px) {
  .palette { grid-template-columns: repeat(3, 1fr); }
  header h1 { font-size: 1.4rem; }
  .result-season .big { font-size: 1.65rem; }
}
"""

SCRIPT_BODY = """
var state = { idx: 0, scores: { spring: 0, summer: 0, autumn: 0, winter: 0 } };

function show(id) {
  var ids = ['start-screen', 'quiz-screen', 'result-screen'];
  for (var i = 0; i < ids.length; i++) {
    document.getElementById(ids[i]).style.display = (ids[i] === id) ? 'block' : 'none';
  }
}

function startQuiz() {
  state.idx = 0;
  state.scores = { spring: 0, summer: 0, autumn: 0, winter: 0 };
  show('quiz-screen');
  renderQuestion();
}

function renderQuestion() {
  var q = DATA.questions[state.idx];
  document.getElementById('progress-label').textContent = 'Q' + (state.idx + 1) + ' / ' + DATA.questions.length;
  document.getElementById('progress-fill').style.width = ((state.idx) / DATA.questions.length * 100) + '%';
  document.getElementById('question-text').textContent = q.q;
  var box = document.getElementById('choices');
  box.innerHTML = '';
  for (var i = 0; i < q.choices.length; i++) {
    (function (choice) {
      var btn = document.createElement('button');
      btn.className = 'choice';
      btn.textContent = choice.label;
      btn.onclick = function () { answer(choice.season); };
      box.appendChild(btn);
    })(q.choices[i]);
  }
}

function answer(season) {
  state.scores[season] += 1;
  state.idx += 1;
  if (state.idx < DATA.questions.length) {
    renderQuestion();
  } else {
    document.getElementById('progress-fill').style.width = '100%';
    showResult();
  }
}

function judge() {
  var best = ORDER[0];
  for (var i = 1; i < ORDER.length; i++) {
    if (state.scores[ORDER[i]] > state.scores[best]) {
      best = ORDER[i];
    }
  }
  return best;
}

function showResult() {
  var key = judge();
  var s = DATA.seasons[key];
  document.getElementById('result-en').textContent = key;
  document.getElementById('result-big').textContent = s.base + '（' + s.name + '）';
  document.getElementById('result-desc').textContent = s.desc;
  document.getElementById('result-weak').textContent = s.weak;
  var pal = document.getElementById('palette');
  pal.innerHTML = '';
  for (var i = 0; i < s.colors.length; i++) {
    var wrap = document.createElement('div');
    wrap.className = 'swatch';
    var chip = document.createElement('div');
    chip.className = 'chip';
    chip.style.background = s.colors[i].hex;
    var nm = document.createElement('div');
    nm.className = 'cname';
    nm.textContent = s.colors[i].name;
    wrap.appendChild(chip);
    wrap.appendChild(nm);
    pal.appendChild(wrap);
  }
  var sc = document.getElementById('scores');
  sc.innerHTML = '';
  var barColors = { spring: '#f2a65a', summer: '#7aa7e8', autumn: '#a9713f', winter: '#5e6fb8' };
  for (var j = 0; j < ORDER.length; j++) {
    var k = ORDER[j];
    var row = document.createElement('div');
    row.className = 'score-row';
    var label = document.createElement('span');
    label.className = 'sname';
    label.textContent = DATA.seasons[k].base;
    var track = document.createElement('div');
    track.className = 'score-track';
    var fill = document.createElement('div');
    fill.className = 'score-fill';
    fill.style.width = (state.scores[k] / DATA.questions.length * 100) + '%';
    fill.style.background = barColors[k];
    track.appendChild(fill);
    var num = document.createElement('span');
    num.textContent = state.scores[k] + '点';
    row.appendChild(label);
    row.appendChild(track);
    row.appendChild(num);
    sc.appendChild(row);
  }
  show('result-screen');
}

function restart() {
  show('start-screen');
}
"""

DATA = {"questions": QUESTIONS, "seasons": SEASONS, "order": ORDER}
SCRIPT = "var DATA = " + json.dumps(DATA, ensure_ascii=False) + ";\n" + "var ORDER = ['spring', 'summer', 'autumn', 'winter'];" + SCRIPT_BODY

BASE = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>パーソナルカラー診断 | colorseasons</title>
<style>{{ css|safe }}</style>
</head>
<body>
<header>
<h1>パーソナルカラー診断</h1>
<p>colorseasons ― 8つの質問で、あなたに似合う色の季節がわかります</p>
</header>
<main>
  <section class="card" id="start-screen">
    <div class="season-dots"><span style="color:#f2a65a">●</span><span style="color:#7aa7e8">●</span><span style="color:#a9713f">●</span><span style="color:#5e6fb8">●</span></div>
    <p class="lead">肌や瞳の色など、あなたの特徴についての8つの質問に答えるだけ。<br>
    春（スプリング）・夏（サマー）・秋（オータム）・冬（ウィンター）の4タイプから、似合う色のグループを診断します。</p>
    <p class="center" style="margin-top:1.4rem"><button class="btn" onclick="startQuiz()">診断をはじめる</button></p>
  </section>

  <section class="card" id="quiz-screen" style="display:none">
    <div class="progress-wrap">
      <div class="progress-label" id="progress-label">Q1 / 8</div>
      <div class="progress-bar"><div class="progress-fill" id="progress-fill" style="width:0%"></div></div>
    </div>
    <p class="question" id="question-text"></p>
    <div class="choices" id="choices"></div>
  </section>

  <section class="card" id="result-screen" style="display:none">
    <div class="result-season">
      <div class="en" id="result-en"></div>
      <div class="big" id="result-big"></div>
    </div>
    <p class="result-desc" id="result-desc"></p>
    <h2 class="sub">あなたに似合う色</h2>
    <div class="palette" id="palette"></div>
    <h2 class="sub">苦手な色の傾向</h2>
    <p class="weak" id="result-weak"></p>
    <h2 class="sub">タイプ別のスコア</h2>
    <div id="scores"></div>
    <p class="center" style="margin-top:1.6rem"><button class="btn" onclick="restart()">もう一度診断する</button></p>
  </section>
</main>
<footer>この診断は目安です。回答はブラウザの中だけで処理され、サーバーには送信されません。</footer>
<script>{{ script|safe }}</script>
</body>
</html>
"""


def render_page():
    return render_template_string(BASE, css=CSS, script=SCRIPT)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok", "questions": len(QUESTIONS), "seasons": len(SEASONS)})


@app.route("/")
def index():
    return render_page()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
