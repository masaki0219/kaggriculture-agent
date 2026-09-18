# Kaggriculture Agent

Kaggle Featured Simulation Competition **Kaggriculture** のエージェントを、最終 Leaderboard の Bradley–Terry 評価をできるだけ高くするために研究・実験するリポジトリ。

Competition: https://www.kaggle.com/competitions/kaggriculture

この `README.md` は単なる紹介ではなく、**プロジェクトの目的、現在地、判断原則、重要な実験履歴、ChatGPT / Codex への引き継ぎ方針をまとめる canonical document** として使う。

Status snapshot: **2026-09-18 / repository reorganization 後 / E29 評価済み / E30 は GitHub 上に存在せず未実行**

---

# 0. 最初に読むこと

新しい ChatGPT / Codex セッションや作業者は、過去チャットの局所的な文脈より先に次を確認する。

1. この `README.md`
2. `docs/current_research_state.md`
3. `docs/repository_layout.md`
4. `docs/experiment_index.md`
5. `docs/experiment_run_history.md`
6. GitHub の最新 commit と現在のコード
7. 必要な experiment の `README.md` / `results.md` / `results.json`

原則:

> **GitHub の最新状態 > 古い README > 過去チャットの断片的な記憶**

ただし、この README 更新後に新しい実験結果が出た場合は、その新しい evidence を優先する。

重要な current paths:

| Role | Canonical path |
| --- | --- |
| Current frozen frontier reference | `artifacts/bundles/current/agent_e21_tetsu_market_v23.py` |
| Historical strong baseline | `artifacts/bundles/current/agent_e11_prvsiyan_frontier.py` |
| Latest M-family research snapshot | `artifacts/bundles/current/agent_e29_m_family_staged_opening.py` |
| Latest evaluated experiment | `experiments/e029_m_family_staged_opening/` |
| Current research state | `docs/current_research_state.md` |
| Experiment index | `docs/experiment_index.md` |
| Experiment execution history | `docs/experiment_run_history.md` |
| Live-population replay archive | `data/replays/2026-09-18/live_population.zip` |
| M-family replay corpus | `data/corpora/2026-09-18/m_family.zip` |

**E30 は現在 GitHub に存在しない。実行済み・評価済みとして扱わない。**

## 0.1 詳細分析は README に複製しない

README は「目的・現在地・判断原則・読むべき場所」を保持する。

詳細な解析結果が既に GitHub にある場合、同じ内容を README や ChatGPT の会話メモへ重複コピーしない。必要なときに canonical report を直接読む。

現在の主要 analysis / evidence sources:

| Topic | Canonical source |
| --- | --- |
| Current frontier failure regimes | `analysis/frontier_failure_regimes/report.md` |
| E21 structure | `experiments/e021_tetsu_market_v23/structure_report.md` |
| E21 shop routes | `experiments/e021_tetsu_market_v23/shop_route_report.md` |
| E21 realized shop response | `experiments/e021_tetsu_market_v23/realized_shop_response.md` |
| E21 vs aurax market-policy difference | `experiments/e021_tetsu_market_v23/aurax_market_diff.md` |
| E22 market-policy result | `experiments/e022_market_policy_swap/market_policy_results.md` |
| E21/E22 strong common panel | `experiments/e022_market_policy_swap/strong_panel_results.md` |
| M replay-router failures | `experiments/e023_m_family_v1/results.md`, `experiments/e024_m_family_corrected/results.md` |
| State-based M branch | `experiments/e026_m_family_state_based/results.md` through `experiments/e029_m_family_staged_opening/results.md` |
| Machine-readable details | each experiment's `results.json` |
| Replay evidence | `data/replays/2026-09-18/live_population.zip`, `data/corpora/2026-09-18/m_family.zip` |

新しい ChatGPT / Codex セッションで詳細な主張を使う場合、README の要約だけで推測せず、該当する report / result を読む。

---

---

# 1. 最終目的

## 1.1 本来の目的

**Kaggriculture の最終 Leaderboard における Bradley–Terry 評価を最大化すること。**

これだけが最終目的。

以下は目的ではない。

- raw reward / coin を最大化すること
- mean margin を最大化すること
- E11 に勝つこと
- E21 に勝つこと
- 特定 opponent に圧勝すること
- replay を完全再現すること
- 上位 agent のソースコードを復元すること
- adaptive にすること
- RL を使うこと
- 自作度を高くすること
- コードを複雑にすること
- 評価器を高度化し続けること
- 最新 experiment を必ず採用すること

これらはすべて、

> **unknown / active leaderboard population に対する W/D/L を改善する**

場合にだけ価値がある。

## 1.2 何を最適化するか

Kaggriculture は shared market を持つ対戦ゲームなので、単独 farm score だけでは agent の価値は決まらない。

重要なのは opponent ごとの matchup vector。

```text
A > B
B > C
C > A
```

のような non-transitivity もあり得る。

したがって概念的な目標は、

```text
P(win | active leaderboard population)
```

を高めること。

局所的な H2H、raw reward、coin margin は evidence / diagnostic であり、最終目的ではない。

---

# 2. Competition facts

2026-09-18 時点で Kaggle 公式 Overview / Staff clarification から確認している内容。

- Final Submission Deadline: **2026-09-30 23:59 UTC**
  - 日本時間: **2026-10-01 08:59 JST**
- 1日最大 5 submissions
- 最新 2 submissions が tracked / final evaluation 対象
- 720 turns 終了時の bank coins が多い方が勝ち
- rating では coin margin 自体は使われず、win / loss / tie が重要
- 締切後もしばらく games が続き、その episodes から final Bradley–Terry tournament が行われる
- Kaggle Staff clarification:
  - team score は active 2 submissions の **良い方**
  - 2本目は hedge として使える
  - tie は各 side 0.5 win

Sources:

- https://www.kaggle.com/competitions/kaggriculture/overview
- https://www.kaggle.com/competitions/kaggriculture/discussion/732931
- https://www.kaggle.com/competitions/kaggriculture/discussion/739410

最終 submission 判断の直前には必ず再確認する。

---

# 3. Repository structure

整理後の canonical layout:

| Path | Responsibility |
| --- | --- |
| `experiments/` | immutable な numbered experiments と legacy v/h series |
| `evaluation/` | experiment-independent arena / screen |
| `analysis/` | diagnostics / replay / economy / one-off analysis |
| `public_agents/` | external Git submodules |
| `artifacts/` | canonical runtime bundle / submission artifacts |
| `archive/` | superseded bundles / retained duplicates / historical packages |
| `data/` | replay corpus / downloaded data / meta cache |
| `tools/` | acquisition / setup / bundle maintenance |
| `docs/` | experiment index / run history / repository documentation |

root 直下には原則として、README・設定ファイル・主要 directory だけを置く。

Active runtime bundle:

```text
artifacts/bundles/current/
```

E21–E29 の各 experiment directory は、agent / builder / screen / results を experiment 単位で追える構成にする。

詳細は `docs/repository_layout.md` を参照する。

---

# 3.1 Working-directory rule

ローカル repository root は原則:

```text
/Users/takahashimasaki/Desktop/Kaggle
```

**すべての開発・分析・screenコマンドは Kaggle 直下から実行できるようにする。**

良い例:

```bash
python experiments/e029_m_family_staged_opening/screen.py
python analysis/frontier_failure_regimes/analyze.py
python evaluation/frontier_screen_v2/arena.py
```

避ける:

```bash
cd experiments/e029_m_family_staged_opening
python screen.py
```

新しい Python script は、特定 directory へ `cd` しないと動かない設計にしない。必要な repository path は `Path(__file__)` などから安定して解決する。

同時に、**実行しやすさのためだけに root 直下へ大量の `.py` を置かない。**

ファイルは責務に応じて、

```text
experiments/
analysis/
evaluation/
tools/
```

へ置き、rootから path付きで実行する。

ユーザーへ実行コマンドを渡す場合も、特に指示がない限り Kaggle 直下にいる前提で1行のコマンドを示す。

---

# 4. Experiment 管理の絶対ルール

## 4.1 E番号は immutable

一度実験として使った E番号の意味を変更しない。

```text
E27 のロジックを修正した
→ E27を書き換えない
→ E28 / E29 / ... と新番号にする
```

欠番を詰めない。同じ名前の agent の中身だけ差し替えない。

## 4.2 E25 の扱い

E25 は会話・ローカル作業中に設計案が存在したが、現在の GitHub experiment history には canonical experiment として存在しない。

したがって、

- E25 を勝手に復元しない
- E25 の結果を捏造しない
- 欠番だからという理由で後から別実験に再利用しない

GitHub に存在する履歴を正とする。

## 4.3 cache / results は研究履歴

結果が悪くても `results.md` / `results.json` / cache / telemetry は experiment history。

routine で消さない。

## 4.4 implementation failure と strategy failure を分ける

agent が弱かったときは、

```text
runtime error?
↓
経済が成立している?
↓
意図した mechanism が発動している?
↓
想定 trajectory を再現している?
↓
その上で W/D/L はどうか?
```

の順で見る。

---

# 5. 現在の戦略地図

## 5.1 E21 — current frozen frontier reference

E21 = **Tetsu Market-Smart Farming V23**

canonical:

```text
artifacts/bundles/current/agent_e21_tetsu_market_v23.py
```

SHA256:

```text
f6a756cfb900b9d5f499905d596b63f1fde2445342ac4b1ae04e353739bd62d2
```

E21 は現在の **強い generalist / K-line reference** として扱う。

ただし、

```text
E21に勝つ = 最終Leaderboardで強い
```

ではない。

## 5.2 E22 — market-policy mechanism isolation

E22 は E21 の production / route / opening をほぼ維持し、market policy を変更した experiment。

market mechanism の evidence として意味があるが、独立した production family ではない。

## 5.3 E11 — historical strong baseline

E11 Prvsiyan Frontier exact は過去の強い frozen baseline。

canonical:

```text
artifacts/bundles/current/agent_e11_prvsiyan_frontier.py
```

E11 direct H2H を candidate acceptance gate にしない。

---

# 6. 2026-09-18 live population から得た最重要 evidence

2026-09-18 に current leaderboard top layer を replay から再取得した。

archive:

```text
data/replays/2026-09-18/live_population.zip
```

top20 の大分類:

```text
K-family: 8
M-family: 7
Other:    5
```

Top10:

```text
K:     3
M:     5
Other: 2
```

M-family は top-heavy だった。

このため、

> **E21/K系だけを局所改善するより、独立した M-family を理解・再構成して portfolio diversity を作る価値が高い**

と判断している。

---

# 7. M-family とは何か

M-family corpus:

```text
data/corpora/2026-09-18/m_family.zip
```

収集:

- 96 replay files
- 7 M-family teams × 12 runs = 84 M-family player-runs
- K-family control も含む

M-family の core signature:

```text
4 hires
2 cows
3 sheep
melon seed 6 の初期 tranche
wheat seed 約 7–11
```

重要:

> **M6 は「メロンを6枚だけ作る」という意味ではない。**

day0 の初期 seed 購入 tranche が6であり、その後追加購入する。

代表的な land timing:

```text
2Q: step 149–150 前後
3Q: step 218–224 前後
```

shop unlock:

```text
shop1: step 72
shop2: step 144
shop3: step 216
shop4: step 288
```

## 7.1 shop-conditioned production

84-run corpus では、

```text
MILK demand ↑      → cows ↑
WOOL demand ↑      → sheep ↑
STRAWBERRY demand ↑ → strawberry acreage ↑
CARROT demand ↑    → late carrot conversion ↑
TOMATO demand ↑    → midgame tomato ↑
```

という強い傾向がある。

WHEAT は demand-specific crop というより、feed / cashflow / residual acreage を支える backbone と見る。

## 7.2 market は family invariant ではない

DSM は極端に sell-heavy だが、他の M-family agent は market style がかなり異なる。

したがって、

```text
M-family = DSM型SELL spam
```

ではない。

---

# 8. 上位ログから何を再現するのか

目標は **上位agentのソースコードをログから復元することではない。**

目標は、

> **ゲームログから、強さを生んでいる意思決定構造 / policy / module を推定し、別の program として再構成すること。**

```text
observed state
↓
top agent action
↓
many replays
↓
common mechanism
↓
policy hypothesis
↓
our implementation
↓
trajectory comparison
↓
hypothesis update
```

system identification / imitation learning / program synthesis に近い。

理想構造:

```text
Strategy
  day / shop / capital
  → target scale / composition

Planner
  current state と target の差
  → jobs

Executor
  jobs
  → farmer / hands

Market
  live cash / inventory / prices
  → SELL / HIRE / LAND / BUY
```

---

# 9. なぜ replay-router を捨てたのか

## E23

24 replay-derived routes を再生する方式。

結果は broad screen で `0-0-96`。

最初に state/action の1turnずれという実装問題が判明した。

## E24

alignment を直したが、donor replay の cash / inventory / position / market trajectory への依存が強く、実用経済にならなかった。

結論:

```text
strong replay
↓
720-turn actionsを再生
```

ではなく、

```text
strong replay corpus
↓
policy / target / moduleを推定
↓
live stateから行動を生成
```

へ移行した。

**E23/E24を再び細かくpatchする経路には戻らない。**

---

# 10. State-based M-family branch: E26–E29

## E26

replay action を捨てて state-based planner/executor へ移行。

前進したが、shop-conditioned target を独立に足しすぎ、structure / herd が過剰になり crop production を圧迫した。

## E27

- first4 shops を重視
- M6 を初期 tranche として再解釈
- crop / structure trajectory を導入
- purchase pacing を改善

economic gate は通過したが M-family trajectory fidelity は不足。

## E28

`total scale → shop-conditioned composition` という仮説を実装しようとしたが、market / workforce hard gate で bootstrap cashflow を壊し、ほぼcollapse。

**implementation regression** と扱う。

## E29

E28ではなく、最後に経済が成立していた E27 を土台に戻した。

仮説:

```text
4H / 2C3S / M6 / W~10
```

は step0 の一括購入ではなく、day0 全体で段階的に到達する cashflow policy。

最新結果:

```text
Status: OPENING FIDELITY FAIL
Errors: 0
```

| Step | E29 crops | M reference | Structures | Animals | Hands |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 23 | 4.0 | ≈15.5 | 5 | 5 | 4 |
| 47 | 9.5 | ≈19.5 | 5 | 5 | 3 |
| 71 | 17.5 | ≈20 | 5 | 5 | 6 |
| 143 | 20.0 | ≈20 | 5 | 5 | 6 |

重要:

- structure=5
- animals=2C3S
- later hands trajectory
- step143 crop total

はかなり近づいた。

main bottleneck は、

> **step23 / step47 の植え付け速度**

と考える。

---

# 11. 現在の opening 仮説

M-core の複数 replay では day0 action sequence に強い共通性がある。

典型:

```text
WHEAT product + COW
↓
HIRE x4
COW / SHEEP
↓
pasture build / animal placement / feed / care
↓
MELON seedを小分け購入
↓
複数handsで melon plant + water
↓
WHEAT seed追加
↓
複数handsで wheat plant + water
```

したがって、

> **opening は完全generic plannerではなく、かなり固定された opening program / module を持つ**

可能性がある。

候補 architecture:

```text
fixed / semi-fixed day0 opening
↓
state-based midgame planner
↓
first4-shop conditioned routing
↓
live market
```

ただし、この consensus-opening idea はまだ canonical experiment ではない。

**E30 は現在 GitHub に存在せず、未実行。**

---

# 12. 次にやること

## Phase 1 — opening module identification

M-core replay corpus から、

```text
step 0..23
step 24..47
step 48..71
```

の action fingerprint を比較する。

確認するもの:

- どこまで family-wide fixed か
- どこから state-dependent になるか
- team間で共通する部分
- subfamily差

## Phase 2 — next M candidate

次の新しい canonical logic を作る場合のみ **E30** を使う。

作る前から E30 を存在扱いしない。

候補:

```text
family-wide consensus opening
↓
state-based planner
↓
shop-conditioned production
↓
live market
```

## Phase 3 — fidelity first

いきなり大量の E21 H2H を回さない。

opening:

```text
step23 / 47 / 71 / 143
```

midgame:

```text
land timing
hands
herd size
crop footprint
shop-conditioned composition
```

を先に見る。

上位M-familyのtrajectoryへ近づいてから W/D/L を評価する。

## Phase 4 — population screen

成立した候補だけを、多様な opponent family に対して fresh seeds / both seats で評価する。

## Phase 5 — final portfolio

現時点の方向:

```text
Slot A:
strong broad generalist
→ E21が有力reference

Slot B:
strong independent complement
→ M-family branchが候補
```

M-family が弱いままなら diversity のためだけに採用しない。

---

# 13. 開発原則 — このチャットで繰り返し修正されたこと

## 13.1 局所課題を目的にしない

major decision のたびに、

```text
この作業は最終 BT を上げる経路上にあるか？
```

を確認する。

## 13.2 patch loop に入ったら一段上へ戻る

同じ architecture に小修正を繰り返しているなら implementation premise 自体を疑う。

E23→E24 の後に replay-router から state-based へ移った判断を参考にする。

## 13.3 featureではなくsystemを推定する

```text
3Qが早い
SELLが多い
M6
pasture5
```

を単独でコピーしない。

見るべきは、

```text
opening
cashflow
labour
land
herd
crop
shop response
inventory
market
```

の連動。

## 13.4 replay actions と policy を混同しない

知りたいのは、

```text
step221でCOW3を買った
```

ではなく、

```text
shop state + cows + capacity + cash
→ cow targetとの差を埋める
```

という rule。

## 13.5 implementation failureをstrategy evidenceにしない

reward≈0 / economy collapse / trajectory破綻した版は family strength を評価していない。

## 13.6 smoke gateはabsolute economicsを見る

runtime error 0だけでは不十分。

reward / land / hands / crops / herd / structure を見る。

## 13.7 評価器を目的化しない

evaluation framework は strategy research の道具。

## 13.8 baselineを神格化しない

historical strength と current population strength は別。

## 13.9 同じ指摘をユーザーに繰り返させない

一般化可能な correction は README の原則へ昇格する。

---

# 14. Evaluation protocol

candidate比較では可能な限り、

1. same seeds
2. both seats
3. fresh seeds
4. strong + diverse opponent families
5. W/D/L primary
6. marginはdiagnostic
7. tuning seedsとholdoutを分ける
8. broken economyをaggregateに混ぜない
9. mechanism telemetryを取る
10. trajectory fidelityを先に見る
11. saturated panelでmargin rankingを続けない
12. local evidenceとlive leaderboard evidenceを分ける

---

# 15. Final two-slot portfolio

Kaggle Staff clarificationでは、team score は active 2 submissions の良い方。

理想:

```text
Agent A:
broad generalist

Agent B:
Aとfailure mode / lineageが異なるstrong complement
```

`strong K-line + strong independent M-line` は候補だが、M-line が弱ければ採用しない。

---

# 16. Experiment status summary

詳細は `docs/experiment_index.md` を正とする。

| Experiment | Current interpretation |
| --- | --- |
| E11 | historical strong baseline |
| E17 | idle-hand rescue / no-op |
| E18 | late-shop tape switch / state mismatch |
| E19 | early SW history |
| E20 | mechanism発動。E11 H2Hだけでglobal rejectしない |
| E21 | **current frozen frontier reference** |
| E22 | market-policy mechanism experiment |
| E23 | replay-router implementation failure |
| E24 | alignment fixed; replay routing still insufficient |
| E25 | no canonical GitHub experiment; gapを維持 |
| E26 | state-based M; economy improved |
| E27 | economic gate passed; trajectory insufficient |
| E28 | implementation regression / collapse |
| E29 | **latest evaluated; opening fidelity fail** |
| E30 | **not present / not executed** |

---

# 17. Licensing / public code

public agent / notebook / GitHub repo の source を derivative や final submission に使う前に license を確認する。

```text
publicに見える
≠
自由にコピーしてよい
```

ゲームログから behavior / statistics を分析することと、外部 source code をコピーすることを分ける。

---

# 18. ChatGPT / Codex 作業規約

## 18.1 Source of truth

長期原則:

```text
README.md
```

現在地:

```text
docs/current_research_state.md
```

実験の事実:

```text
docs/experiment_index.md
docs/experiment_run_history.md
experiments/e0xx_.../results.md
experiments/e0xx_.../results.json
```

詳細分析:

```text
analysis/
experiments/e021_tetsu_market_v23/*.md
experiments/e022_market_policy_swap/*.md
```

生replay:

```text
data/
```

という役割分担にする。

**会話メモリだけを source of truth にしない。**
詳細が GitHub に残っている場合は、まずそのファイルを読む。

## 18.2 Current state は短く保つ

`docs/current_research_state.md` は README のコピーにしない。

書くのは、

- current reference
- latest evaluated experiment
- current hypothesis
- current bottleneck
- next unused E number
- immediate next action
- do-not-do

程度。

experiment を評価して現在地が変わったら更新する。


- 新しいセッションではまず README を読む
- GitHub の latest evaluated experiment を確認する
- substantial work は experiment / analysis / evaluation directory に残す
- script は Kaggle repository root から実行可能にする
- 新logicは新E番号
- fidelity / smoke gate を先に置く
- 明らかに壊れた候補で大量arenaを回さない
- 分析結果は「今回わかったこと → 判断 → 次にやること」まで示す
- ユーザーに毎回「次は？」と聞かせない
- final objectiveから外れたらメタに戻る

---

# 19. Historical lessons that must not be forgotten

## Kaito27

historical frontier と current population strength は別。

## E11 micro-patches

coordinated tape に局所patchを入れると state mismatch が起きやすい。

## E23/E24

ログからコピーすべきなのは 720 actions ではなく policy structure。

## E28

高レベル仮説がよくても bootstrap cashflow を壊せば0になる。

## E29

最終farm shapeだけでなく、**到達速度 / trajectory** が重要。

---

# 20. Current decision

2026-09-18 時点:

```text
E21
= strongest frozen generalist/reference

M-family research
= strategically justified independent branch

E29
= latest evaluated M implementation
= opening skeleton is closer
= day0/day1 planting speed still wrong

E30
= does not exist on GitHub
= not executed
```

次の研究テーマ:

> **M-core の day0 opening がどこまで family-wide fixed program なのかを action fingerprint から確定し、必要なら次の immutable experiment として実装する。**

評価順序:

```text
opening fidelity
↓
midgame fidelity
↓
population W/D/L
```

---

# 21. README update rule

更新するタイミング:

- 新experimentを評価した
- current referenceが変わった
- live population mapが変わった
- strategy hypothesisが大きく変わった
- final portfolio方針が変わった
- repository layoutが変わった
- ユーザーから一般化すべき correction を受けた

確定事項として書かないもの:

- 未実行agent
- 1 replayだけの現象
- mechanism未確認の仮説
- live leaderboardの瞬間値
- local marginだけからのglobal strength

---

# 最後の原則

**本来の目的を忘れないこと。**

チャットやexperimentが進むほど、直前の局所課題が大きく見える。

そのたびに一段上から、

```text
この作業は、
最終時点の active leaderboard population に対する
勝率 / Bradley–Terry を上げる道筋に本当に接続しているか？
```

を確認する。

目的は E21 を倒すことでも、M-familyを完全コピーすることでも、E30を成功させることでもない。

目的は、

> **最終 Kaggriculture Leaderboard で、未知・多様な active population に対する Bradley–Terry performance を最大化すること。**
