# DS業務AIエージェント ワークフロー仕様書

各ステップでAIエージェントが**何を読んで・どう判断して・何を生成するか**を定義する。

---

## STEP 1：受付

### インプット
| 種別 | ファイル/情報 | 内容 |
|------|-------------|------|
| 依頼書 | `runs/{ID}/request.yaml` | 依頼者・目的・対象機能・必要データ・未解決事項 |
| 参照 | `data/03_reference/past_tests.csv` | 類似目的の過去テストを探す |
| 参照 | `data/04_sample/sample_request.yaml` | 依頼フォーマットの記載例 |

### 処理ロジック
1. `request.yaml`の`open_questions`を読み、`resolved: false`の項目を特定する
2. `past_tests.csv`の`function_area`・`required_data`と依頼内容を照合して類似テストを検索する
3. 業務ナレッジ（`validation_knowhow.md`）を参照して各未解決事項に対する標準的な回答案を生成する
4. `ai_understanding.summary`に依頼全体の把握内容をまとめる
5. 推奨DiLS・推奨過去テストを仮決めする（次ステップで詳細化）

### 判断基準
- 走行場面が未定 → 目的に合った標準シナリオ（高速/市街地/合流）を提案
- 測定方法が未定 → アンケート5段階を基本とし、必要に応じて生理指標を追加提案
- 被験者条件が未定 → 経験者・未経験者混合（n=10）を標準として提案
- 合否基準が未定 → アンケート平均4.0点以上・介入操作3回以内を標準として提案

### アウトプット
| ファイル | 変更内容 |
|---------|---------|
| `runs/{ID}/request.yaml` | `open_questions`を全て`resolved: true`に更新、`ai_understanding`を記入、`status`を「計画中」に変更 |

---

## STEP 2：試験計画・DiLS選定

### インプット
| 種別 | ファイル/情報 | 内容 |
|------|-------------|------|
| 依頼書 | `runs/{ID}/request.yaml` | 解決済みの要件・推奨DiLS候補 |
| 参照 | `data/03_reference/dils_master.csv` | DiLS設備一覧・搭載機能・稼働状況 |
| 参照 | `data/03_reference/past_tests.csv` | 類似テストが使ったDiLS・実績 |

### 処理ロジック
1. `request.yaml`の`required_data`・`preferred_scenario`から必要な設備要件を整理する
2. `dils_master.csv`の`features`・`suitable_tests`・`status`と照合して候補を絞る
3. 類似テスト（`past_tests.csv`）が使用したDiLSを参考にして実績を確認する
4. 第一候補・補助設備を決定し、選定理由を明文化する
5. 実施スケジュール（準備〜提出）を標準日程で策定する

### 判断基準
- Eye Tracker必要 → DiLS-02を優先
- 操舵感・体感評価 → DiLS-03（Motion Platform）を優先
- ADAS制御ログ・外部連携必要 → DiLS-05を優先
- `status`が「整備中」のDiLSは除外する

### アウトプット
| ファイル | 内容 |
|---------|------|
| `runs/{ID}/dils_selection.md` | 選定設備・選定理由・候補比較表・類似テスト検索結果 |
| `runs/{ID}/plan.md` | 試験目的・構成・合否基準・参照テスト・実施スケジュール |

---

## STEP 3：シナリオ作成

### インプット
| 種別 | ファイル/情報 | 内容 |
|------|-------------|------|
| 試験計画 | `runs/{ID}/plan.md` | シナリオ数・被験者数・取得データ |
| 依頼書 | `runs/{ID}/request.yaml` | preferred_scenario（走行場面） |
| 参照 | `data/03_reference/past_tests.csv` | 流用可能なシナリオ資産 |
| 参照 | `data/03_reference/checklist.csv` | 設計品質の確認項目 |

### 処理ロジック
1. `preferred_scenario`をもとに各シナリオの走行条件（速度・時間・イベント回数）を設定する
2. `past_tests.csv`の`reusable_items`から流用できるシナリオ構成を確認する
3. アンケート設問を「測定したい概念（安心感・視認性など）」に対応させて設計する
4. `checklist.csv`の必須項目（S01〜S04, P01〜P02, Q01〜Q04）を照合して確認結果を記録する
5. 順序効果排除のため被験者の実施順序（カウンターバランス）を設定する

### 判断基準
- シナリオ再現性 → 再生ファイル統制を原則とする
- 設問数 → 5〜6問（5段階＋自由記述）を標準とする
- 逆転項目 → 「ストレス」「違和感」など負の概念は逆転項目として設計する

### アウトプット
| ファイル | 内容 |
|---------|------|
| `runs/{ID}/scenario.md` | 各シナリオの走行条件・ACCイベント・アンケート設問・チェックリスト確認結果 |

---

## STEP 4：テスト実行

### インプット
| 種別 | ファイル/情報 | 内容 |
|------|-------------|------|
| シナリオ | `runs/{ID}/scenario.md` | アンケート設問・シナリオ構成 |
| 依頼書 | `runs/{ID}/request.yaml` | 被験者条件・取得データ種別 |
| 参照 | `data/04_sample/sample_questionnaire.csv` | アンケートCSVのフォーマット例 |

### 処理ロジック
1. `scenario.md`の設問定義をもとにCSV列名を設計する（例：`q1_safety`, `q2_naturalness`）
2. 被験者属性（経験有無・年齢層）をCSVに記録する
3. シナリオごとに1行ずつアンケート回答・介入操作回数・自由記述を記録する
4. 実行ログには日時・使用DiLS構成・環境条件（室温・騒音）・特記事項を記録する

### 判断基準
- 列名はシナリオの測定概念を反映した英語スネークケースで命名する
- `scenario`列の値は`request.yaml`の`preferred_scenario`と一致させる
- データ欠損がある場合は`notes`列に理由を記録する

### アウトプット
| ファイル | 内容 |
|---------|------|
| `runs/{ID}/questionnaire.csv` | 被験者×シナリオ別アンケート回答・介入回数・自由記述 |
| `runs/{ID}/execution_log.csv` | 被験者×シナリオ別実施日時・DiLS構成・環境記録 |

---

## STEP 5：報告書作成

### インプット
| 種別 | ファイル/情報 | 内容 |
|------|-------------|------|
| アンケート結果 | `runs/{ID}/questionnaire.csv` | スコア集計・自由記述 |
| 実行ログ | `runs/{ID}/execution_log.csv` | 実施環境・特記事項 |
| 試験計画 | `runs/{ID}/plan.md` | 合否判断基準 |
| 依頼書 | `runs/{ID}/request.yaml` | 目的・合否基準 |
| 参照 | `data/03_reference/past_tests.csv` | 比較対象テストの結果 |

### 処理ロジック
1. `questionnaire.csv`をシナリオ別・設問別に平均算出する
2. `plan.md`の合否基準と照合して各シナリオの判定（合格/条件付き合格/不合格）を行う
3. 被験者属性（経験者/未経験者など）でグループ分けして差分を分析する
4. 低スコア被験者・自由記述の傾向から残課題を抽出する
5. 過去テスト（`past_tests.csv`）との比較が可能な場合は差分を記載する
6. 報告書完成後に`request.yaml`の`status`を「完了」に更新する

### 判断基準
- シナリオ平均が合否基準を下回る場合 → 「条件付き合格」として残課題に改善項目を記載
- 被験者グループ間で0.5点以上の差がある場合 → 考察で言及する
- 介入操作回数が基準超えの被験者がいる場合 → 個別フォローを残課題に記載

### アウトプット
| ファイル | 内容 |
|---------|------|
| `runs/{ID}/report_draft.md` | 検証概要・結果・合否判定・考察・残課題・参照資料 |
| `runs/{ID}/request.yaml` | `status`を「完了」に更新 |

---

## ステップ間のデータフロー

```
request.yaml（依頼）
    ↓ STEP1
request.yaml（解決済み）
    ↓ STEP2
dils_selection.md / plan.md
    ↓ STEP3
scenario.md
    ↓ STEP4
questionnaire.csv / execution_log.csv
    ↓ STEP5
report_draft.md / request.yaml（完了）
```
