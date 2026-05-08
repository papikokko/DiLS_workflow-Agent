"""
DS業務 AIエージェント ダッシュボード
Claudeとの会話で生成されたファイルを読み込んで表示するだけ。
AIの本体はClaudeとの会話。
"""
import sys
import time
import yaml
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

st.set_page_config(
    page_title="DS業務 AIエージェント ダッシュボード",
    page_icon="🚗",
    layout="wide",
)

# ─── ヘルパー ──────────────────────────────────────────────

def load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

def load_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def load_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def mtime(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%H:%M")
    except Exception:
        return ""

def get_runs() -> list[Path]:
    d = BASE_DIR / "runs"
    return sorted([p for p in d.iterdir() if p.is_dir()], reverse=True) if d.exists() else []

# ─── ステップ定義 ──────────────────────────────────────────

# 画像の業務フローに合わせたステップ定義
# 受付 → 試験計画（DiLS選定含む） → シナリオ作成 → テスト実行 → 報告書
STEPS = [
    {
        "key":   "request",
        "label": "受付",
        "icon":  "📥",
        "desc":  "依頼内容の確認・不足情報の洗い出し",
        "files": ["request.yaml"],          # どれか1つでもあれば ✅
        "primary_file": "request.yaml",
    },
    {
        "key":   "plan",
        "label": "試験計画",
        "icon":  "📋",
        "desc":  "DiLS選定・試験計画書の作成",
        "files": ["plan.md", "dils_selection.md"],
        "primary_file": "plan.md",
    },
    {
        "key":   "scenario",
        "label": "シナリオ作成",
        "icon":  "🗺️",
        "desc":  "走行シナリオ・コンテンツ・アンケート設計",
        "files": ["scenario.md"],
        "primary_file": "scenario.md",
    },
    {
        "key":   "execution",
        "label": "テスト実行",
        "icon":  "🚗",
        "desc":  "実行記録・アンケート・ヒアリング集計",
        "files": ["execution_log.csv", "questionnaire.csv"],
        "primary_file": "questionnaire.csv",
    },
    {
        "key":   "report",
        "label": "報告書",
        "icon":  "📄",
        "desc":  "結果報告書ドラフト作成・提出",
        "files": ["report_draft.md"],
        "primary_file": "report_draft.md",
    },
]

GENERATED_FILES = ["plan.md", "dils_selection.md", "scenario.md",
                   "execution_log.csv", "questionnaire.csv", "report_draft.md"]

def reset_run(run_dir: Path) -> int:
    deleted = 0
    for name in GENERATED_FILES:
        p = run_dir / name
        if p.exists():
            p.unlink()
            deleted += 1
    req = load_yaml(run_dir / "request.yaml")
    rid = req.get("request_id", "")
    if rid:
        out = BASE_DIR / "output" / "reports" / f"{rid}_report_draft.md"
        if out.exists():
            out.unlink()
            deleted += 1
    req_path = run_dir / "request.yaml"
    if req_path.exists():
        data = load_yaml(req_path)
        for q in data.get("open_questions", []):
            if isinstance(q, dict):
                q["resolved"] = False
        if "ai_understanding" in data:
            data["ai_understanding"] = {"summary": "", "recommended_past_tests": [], "recommended_dils": ""}
        data["status"] = "受付済み（確認中）"
        req_path.write_text(yaml.dump(data, allow_unicode=True, default_flow_style=False), encoding="utf-8")
    return deleted

# ─── サイドバー ────────────────────────────────────────────

with st.sidebar:
    st.header("📁 案件")

    runs = get_runs()
    if not runs:
        st.warning("案件がありません。\nClaudeに依頼を出してください。")
        st.stop()

    def run_label(run_dir: Path) -> str:
        req = load_yaml(run_dir / "request.yaml")
        status = req.get("status", "")
        badge = "✅ " if status == "完了" else "🔵 " if status in ("実施中", "計画中") else "🟡 "
        return badge + run_dir.name

    run_labels = [run_label(r) for r in runs]
    selected_label = st.radio("選択", run_labels, label_visibility="collapsed")
    selected_name = runs[run_labels.index(selected_label)].name
    selected_run = BASE_DIR / "runs" / selected_name

    st.divider()
    if st.button("🔄 手動更新", use_container_width=True):
        st.rerun()
    # 監視状態はメインエリアで制御（ここはステータス表示のみ）
    st.session_state.setdefault("watch_placeholder", None)

    st.divider()
    st.markdown("**📂 参照データ**")
    REF = {
        "DiLSマスタ":    BASE_DIR / "data" / "03_reference" / "dils_master.csv",
        "過去テスト一覧": BASE_DIR / "data" / "03_reference" / "past_tests.csv",
        "チェックリスト": BASE_DIR / "data" / "03_reference" / "checklist.csv",
    }
    for label, path in REF.items():
        if path.exists():
            with st.expander(f"📄 {label}"):
                df = load_csv(path)
                if not df.empty:
                    st.dataframe(df, use_container_width=True, height=200)
                st.download_button(
                    f"⬇ {path.name}",
                    data=path.read_bytes(),
                    file_name=path.name,
                    mime="text/csv",
                    key=f"sidebar_{label}",
                )

    st.divider()
    st.markdown("**🎬 デモ操作**")
    if "reset_confirm" not in st.session_state:
        st.session_state.reset_confirm = False

    if not st.session_state.reset_confirm:
        if st.button("🔁 デモをリセット", use_container_width=True):
            st.session_state.reset_confirm = True
            st.rerun()
    else:
        st.warning(f"生成ファイルを削除して\n初期状態に戻します")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("実行", type="primary", use_container_width=True):
                n = reset_run(selected_run)
                st.session_state.reset_confirm = False
                st.success(f"{n}件削除")
                st.rerun()
        with c2:
            if st.button("キャンセル", use_container_width=True):
                st.session_state.reset_confirm = False
                st.rerun()

# ─── 案件ヘッダー ──────────────────────────────────────────

request = load_yaml(selected_run / "request.yaml")
def step_done(step: dict, run_dir: Path) -> bool:
    return any((run_dir / f).exists() for f in step["files"])

def step_mtime(step: dict, run_dir: Path) -> str:
    times = [mtime(run_dir / f) for f in step["files"] if (run_dir / f).exists()]
    return times[0] if times else ""

steps_status = [(s, step_done(s, selected_run), step_mtime(s, selected_run)) for s in STEPS]
done_count = sum(1 for _, done, _ in steps_status if done)

col_title, col_badge = st.columns([4, 1])
with col_title:
    st.markdown(f"## {request.get('request_id', '')}　{request.get('request_title', selected_name)}")
    st.caption(request.get("purpose", ""))
with col_badge:
    status = request.get("status", "")
    color = {"受付済み（確認中）": "🟡", "計画中": "🔵", "実施中": "🔵", "完了": "🟢"}.get(status, "⚪")
    st.markdown(f"<br>**{color} {status}**", unsafe_allow_html=True)

# ─── 進捗ステッパー ────────────────────────────────────────

st.progress(done_count / len(STEPS))

chips_html = '<div style="display:flex;gap:6px;margin:8px 0 4px;">'
for i, (step, done, t) in enumerate(steps_status):
    if i > 0:
        chips_html += '<div style="display:flex;align-items:center;color:#bbb;font-size:18px;padding:0 2px;">▶</div>'
    bg     = "#d4edda" if done else "#f0f0f0"
    border = "2px solid #28a745" if done else "2px solid #ddd"
    opacity = "1" if done else "0.55"
    status_line = f'<div style="font-size:11px;color:#28a745;font-weight:bold">✅ {t}</div>' if done else '<div style="font-size:11px;color:#aaa">⬜ 未生成</div>'
    chips_html += f"""
    <div style="flex:1;background:{bg};border:{border};border-radius:10px;
                padding:10px 6px;text-align:center;opacity:{opacity};">
      <div style="font-size:22px;line-height:1.2">{step['icon']}</div>
      <div style="font-size:12px;font-weight:bold;margin:3px 0">{step['label']}</div>
      <div style="font-size:10px;color:#666;margin-bottom:3px">{step['desc']}</div>
      {status_line}
    </div>"""
chips_html += '</div>'
st.markdown(chips_html, unsafe_allow_html=True)

st.markdown(f"<p style='color:#666;font-size:13px;margin:4px 0 16px'>{done_count} / {len(STEPS)} ステップ完了</p>", unsafe_allow_html=True)
st.divider()

# ─── ドリルダウン：各ステップの詳細 ────────────────────────

REF_DIR = BASE_DIR / "data" / "03_reference"

def ref_panel(refs: list, key_prefix: str) -> None:
    """参照データをその場で表示＋ダウンロード"""
    existing = [(lbl, p) for lbl, p in refs if p.exists()]
    if not existing:
        return
    st.markdown("---")
    st.markdown("##### 📎 参照したデータ")
    for lbl, path in existing:
        with st.expander(f"🗂️ {lbl}　`{path.relative_to(BASE_DIR)}`"):
            if path.suffix == ".csv":
                df = load_csv(path)
                if not df.empty:
                    st.dataframe(df, use_container_width=True, height=200)
            elif path.suffix in (".yaml", ".yml"):
                st.code(path.read_text(encoding="utf-8"), language="yaml")
            else:
                st.markdown(load_md(path))
            st.download_button(f"⬇ {path.name}",
                               data=path.read_bytes(), file_name=path.name,
                               mime="text/plain", key=f"{key_prefix}_{path.stem}")

def dl_row(paths: list, key_prefix: str) -> None:
    """成果物ダウンロードボタンを横並びで表示"""
    existing = [p for p in paths if p.exists()]
    if not existing:
        return
    st.markdown("##### ⬇ 成果物ダウンロード")
    cols = st.columns(len(existing))
    for col, p in zip(cols, existing):
        col.download_button(f"⬇ {p.name}", data=p.read_bytes(),
                            file_name=p.name, mime="text/plain",
                            key=f"{key_prefix}_{p.stem}")

last_done_idx = max((i for i, (_, done, _) in enumerate(steps_status) if done), default=0)

for i, (step, done, t) in enumerate(steps_status):

    if not done:
        st.markdown(
            f'<div style="padding:12px 16px;background:#f8f8f8;border-radius:8px;'
            f'color:#aaa;margin-bottom:8px;">'
            f'{step["icon"]} <b>{step["label"]}</b> — Claudeとの会話で生成されます</div>',
            unsafe_allow_html=True,
        )
        continue

    with st.expander(f'{step["icon"]} **{step["label"]}** ✅　{t}', expanded=(i == last_done_idx)):

        # ── 受付 ──────────────────────────────────────────
        if step["key"] == "request":
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("#### 依頼内容")
                for label, key in [("依頼ID", "request_id"), ("依頼名", "request_title"),
                                    ("目的", "purpose"), ("対象機能", "target_function")]:
                    val = request.get(key, "")
                    if val:
                        st.markdown(f"**{label}：** {val}")
                rd = request.get("required_data", [])
                if rd:
                    st.markdown("**取得データ：** " + " / ".join(rd))
                sc = request.get("preferred_scenario", [])
                if sc:
                    st.markdown("**シナリオ：** " + " / ".join(sc))
            with c2:
                oq = request.get("open_questions", [])
                if oq:
                    all_resolved = all(q.get("resolved", False) for q in oq if isinstance(q, dict))
                    st.markdown(f"#### {'✅ 不足情報（解決済み）' if all_resolved else '⚠️ 不足情報（確認中）'}")
                    for q in oq:
                        if isinstance(q, dict):
                            icon = "✅" if q.get("resolved") else "⚠️"
                            st.markdown(f"{icon} **{q.get('item','')}**：{q.get('detail','')}")
                ai = request.get("ai_understanding", {})
                summary = ai.get("summary", "") if isinstance(ai, dict) else ""
                if summary:
                    st.markdown("#### 🤖 Claudeの理解")
                    st.info(summary)
            ref_panel([
                ("受付サンプル（依頼フォーム）", BASE_DIR / "data" / "04_sample" / "sample_request.yaml"),
            ], key_prefix="req")
            dl_row([selected_run / "request.yaml"], key_prefix="req")

        # ── 試験計画（DiLS選定含む） ───────────────────────
        elif step["key"] == "plan":
            plan_path = selected_run / "plan.md"
            dils_path = selected_run / "dils_selection.md"
            if plan_path.exists():
                st.markdown(load_md(plan_path))
            if dils_path.exists():
                with st.expander("🏭 DiLS選定・類似テスト検索結果"):
                    st.markdown(load_md(dils_path))
            ref_panel([
                ("DiLSマスタ（設備・稼働状況）",       REF_DIR / "dils_master.csv"),
                ("過去テスト一覧（類似テスト検索元）",  REF_DIR / "past_tests.csv"),
            ], key_prefix="plan")
            dl_row([plan_path, dils_path], key_prefix="plan")

        # ── シナリオ作成 ───────────────────────────────────
        elif step["key"] == "scenario":
            st.markdown(load_md(selected_run / "scenario.md"))
            ref_panel([
                ("過去テスト一覧（シナリオ流用元）", REF_DIR / "past_tests.csv"),
                ("DS検証チェックリスト",             REF_DIR / "checklist.csv"),
            ], key_prefix="scen")
            dl_row([selected_run / "scenario.md"], key_prefix="scen")

        # ── テスト実行 ─────────────────────────────────────
        elif step["key"] == "execution":
            q_path  = selected_run / "questionnaire.csv"
            ex_path = selected_run / "execution_log.csv"
            # 既知アンケート列名→表示ラベルのマッピング（案件ごとに異なる列名に対応）
            q_labels = {
                "q1_notice_ease":            "Q1 気づきやすさ",
                "q2_content_clarity":        "Q2 内容理解",
                "q3_timing_appropriateness": "Q3 タイミング",
                "q4_stress_level":           "Q4 ストレスの低さ",
                "q5_overall_satisfaction":   "Q5 総合満足度",
                "q1_safety":                 "Q1 安心感",
                "q2_naturalness":            "Q2 動作の自然さ",
                "q3_trust":                  "Q3 信頼感",
                "q4_discomfort":             "Q4 違和感",
                "q5_adoption":               "Q5 採用意向",
            }
            if q_path.exists():
                q_df = load_csv(q_path)
                if not q_df.empty:
                    valid_scores = [c for c in q_labels if c in q_df.columns]
                    scenarios = q_df["scenario"].unique().tolist() if "scenario" in q_df.columns else []
                    ca, cb = st.columns(2)
                    with ca:
                        st.markdown("**アンケート集計（シナリオ別平均）**")
                        if valid_scores and scenarios:
                            rows = []
                            for c in valid_scores:
                                row = {"設問": q_labels[c]}
                                for sc in scenarios:
                                    sc_df = q_df[q_df["scenario"] == sc]
                                    row[sc] = round(sc_df[c].mean(), 1) if not sc_df.empty else "-"
                                rows.append(row)
                            st.dataframe(pd.DataFrame(rows).set_index("設問"), use_container_width=True)
                        else:
                            st.dataframe(q_df, use_container_width=True)
                    with cb:
                        if valid_scores and scenarios and "participant_id" in q_df.columns:
                            sc0 = scenarios[0]
                            sc0_df = q_df[q_df["scenario"] == sc0]
                            st.markdown(f"**被験者別スコア（{sc0}）**")
                            chart = sc0_df.groupby("participant_id")[valid_scores[:2]].mean()
                            chart.columns = [q_labels[c] for c in chart.columns]
                            st.bar_chart(chart)
                    if "free_comment" in q_df.columns:
                        with st.expander("💬 自由記述・ヒアリング"):
                            fcols = [c for c in ["participant_id","scenario","free_comment"] if c in q_df.columns]
                            st.dataframe(q_df[q_df["free_comment"].notna()][fcols], use_container_width=True)
            if ex_path.exists():
                with st.expander("📋 実行ログ（環境記録・データ）"):
                    st.dataframe(load_csv(ex_path).head(15), use_container_width=True)
            ref_panel([
                ("アンケートサンプル（設問フォーマット）", BASE_DIR / "data" / "04_sample" / "sample_questionnaire.csv"),
            ], key_prefix="exec")
            dl_row([q_path, ex_path], key_prefix="exec")

        # ── 報告書 ─────────────────────────────────────────
        elif step["key"] == "report":
            st.markdown(load_md(selected_run / "report_draft.md"))
            out = BASE_DIR / "output" / "reports" / f"{request.get('request_id','')}_report_draft.md"
            if out.exists():
                st.success(f"✅ output保存済み：`{out.relative_to(BASE_DIR)}`")
            ref_panel([
                ("アンケート結果（集計元）",   selected_run / "questionnaire.csv"),
                ("DiLSマスタ（設備情報）",     REF_DIR / "dils_master.csv"),
                ("過去テスト一覧（比較元）",    REF_DIR / "past_tests.csv"),
            ], key_prefix="rep")
            dl_row([selected_run / "report_draft.md", out], key_prefix="rep")

# ─── ファイル変更検知・自動更新 ──────────────────────────────
# 常時ポーリング（完了後も含む）。完了後は間隔を3秒に落とす。

def run_fingerprint(run_dir: Path) -> str:
    files = sorted(run_dir.glob("*.*"))
    return "|".join(f"{f.name}:{f.stat().st_mtime:.1f}" for f in files if f.is_file())

all_done = done_count == len(STEPS) and request.get("status") == "完了"

current = run_fingerprint(selected_run)
prev = st.session_state.get("fingerprint", "")
st.session_state.fingerprint = current

if current != prev and prev != "":
    st.rerun()
else:
    time.sleep(3.0 if all_done else 1.5)
    st.rerun()
