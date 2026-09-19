# Kaggriculture Agent

Kaggle Featured Simulation Competition **Kaggriculture** のエージェント研究リポジトリ。

Competition: https://www.kaggle.com/competitions/kaggriculture

この `README.md` は単なる紹介ではなく、**このプロジェクトの目的・現在地・重要な証拠・研究上の判断原則・次に進む経路をまとめる canonical document** として使う。

Status snapshot: **2026-09-19**

---

# 0. 最初に読むこと

新しい ChatGPT / Codex セッションでは、直前の会話や最新 experiment の局所課題から始めない。

最初に確認する順序:

1. `README.md`
2. `docs/current_research_state.md`
3. `docs/experiment_index.md`
4. `docs/experiment_run_history.md`
5. `docs/repository_layout.md`
6. GitHub / local repository の最新 commit・working tree
7. 必要な experiment / analysis の `results.md`, `results.json`, report

最重要原則:

> **直前の実験を直すことではなく、最終 Leaderboard の Bradley–Terry を最大化する経路を選ぶ。**

GitHub にある文書が古く、より新しい live leaderboard evidence / experiment evidence が存在する場合は、**新しい evidence を優先**する。

---

# 1. 最終目的

## 1.1 本来の目的

**Kaggriculture の final active leaderboard population に対する Bradley–Terry / W-D-L performance を最大化すること。**

これだけが最終目的。

以下はそれ自体では目的ではない。

- raw reward / coin を最大化する
- coin margin を最大化する
- E11 / E21 / 特定 opponent に勝つ
- replay を完全再現する
- 上位 agent の挙動を忠実に模倣する
- M-family を完全再現する
- adaptive / RL /複雑な architecture を使う
- 自作度を上げる
- experiment 数を増やす
- local fidelity を極限まで上げる
- evaluation framework を高度化し続ける

これらはすべて、

> **active leaderboard population に対する勝率を上げる**

ときにだけ価値がある。

## 1.2 判断単位

Kaggriculture は shared market を持つ対戦ゲームなので、単独 farm score だけでは強さは決まらない。

概念的には、

```text
P(win | active leaderboard population)
```

を上げる。

したがって:

- direct H2H
- raw reward
- margin
- replay trajectory
- farm shape
- market telemetry

は **evidence / diagnostic** であり、最終目的ではない。

---

# 2. Competition facts

最終 submission 判断前には Kaggle 公式を再確認すること。

現時点で確認済みの重要事項:

- Final Submission Deadline: **2026-09-30 23:59 UTC**
  - 日本時間: **2026-10-01 08:59 JST**
- 1日最大 5 submissions
- 最新 2 submissions が active / final evaluation 対象
- 720 turns 終了時の bank coins が多い方が勝ち
- rating では coin margin ではなく win / loss / tie が重要
- active 2 submissions は hedge として使える
- final では active 2 submission のうち良い方を使うという Staff clarification がある

最終2枠は、単なる「1位候補 + 弱い保険」ではなく、

```text
A: strongest broad line
B: A と failure mode / lineage が異なる strong complement
```

を理想とする。

---

# 3. 2026-09-19 の現在地

## 3.1 Live leaderboard で確認済み

現在の重要な live evidence:

| Agent | Live score | Status / interpretation |
| --- | ---: | --- |
| **Tetsu Demand-Preserving Turn Sale Timing** | **≈2415** | current best live-validated candidate |
| **E21 — Tetsu Market-Smart Farming V23 exact** | **≈2264** | previous strong live-validated reference |
| **E22 — E21 farm + Aurax market policy swap** | **≈2032** | weaker than E21 live; mechanism experiment |
| **E11 — Prvsiyan Frontier exact** | **1624.2** | historical strong baseline |
| **Kaito27 exact** | **≈904** | historical submitted baseline |

注意:

- live score は瞬間値なので将来動く
- それでも **relative ordering と方向性** は重要な evidence
- Tetsu Demand-Preserving は提出約3時間で ≈2415 まで上昇し、E21 ≈2264 を上回った
- E22 は E21 より下に収束し、market-policy swap が general improvement ではないことを live で確認した

## 3.2 現在の active slots

2026-09-19 snapshot では、active 2 submission は概ね:

```text
Slot 1: Tetsu Demand-Preserving Turn Sale Timing  ≈2415
Slot 2: E22 E21 farm + Aurax market policy swap ≈2032
```

E21 は過去提出として ≈2264 の live evidence を持つが、最新2枠からは外れている。

**E22 を最終2枠に固定する理由はない。**
次の最優先候補は後述の Alperen。

---

# 4. 最新 public candidate screen

2026-09-19 に、公開された新しい Kaggriculture candidate を取得し、E21 と fresh H2H を実施した。

canonical result:

```text
evaluation/public_candidates_2026-09-19/
```

条件:

- seeds `36000..36007`
- both seats
- 16 games / candidate
- W-D-L primary
- margin diagnostic

結果:

| Candidate | W-D-L vs E21 | Median margin |
| --- | ---: | ---: |
| **tetsu_demand_timing** | **15-0-1** | **+1193** |
| **alperen_first_in_line** | **15-0-1** | **+229** |
| ahmed_v47 | 1-0-15 | ≈-34 |
| sunil_v8 | 1-0-15 | ≈-34 |

## 4.1 Tetsu Demand-Preserving

local:

```text
15-0-1 vs E21
median margin +1193
```

live:

```text
≈2415
```

E21:

```text
≈2264
```

したがって、local H2H の改善方向が **live population でも再現した**。

現在の strongest live-validated line。

## 4.2 Alperen First in Line

local:

```text
15-0-1 vs E21
median margin +229
```

まだ live validation が済んでいない。

**次に live submission slot を使う最優先 candidate。**

## 4.3 Ahmed V47 / Sunil V8

どちらも:

```text
1-0-15 vs E21
```

fresh H2H gate では非競争的。

現時点では live slot を使う優先度は低い。

---

# 5. E21 / E22 から得た重要な教訓

E22 は E21 の production / route / opening を維持しつつ、最終 market policy を Aurax 系へ置き換えた mechanism-isolation experiment。

## 5.1 Local evidence

E22 vs E21 direct:

```text
E22: 6-0-18
```

一方、strong common panel:

```text
E21: 91-0-5
E22: 91-0-5
```

local panel 上では同率だった。

## 5.2 Live evidence

```text
E21 ≈2264
E22 ≈2032
```

live population では明確な差が出た。

## 5.3 結論

1. **local common panel は population の全差を捉えない**
2. direct H2H だけで final strength を決めるのも不十分
3. ただし direct H2H を無視するのも誤り
4. 最終的には live population evidence が非常に重要
5. evaluation は「screen → population panel → live」で使い分ける

今後の candidate gate:

```text
integrity
↓
targeted mechanism / trajectory
↓
fresh H2H vs live-proven reference
↓
broader population panel
↓
live submission
```

---

# 6. 現在の最重要方針

## 6.1 まず public frontier を取り切る

Tetsu Demand-Preserving だけで、

```text
E21 ≈2264
→ Tetsu latest ≈2415
```

まで改善できた。

したがって、**新しい custom agent を作る前に、公開された強い candidate を回収・screen・live validation する方が期待値が高い場合がある。**

新しい agent を発明する前に必ず確認する:

```text
今、より新しく強い public candidate が存在しないか？
```

## 6.2 次の immediate action

**Alperen First in Line を live に提出し、E22 を active slot から外して評価する。**

期待する分岐:

### Alperen が ≈2400以上

public frontier にまだ強い line がある。

→ public candidates の最新版探索を続ける  
→ 最終2枠候補を比較する

### Alperen が ≈2200前後

E21級の candidate。

→ Tetsu latest を主軸にしつつ、次の candidate / custom mechanism を探す

### Alperen が ≈2000以下

E21 H2H 15-1 だけでは population strength を十分予測できない。

→ evaluation blind spot を再評価  
→ failure-driven custom workへ移行

---

# 7. Top leaderboard との差

最近の live population snapshot では、Top20 boundary はおよそ **2960前後**。

current best:

```text
Tetsu Demand-Preserving ≈2415
```

なので、まだ約 500+ rating の差がある。

つまり、

> **2415で十分ではない。**

ただしこの差を埋める方法は、「現在の agent を100回 micro-patchする」こととは限らない。

優先順位は:

```text
1. 新しい public frontier を確認
2. current best の live failure mode を観測
3. 強い family / mechanism を抽出
4. custom implementation
```

---

# 8. M-family research

## 8.1 なぜ調べたか

2026-09-18 の live population replay analysis では、Top層に M-family が多く存在した。

大分類:

```text
Top20:
K-family 8
M-family 7
Other    5
```

Top10:

```text
K 3
M 5
Other 2
```

M-family は top-heavy。

そのため、

> E21/K-line だけを改善するより、別lineの強さを理解する価値がある

と判断した。

## 8.2 目的

M-family研究の目的は、

- source reconstruction
- replay action copy
- imitationそのもの

ではない。

目的:

> **top agents に共通する意思決定構造を system identification し、独立した policy として実装できるかを調べる。**

---

# 9. M-family core evidence

M-family corpus:

```text
data/corpora/2026-09-18/m_family.zip
```

代表 fingerprint:

- hands 4 by ~step2
- 2 cows + 3 sheep by ~step2
- structures 5 by ~step8
- early melon acquisition / planting
- step23 typical:
  - crops ≈15.5
  - structures 5
  - animals 5
  - hands 4

典型 land expansion:

```text
2Q around step149-150
3Q around step218-224
```

重要:

**M6 は「最終的にmelon6枚」ではなく、opening seed tranche の特徴。**

---

# 10. E23-E33 M-family branch

E番号は immutable。過去 experiment の意味を書き換えない。

## E23 / E24

replay-derived action routing。

E23:

```text
0-0-96
```

alignment bug も存在。

E24 でalignmentを修正したが、donor replay の state / cash / inventory / position 依存が強すぎた。

結論:

> replay actions を再生する方式には戻らない。

## E26

state-based planner / executor。

replay playback を捨てた重要な転換点。

ただし target 設計が強すぎて structure / herd を過剰建設。

## E27

trajectory correction。

economic gate は通ったが、M-family production trajectoryに不足。

## E28

total scale → composition を狙ったが bootstrapを壊し、near collapse。

implementation regression。

## E29

E27 baseへ戻し staged opening。

opening skeleton は改善したが early planting speed が不足。

## E30

planting executor を強化。

植え付けは改善したが construction / animal placement が崩れた。

## E31

scheduler修正。

construction / animal handling を戻したが opening はまだ不足。

## E32

opening BUILD priority を修正。

結果:

- step23: crops12 / structures5 / animals5 / hands4
- step47: crops17 / structures5 / animals5 / hands4
- step71: crops18 / structures5 / animals5 / hands6
- step143: crops20 / structures5 / animals5 / hands6

opening skeleton はほぼ成立。

ただし midgame crop scale が不足。

## E33

midgame crop expansion を改善。

代表:

```text
step215 crops 28
step239 crops 28.5
step287 crops 37.5
```

E32より改善したが M-family reference:

```text
step215 ≈38
step239 ≈53
step287 ≈58.5
```

には届かない。

diagnostic:

```text
0-0-12 vs E21 / Aurax
```

結論:

> generic M-family planner をさらに微修正し続ける経路は一旦停止。

---

# 11. M-family から得た最重要 mechanism

Top M-like agents は midgame に synchronized production burst を持つように見える。

## Day 6

典型:

- hands ≈8
- Q2
- strawberry-heavy expansion
- crops ≈33+
- structures / animals ≈11
- BUY_SEED と PLANT が turn 単位で同期

## Day 9

典型:

- hands ≈10
- Q3
- wheat-heavy expansion
- crops ≈53+
- structures / animals ≈14

これは E33 のgeneric expansionより明確に速い。

## Potential future branch

もし public frontier / failure-driven route より期待値が高くなった場合:

> **seed-aware pipelined burst controller**

として再開する。

ただし M-family fidelity 自体を目的にしない。

---

# 12. Official environment semantics で重要なこと

公式 Kaggriculture environment source から確認済み。

- 24 turns / day
- 30 days
- 720 turns total
- starting money 3000
- hired hands は日末に消える
- HIRE cost は日内 Fibonacci、翌日 reset
- unit actions が market actions より先に実行される
- このturnで買ったseedは同turnのPLANTには使えない
- invalid action は silent no-op
- max market orders default 10
- movement onto locked tiles は可能だが tile operation は不可

特に重要:

> **同一cropのPLANT requestsがavailable seedを超えると、そのcropのPLANTがatomicに全部失敗する可能性がある。**

したがって future crop executor は:

```text
available seeds
>= simultaneous PLANT requests
```

を必ず守る。

---

# 13. Evaluation philosophy

## 13.1 評価順序

### A. Integrity

- runtime errors
- DONE
- economy collapseの有無

### B. Mechanism

- intended logic が発火したか
- telemetry
- target state / action trajectory

### C. Fresh direct H2H

current live-proven reference に対して:

- fresh seeds
- both seats
- W-D-L primary

### D. Population panel

- diverse opponent families
- saturated old panelだけに依存しない

### E. Kaggle live

最終的な実population evidence。

## 13.2 raw marginの扱い

marginはdiagnostic。

promotion criterionは W/D/L と population relevance。

ただし同じW-D-Lなら、mechanism strength を見る補助として margin は使える。

## 13.3 live leaderboardを実験装置として使う

live leaderboard は「最後に見るスコア」ではない。

> **local evaluationの盲点を発見する外部実験系。**

E21/E22でこれが実証された。

---

# 14. 開発上の絶対ルール

## 14.1 E番号は immutable

一度使った E番号は再利用しない。

agent logic を変えたら新E番号。

E25のような欠番も勝手に再利用しない。

## 14.2 局所patch loopを避ける

同じ architecture を何度もpatchしているなら、

```text
このarchitectureを直すこと自体が目的化していないか？
```

を確認する。

## 14.3 featureではなくsystemを見る

単独で:

```text
3Qが早い
SELLが多い
M6
pasture5
```

をコピーしない。

見るべきは:

```text
opening
cashflow
labor
land
crops
herd
shops
inventory
market
```

の相互作用。

## 14.4 implementation failureとstrategy failureを分ける

economy collapseしたagentで family strength を評価しない。

## 14.5 saturated panelを信じすぎない

E21/E22 の common panel は完全同率でも、liveでは約230点差が出た。

panel saturation / blind spot を常に疑う。

---

# 15. Repository layout

整理後の canonical layout:

| Path | Responsibility |
| --- | --- |
| `analysis/` | diagnostics / replay / mechanism analysis |
| `archive/` | superseded bundles / historical setup |
| `artifacts/` | current runtime / exact submitted artifacts |
| `candidates/` | downloaded public candidates |
| `data/` | replay / corpus / cache |
| `docs/` | project state / experiment history / cleanup records |
| `evaluation/` | generic arenas / screens / recorded evaluation |
| `experiments/` | immutable numbered experiments / legacy |
| `public_agents/` | external Git submodules |
| `tools/` | acquisition / setup / bundle utilities |

rootには一時submissionやscratchを置かない。

---

# 16. Submitted artifacts

実際に提出した artifact は:

```text
artifacts/submissions/
```

以下へ canonical 保存する。

現在:

```text
artifacts/submissions/e10_kaito27/
artifacts/submissions/e11_prvsiyan_frontier/
artifacts/submissions/e21_tetsu_market_v23/
artifacts/submissions/e22_market_policy_swap/
artifacts/submissions/tetsu_demand_preserving/
```

各 artifact は:

- exact submission bytes
- `metadata.json`
- `sha256.txt`

を持つ構成を基本とする。

failed packaging artifact はcanonicalにしない。

---

# 17. Public candidates

2026-09-19に取得した重要candidate:

```text
candidates/2026-09-19_public/
```

少なくとも:

- Tetsu Demand-Preserving
- Alperen First in Line
- Ahmed V47
- Sunil V8

の exact source / submission は保持する。

Kaggle output log, pycache,完全重複extractなどはcanonicalではない。

---

# 18. Replay / corpus data

重要data:

```text
data/replays/
data/corpora/
```

canonical:

```text
data/replays/2026-09-18/live_population.zip
data/corpora/2026-09-18/m_family.zip
```

展開済み tree はanalysis convenienceとして残る場合がある。

以前作った:

```text
live_population_before_e21/
live_population_before_e21.zip
```

は current `live_population` と byte-identical だったため削除済み。

`tools/acquisition/refresh_live_population.py` は実行日から保存先の日付を決めるよう修正済み。

---

# 19. Working-directory rule

repository root:

```text
/Users/takahashimasaki/Desktop/Kaggle
```

scriptは原則rootから実行可能にする。

良い例:

```bash
python evaluation/public_candidates_2026-09-19/...
python analysis/...
python experiments/e0xx_.../screen.py
```

不必要に `cd` 前提にしない。

rootへ一時 `.py` を大量に置かない。

---

# 20. Source of truth

長期原則:

```text
README.md
```

短いcurrent state:

```text
docs/current_research_state.md
```

experiment facts:

```text
docs/experiment_index.md
docs/experiment_run_history.md
experiments/
```

detailed analysis:

```text
analysis/
evaluation/
```

exact submitted artifacts:

```text
artifacts/submissions/
```

raw/public candidates:

```text
candidates/
artifacts/bundles/current/public_agents/
```

replays:

```text
data/
```

---

# 21. 今後の方針

## Phase 1 — Alperen live validation

最優先:

> **Alperen First in Line を live に提出して population performance を測る。**

E22は既に E21 より弱いことが分かっているため、active slotの情報価値は低い。

Alperenを出すことで:

```text
Tetsu latest
+
Alperen
```

の2本を直接比較できる。

## Phase 2 — public frontier refresh

Alperenの結果を見た後も:

- 新Notebook
- 新submission
- 新public candidate

を定期確認する。

custom workより安く strong line が得られるなら先に使う。

## Phase 3 — live failure-driven analysis

current best の live games / replay から:

- どの opponent family に負けるか
- shop regime
- sale timing
- production scale
- land timing
- labor
- terminal conversion

の共通failureを抽出する。

**current best が実際に負けているpopulationを直接見る。**

## Phase 4 — custom mechanism

必要なら:

### Route A
Tetsu latest の failure-specific coherent improvement

### Route B
M-like synchronized burst controller

### Route C
他family / new public lineage

を比較する。

直前branchを惰性で続けない。

## Phase 5 — final portfolio

締切前に:

- strongest live line
- independent strong complement

を最新2 submissionsにする。

最終直前にはKaggle rules / active submission status / scoresを再確認する。

---

# 22. 現時点の優先順位

2026-09-19 の判断:

```text
Priority 1:
Alperen live validation

Priority 2:
new public frontier acquisition

Priority 3:
current best live failure analysis

Priority 4:
custom agent development

Possible custom branch:
M-like day6/day9 pipelined burst
```

つまり、

> **今すぐE34を作ることは最優先ではない。**

---

# 23. Do not do

現時点では以下を避ける。

- E23/E24 replay-routerへ戻る
- E33を40crop→45cropのようにmicrofitし続ける
- raw rewardでcandidate rankingする
- 1 opponentだけでglobal strengthを決める
- local strong panelだけでpromotionを決める
- public最新版を確認せずcustom agentを作る
- Top agent imitationそのものを目的化する
- E21を永遠のreferenceとして固定する
- E22をfinal hedgeとして惰性で残す
- rootにtemporary submissionを残す
- experiment IDを再利用する
- live replay / corpusを雑に削除する

---

# 24. ChatGPT / Codex への最重要指示

このプロジェクトでは、会話が進むほど直前の局所課題に引きずられやすい。

毎回 major decision の前に必ず:

```text
いま考えている作業は、
最終 active leaderboard population に対する
Bradley–Terry / W-D-L を上げる経路として
本当に期待値が高いか？
```

を確認する。

もし答えが弱いなら、一段上へ戻る。

比較するべきは常に:

```text
このbranchを続ける
vs
public frontierを取る
vs
live failureを調べる
vs
別familyを調べる
vs
submission slotで直接測る
```

である。

---

# 25. Historical lessons that must not be forgotten

## E11

historical strong baselineでも current population では最強ではない。

## E21

localで強かっただけでなく liveでも≈2264まで上がり、評価系が完全に壊れてはいないことを示した。

## E22

common panelがE21と完全同率でも liveでは大きく弱かった。

→ **local panel blind spot の実例。**

## Tetsu Demand-Preserving

E21 H2H 15-1 → liveでもE21を上回った。

→ **fresh direct H2Hが有用なscreenになり得る実例。**

## E23/E24

replayからコピーするべきなのはaction列ではなくpolicy structure。

## E28

高レベル仮説が良くても bootstrap economy を壊せば意味がない。

## E32/E33

opening fidelityを上げても、それだけではmidgame scale / actual strengthに届かない。

---

# 26. Meta checkpoint

次の作業を始める前に必ず確認する:

> **これは final leaderboard population に対する Bradley–Terry を上げるための情報を増やしているか？**

「前のexperimentを直すこと」「M-familyに近づけること」「E21を倒すこと」が目的になっていたら、一段上へ戻る。

---

# 27. Current decision

2026-09-19:

```text
Current best live-validated:
Tetsu Demand-Preserving ≈2415

Previous strong live reference:
E21 ≈2264

Rejected as stronger generalist:
E22 ≈2032

Best unvalidated public candidate:
Alperen First in Line
15-0-1 vs E21
```

次の1手:

> **Alperenをliveに出して、E22 slotをより情報価値の高いcandidateに置き換える。**

その結果を見て、public frontier継続か、failure-driven custom developmentへ移るかを決める。

---

# 最後の原則

**本来の目的を忘れないこと。**

目的は:

- E21を倒すことではない
- M-familyを再現することではない
- E34を作ることではない
- local metricを上げることではない

目的は、

> **最終 Kaggriculture Leaderboard で、未知・多様な active population に対する Bradley–Terry performance を最大化すること。**

直前の作業より、常にこの目的を優先する。
