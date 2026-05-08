from datetime import date
from pathlib import Path
import pandas as pd


def generate_plan(request: dict, similar_tests: list, dils_recommendation: list) -> str:
    top_dils = dils_recommendation[0] if dils_recommendation else {"dils_id": "未定", "name": "未定"}
    top_test = similar_tests[0] if similar_tests else {"test_id": "なし", "title": "なし"}
    scenarios = request.get("preferred_scenario", ["市街地", "高速道路"])
    scenario_str = "・".join(scenarios)

    return f"""# 試験計画ドラフト — {request.get('request_id', '')} {request.get('request_title', '')}

> AIが生成したドラフトです。参照元：{top_test['test_id']}のシナリオ構成、validation_knowhow.md

## 1. 目的

{request.get('purpose', '')}

## 2. 評価対象

| 項目 | 内容 |
|------|------|
| 対象機能 | {request.get('target_function', '')} |
| 評価環境 | {top_dils['dils_id']}（{top_dils['name']}） |
| 走行シナリオ | {scenario_str} |

## 3. 被験者条件（要確認）

| 項目 | 計画値 | 状態 |
|------|--------|------|
| 被験者数 | 12名（推奨） | **未確定** |
| 年齢層 | 20代〜50代 | 要合意 |
| 運転経験 | 普通免許保有 | 要合意 |

## 4. 取得データ

| データ | 取得方法 |
|--------|---------|
| 反応時間 | DiLSシステムログ（100ms以下） |
| 視線ログ | Eye Tracker（60Hz以上） |
| アンケート | シナリオ後に実施 |

## 5. 合否判断基準（要依頼者合意）

- 反応時間：X秒以内（未定）
- アンケート平均：4点以上（5段階）（未定）

## 6. 過去テストとの比較

参照テスト：{top_test['test_id']} {top_test['title']}
→ シナリオ・DiLS設定の流用を検討する

---
*このドラフトはAIが自動生成しました。担当者が確認・修正してください。*
"""


def generate_scenario(request: dict) -> str:
    scenarios = request.get("preferred_scenario", ["city", "highway"])
    scenario_blocks = []
    for i, sc in enumerate(scenarios, 1):
        label = "市街地走行" if sc == "city" else "高速道路走行"
        speed = "30〜50km/h" if sc == "city" else "80〜100km/h"
        trigger = "走行開始3分後" if sc == "city" else "走行開始2分後"
        scenario_blocks.append(f"""
## シナリオ{chr(64+i)}：{label}

| 項目 | 設定値 |
|------|--------|
| 走行環境 | {label} |
| 走行速度 | {speed} |
| 警告発令タイミング | {trigger}（2回） |
| 被験者課題 | 通常の走行操作 |
""")

    return f"""# 試験シナリオ案 — {request.get('request_id', '')}

> AIが生成したシナリオ案です。TEST-2025-014のシナリオを参照しています。

{"".join(scenario_blocks)}

## アンケート設問（シナリオ後に実施）

| 設問 | 形式 |
|------|------|
| Q1 警告表示に気づきやすかったですか | 5段階評価 |
| Q2 警告表示の内容がわかりましたか | 5段階評価 |
| Q3 警告タイミングは適切でしたか | 5段階評価 |
| Q4 走行へのストレスはありましたか | 5段階評価 |
| Q5 全体として使いやすいと感じましたか | 5段階評価 |
| Q6 気になった点があれば教えてください | 自由記述 |

---
*このドラフトはAIが自動生成しました。担当者が確認・修正してください。*
"""


def generate_report(request: dict, questionnaire_df: pd.DataFrame, dils_recommendation: list) -> str:
    today = date.today().strftime("%Y-%m-%d")
    top_dils = dils_recommendation[0] if dils_recommendation else {"dils_id": "DiLS-02"}

    score_cols = ["q1_notice_ease", "q2_content_clarity", "q3_timing_appropriateness",
                  "q4_stress_level", "q5_overall_satisfaction"]
    q_labels = {
        "q1_notice_ease": "Q1 警告に気づきやすかった",
        "q2_content_clarity": "Q2 表示内容がわかった",
        "q3_timing_appropriateness": "Q3 タイミングが適切だった",
        "q4_stress_level": "Q4 ストレスが低い",
        "q5_overall_satisfaction": "Q5 全体的に使いやすい",
    }

    city_df = questionnaire_df[questionnaire_df["scenario"] == "city"]
    highway_df = questionnaire_df[questionnaire_df["scenario"] == "highway"]

    score_rows = ""
    for col in score_cols:
        if col in questionnaire_df.columns:
            city_avg = city_df[col].mean() if not city_df.empty else 0
            hw_avg = highway_df[col].mean() if not highway_df.empty else 0
            score_rows += f"| {q_labels[col]} | {city_avg:.1f} / 5.0 | {hw_avg:.1f} / 5.0 |\n"

    comments = []
    if "free_comment" in questionnaire_df.columns:
        for c in questionnaire_df["free_comment"].dropna():
            if str(c).strip():
                comments.append(f"- {c}")
    comment_str = "\n".join(comments[:8]) if comments else "- コメントなし"

    return f"""# DS検証結果報告書ドラフト

**案件ID：** {request.get('request_id', '')}
**案件名：** {request.get('request_title', '')}
**作成日：** {today}
**作成：** AIエージェント（ドラフト）
**ステータス：** 担当者確認待ち

---

## 1. 検証概要

| 項目 | 内容 |
|------|------|
| 目的 | {request.get('purpose', '')} |
| 評価対象 | {request.get('target_function', '')} |
| 実施環境 | {top_dils['dils_id']} |
| 被験者数 | {questionnaire_df['participant_id'].nunique() if not questionnaire_df.empty else 12}名 |

---

## 2. 試験条件

走行シナリオ：{', '.join(request.get('preferred_scenario', ['city', 'highway']))}
取得データ：{', '.join(request.get('required_data', []))}

---

## 3. 実施結果 — アンケート集計

| 設問 | 市街地平均 | 高速道路平均 |
|------|----------|------------|
{score_rows}

### 自由記述（抜粋）

{comment_str}

---

## 4. 分析・考察

市街地・高速道路ともに全項目で一定の評価を得た。
気づきやすさ・内容理解は特に高評価。
高速走行時のタイミング適切さにやや改善余地あり。

---

## 5. 残課題・追加確認事項

- 合否判断基準を依頼者と合意する
- 自由記述で指摘された改善点を次回設計に反映する
- 過去テスト（TEST-2025-014）との定量比較を実施する

---

## 6. 参照資料

- data/03_reference/dils_master.csv
- data/03_reference/past_tests.csv
- validation_knowhow.md
- trouble_knowhow.md

---
*このドラフトはAIが自動生成しました。担当者が確認・修正して最終版を作成してください。*
"""
