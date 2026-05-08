# ROOTMAP.md — 情報配置の地図

このファイルは「どこに何の情報があるか」を示す地図です。
AIエージェントはこのファイルを参照して、必要な情報の場所を特定します。

---

## 依頼情報はどこを見るか

| 情報 | 場所 |
|------|------|
| 今回のテスト依頼（構造化済み） | `requirement.md` |
| 受付時のサンプル依頼YAML | `data/04_sample/sample_request.yaml` |
| 各案件の受付内容 | `runs/{案件ID}/request.yaml` |
| 依頼者から受け取った資料 | `data/00_received/` |

---

## DiLS構成はどこを見るか

| 情報 | 場所 |
|------|------|
| DiLS5台の構成・設備・稼働状況 | `data/03_reference/dils_master.csv` |
| DiLS選定理由（案件別） | `runs/{案件ID}/dils_selection.md` |

---

## 過去テストはどこを見るか

| 情報 | 場所 |
|------|------|
| 過去テスト一覧（検索用） | `data/03_reference/past_tests.csv` |
| 各案件の試験計画 | `runs/{案件ID}/plan.md` |
| 各案件のシナリオ | `runs/{案件ID}/scenario.md` |
| 各案件の実行ログ | `runs/{案件ID}/execution_log.csv` |

---

## 検証ノウハウはどこを見るか

| 情報 | 場所 |
|------|------|
| DS検証の確認観点・チェックポイント | `validation_knowhow.md` |
| 過去トラ・失敗知見 | `trouble_knowhow.md` |
| DS検証チェックリスト | `data/03_reference/checklist.csv` |
| アンケートサンプル | `data/04_sample/sample_questionnaire.csv` |

---

## 報告書ドラフトはどこに出るか

| 情報 | 場所 |
|------|------|
| 案件別報告書ドラフト（作業中） | `runs/{案件ID}/report_draft.md` |
| 顧客提出用報告書（完成版） | `output/reports/` |
| デモ説明資料 | `output/deliverables/` |
| 画面キャプチャ | `output/screenshots/` |

---

## AIの作業ログはどこを見るか

| 情報 | 場所 |
|------|------|
| AIエージェントの作業記録 | `session_log.md` |

---

## フォルダー役割早見表

```
DS業務AIエージェント検証/
├── README.md              ← デモの入口・起動手順
├── AGENT.md               ← AIの作業ルール
├── ROOTMAP.md             ← この地図ファイル
├── requirement.md         ← 今回のテスト依頼・要求理解
├── validation_knowhow.md  ← DS検証ノウハウ
├── trouble_knowhow.md     ← 過去トラ・失敗知見
├── session_log.md         ← AIの作業ログ
├── app.py                 ← Streamlitデモアプリ
├── requirements.txt       ← Python依存関係
├── data/
│   ├── 00_received/       ← 依頼者から受け取った資料
│   ├── 01_raw/            ← 加工前データ
│   ├── 02_processed/      ← AI処理済みデータ
│   ├── 03_reference/      ← DiLSマスタ・過去テスト・チェックリスト
│   └── 04_sample/         ← デモ用サンプル
├── runs/
│   └── EXP-001_.../       ← 案件単位の実行記録
├── output/
│   ├── reports/           ← 顧客提出用報告書
│   ├── deliverables/      ← 提案用資料
│   └── screenshots/       ← 画面キャプチャ
└── src/                   ← 業務ロジック（Python）
```
