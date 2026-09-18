# Current Research State

Updated: **2026-09-18**
Repository state checked against `main` commit:

```text
1f289b8cb96cabf6d58a876d987358ea1404d1d0
Reorganize experiment artifacts and data
```

このファイルは「今どこにいて、次に何をするか」だけを短く保持する。
長期方針は `README.md`、詳細な実験履歴は `docs/experiment_index.md` と各 experiment result を正とする。

---

## 1. Final objective

最終目的:

> **Kaggriculture の final active leaderboard population に対する Bradley–Terry performance を最大化する。**

raw reward、coin margin、特定 opponent への勝利、M-family の完全再現は最終目的ではない。

---

## 2. Current references

### Frozen generalist reference

```text
E21 — Tetsu Market-Smart Farming V23
artifacts/bundles/current/agent_e21_tetsu_market_v23.py
```

E21 は current reference だが、最終正解として固定しない。

### Historical strong baseline

```text
E11 — Prvsiyan Frontier exact
artifacts/bundles/current/agent_e11_prvsiyan_frontier.py
```

### Current M-family research snapshot

```text
E29 — staged-opening state-based M-family
artifacts/bundles/current/agent_e29_m_family_staged_opening.py
```

---

## 3. Latest evaluated experiment

Latest evaluated:

```text
E29
experiments/e029_m_family_staged_opening/
```

Result:

```text
OPENING FIDELITY FAIL
errors = 0
```

Observed opening medians:

| Step | E29 crops | M-family reference | Structures | Animals | Hands |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 23 | 4.0 | ≈15.5 | 5 | 5 | 4 |
| 47 | 9.5 | ≈19.5 | 5 | 5 | 3 |
| 71 | 17.5 | ≈20 | 5 | 5 | 6 |
| 143 | 20.0 | ≈20 | 5 | 5 | 6 |

Interpretation:

- 5 structures / 2C3S / later hand count / step143 crop total はかなり近い
- day0–day1 の planting speed が遅い
- E29 は全面collapseではない
- bottleneck は M-family全体より opening execution にある可能性が高い

Canonical evidence:

```text
experiments/e029_m_family_staged_opening/results.md
experiments/e029_m_family_staged_opening/results.json
```

---

## 4. Current research hypothesis

M-family の強さは、単純な feature 集合ではなく、

```text
opening cashflow
+ hand routing
+ land timing
+ total production scale
+ first shops による composition routing
+ live market
```

の system と考える。

現在特に有力な仮説:

> **day0 opening は完全generic plannerではなく、family-wide にかなり固定された program / module を持つ可能性がある。**

その後に state-based planner / shop-conditioned routing へ移る hybrid architecture が候補。

これはまだ確定していない。

---

## 5. Immediate next action

まず新agentを作るのではなく、M-family corpusから opening action fingerprint を確認する。

対象:

```text
step 0..23
step 24..47
step 48..71
```

調べること:

1. action sequence の exact / near agreement
2. teamを跨いで固定されているturn
3. shopやmarket stateで分岐するturn
4. fixed program と state-dependent planner の境界
5. Majkel / DSM / Orbital / Arda / QQ / kwa / ymg_aq の subfamily差

使用する corpus:

```text
data/corpora/2026-09-18/m_family.zip
```

---

## 6. Next experiment number

次に新しい canonical logic を実際に作る場合:

```text
E30
```

ただし現在:

```text
E30 = NOT PRESENT
E30 = NOT EXECUTED
E30 = NOT EVALUATED
```

ファイルを作る前から結果やstatusを仮定しない。

---

## 7. Expected next architecture if evidence supports it

仮説が action fingerprint で支持された場合のみ:

```text
family-wide fixed / semi-fixed opening module
↓
state-based planner
↓
first4-shop conditioned production routing
↓
live market
```

を次candidateとして検討する。

opening fidelity を通過する前に大規模 W/L screen はしない。

---

## 8. Evaluation order

次candidateは以下の順で見る。

### A. Integrity

- runtime errors
- economy collapse
- cash
- hands
- land
- crops / herd / structures

### B. Opening fidelity

```text
step23
step47
step71
step143
```

### C. Midgame fidelity

- 2Q / 3Q timing
- hand trajectory
- herd scale
- crop footprint
- shop-conditioned composition

### D. Population W/D/L

trajectoryが成立した後だけ、多様な opponent families で fresh seeds / both seats を使う。

---

## 9. Important evidence files to read before changing direction

```text
analysis/frontier_failure_regimes/report.md

experiments/e021_tetsu_market_v23/structure_report.md
experiments/e021_tetsu_market_v23/shop_route_report.md
experiments/e021_tetsu_market_v23/realized_shop_response.md
experiments/e021_tetsu_market_v23/aurax_market_diff.md

experiments/e022_market_policy_swap/market_policy_results.md
experiments/e022_market_policy_swap/strong_panel_results.md

experiments/e023_m_family_v1/results.md
experiments/e024_m_family_corrected/results.md
experiments/e026_m_family_state_based/results.md
experiments/e027_m_family_trajectory/results.md
experiments/e028_m_family_scale_routed/results.md
experiments/e029_m_family_staged_opening/results.md
```

必要な数字がsummaryにない場合は対応する `results.json` を読む。

---

## 10. Do not do

現時点では次を避ける。

- E23/E24 replay-routerへ戻る
- E29の1 seedだけを見たmicro-patch
- E21 direct H2Hだけでcandidateをreject
- raw reward / margin を最終目的化
- 未実行E30を成功扱い
- opening fidelity未確認のcandidateに大規模arena
- root直下へ新しい実験ファイルを大量に置く
- experiment IDを再利用する
- 詳細analysisをREADMEへ重複コピーする

---

## 11. Working-directory rule

ローカルの標準 repository root:

```text
/Users/takahashimasaki/Desktop/Kaggle
```

コマンドは原則ここから実行する。

例:

```bash
python experiments/e029_m_family_staged_opening/screen.py
python analysis/frontier_failure_regimes/analyze.py
```

`cd experiments/...` を前提にしない。

---

## 12. Meta checkpoint

次の作業を始める前に必ず確認する:

> **これは最終 leaderboard population に対する Bradley–Terry を上げるための情報を増やしているか？**

「直前のexperimentを直すこと」自体が目的になっていたら、一段上へ戻る。
