# Kaggriculture Agent

Kaggle Featured Simulation Competition **Kaggriculture** のエージェントを、残り期間でできるだけ強くするための研究・実験リポジトリ。

Competition: https://www.kaggle.com/competitions/kaggriculture

この README は単なる紹介ではなく、**プロジェクトの目的、現在の判断原則、重要な実験結果、ChatGPT/Codex への引き継ぎ規約**をまとめる canonical document として使う。

---

## 0. 最初に読むこと

新しいチャット・新しい Codex セッション・新しい作業者は、過去チャットの断片的な記憶より先に次を確認する。

1. この `README.md`
2. `docs/repository_layout.md`
3. `docs/experiment_index.md`
4. GitHub 上の最新コード・最新 commit
5. 必要なら各 experiment の `NOTES.md` / cache / results

**GitHub / README / 現在のコードと会話メモリが食い違う場合、原則として GitHub の最新状態を優先する。**

ただし README 更新後に新しい実験結果や重要な方針修正が出た場合、その最新情報を次の README 更新時に反映する。

### この README を継続更新するルール

ユーザーが今後、

- 「それは本来の目的と違う」
- 「その評価に何の意味があるのか」
- 「それを追加して本当に強くなるのか」
- 「既知の1体に勝つことと未知相手に勝つことは別ではないか」
- 「毎回同じことを指摘させないで」
- その他、探索方針・評価方針・実験管理について重要な修正

を指摘した場合、その指摘が一時的な感情ではなく**再発防止に有用な一般原則**だと判断できるなら、README の「開発原則」または関連節へ反映する。

同じ指摘をユーザーに何度も言わせないこと。

一度しか指摘されていなくても、本来の目的から見て重要な原則なら残す。

README は「過去の判断を消して最新意見だけを書く」のではなく、

- 当時どう判断したか
- 後で何が分かって判断基準がどう変わったか

を区別して記録する。

---

# 1. 最終目的

## 1.1 本来の目的

**Kaggriculture の最終 Leaderboard における Bradley-Terry 評価を最大化すること。**

これだけが最終目的。

以下は目的ではない。

- raw reward / coin の最大化
- mean margin の最大化
- 特定の1 opponent への圧勝
- E11 に勝つこと
- E11 と違うこと
- 自作度を高めること
- adaptive にすること
- RL を使うこと
- 評価器を高度化すること
- コード量を増やすこと
- 新規性の高い仕組みを入れること
- 1つの replay の弱点を全部消すこと

これらは、**未知 leaderboard population に対する W/D/L を改善する場合にのみ価値がある。**

## 1.2 何を最適化するか

Kaggriculture は shared market を持つ対戦ゲームなので、agent の価値は単独 farm score では決まらない。

重要なのは opponent ごとの matchup vector。

例:

```text
A > B
B > C
C > A
```

のような non-transitivity は普通にあり得る。

したがって、

```text
1体の baseline に勝てるか
```

だけで候補を決めない。

目標は概念的には、

```text
P(win | unknown active leaderboard population)
```

を高めること。

最終的には、特定 opponent への最大 margin ではなく、**強く多様な active opponent に対する勝率の広さと matchup coverage**を見る。

---

# 2. 公式 competition 条件

2026-09-18 時点で Kaggle 公式ページ / Staff clarification から確認している内容。

- Final Submission Deadline: **2026-09-30 23:59 UTC**
  - 日本時間では **2026-10-01 08:59 JST**
- 1日最大 5 submissions
- 最新 2 submissions が active
- 最新 2 submissions が final evaluation 対象
- 勝敗は 720 turns 終了時の bank coins で決まる
- rating 変動に coin margin 自体は使われず、win / loss / tie が重要
- deadline 後も約2週間 games が続き、最終 Bradley-Terry tournament が行われる
- Staff clarification:
  - team score は active 2 submissions のうち**良い方**
  - 2本目は hedge として使える
  - tie は各 side 0.5 win として扱う
  - final BT で使われる過去 episode は、**その episode の両 agent が final 時点でも active である必要がある**

Sources:

- Overview / Evaluation: https://www.kaggle.com/competitions/kaggriculture/overview
- Final BT active-agent clarification: https://www.kaggle.com/competitions/kaggriculture/discussion/732931
- Two active submissions / tie clarification: https://www.kaggle.com/competitions/kaggriculture/discussion/739410

公式条件は変更される可能性がある。

**最終提出・submission slot・evaluation に関する重要判断の直前には再確認する。**

---

# 3. Repository structure

整理後の canonical layout:

| Path | Responsibility |
| --- | --- |
| `experiments/` | immutable な numbered experiments と legacy v/h series |
| `evaluation/` | experiment-independent arena / screen / evaluation |
| `analysis/` | diagnostics / replay / economy / one-off analysis |
| `public_agents/` | external Git submodules |
| `artifacts/` | canonical current bundle と submission artifacts |
| `archive/` | superseded bundle / duplicate / historical package |
| `data/` | meta cache / downloaded data |
| `tools/` | acquisition / setup / maintenance utilities |
| `docs/` | repository / experiment / reorganization documentation |

Active elite runtime:

```text
artifacts/bundles/current/
```

詳細:

- `docs/repository_layout.md`
- `docs/reorganization_manifest.md`
- `docs/experiment_index.md`
- `docs/reorganization_verification.md`

---

# 4. Experiment 管理の絶対ルール

## 4.1 E番号は immutable

一度使った E番号の agent logic を後から別ロジックに変更しない。

新しい logic は必ず新しい番号。

```text
E18 -> E18 のまま保存
E19 -> E19 のまま保存
E20 -> E20 のまま保存
新ロジック -> E21, E22, ...
```

番号を綺麗に詰め直さない。

既存番号を再利用しない。

同じ名前の agent を中身だけ差し替えない。

## 4.2 cache / results は研究履歴

cache や result は「邪魔な一時ファイル」ではなく experiment history。

原則:

- 削除しない
- clear しない
- 別experimentと共有しない
- 結果が悪くても残す
- 新experimentには新しい cache/result を使う

cache clear を routine に行わない。

壊れていることが確認できた場合だけ、理由を明記して対処する。

## 4.3 mechanism が発動しない実験

A/B で behavior が変わらなかった場合、

```text
仮説がダメだった
```

と即断しない。

まず、

```text
実装した mechanism が本当に発動したか
```

を確認する。

mechanism が 0 回なら「効果なし」ではなく**仮説未検証**。

---

# 5. 現在の baseline / strategy families

## 5.1 E11 — Prvsiyan Frontier exact

E11 は重要な frozen baseline。

ただし**最終目的そのものでも、永続的 Current Best でもない。**

役割:

- 強い固定/tape 系 strategy family の代表
- regression を見る基準の1つ
- fallback
- 最終提出候補になり得る1本

E11 exact source:

```text
SHA256:
02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79
```

canonical wrapper:

```text
artifacts/bundles/current/agent_e11_prvsiyan_frontier.py
```

engine:

```text
1.32.7
```

2026-09-17 に submission 済み。

### E11 のローカル evidence

過去の known panel では非常に強かった。

- elite arena: 144-0-0
- fresh holdout: 96-0-0
- final confirmation:
  - 40 fresh seeds
  - both seats
  - 6 opponents
  - 480 games
  - 476-0-4
  - 99.2%

これは重要な evidence。

しかし、

**この panel が現在の leaderboard population を十分表している証拠ではない。**

特に複数 opponent に 100% 勝っている panel は candidate 間の W/D/L を分離できない。

その場合の margin 差を BT strength の証明として扱わない。

### E11 Kaggle replay evidence

確認済み 3 replay:

- vs Ankit Hemant Lade: 100,272 - 110,997
- vs Farmula One: 105,153 - 108,068
- vs woldy: 76,205 - 63,896

1W2L。

観測:

- 2区画目: D6H7
- 3区画目: D11H2
- crop mix が shop 差に対して比較的固定
- PASS 約7.2%
- SELL-turn 約34-36%

これは E11 の「弱点候補」を示すが、3試合だけで普遍的弱点と断定しない。

**losses だけでなく wins も control として比較し、複数 opponent family で再現する structural weakness かを見る。**

## 5.2 E11 の内部構造

E11 は単純な rule agent ではない。

- 13 action tapes
- 各 tape 約719 turns
- step 144 付近で初期 shop に基づき plan 選択
- movement / land / planting / worker / inventory trajectory が coordinated
- late overlay として weed repair / sales-first / topup / late investment 等

したがって、

```text
BUY_LAND だけ早める
SELLだけ遅らせる
worker 1人だけ適当に仕事させる
```

のような shallow patch は coordinated state を壊し得る。

E18-E20 はその難しさを確認するための重要な履歴として残す。

---

# 6. Kaito27 から得た重要な教訓

## 6.1 historical strength と current strength は別

Kaito27 exact は過去 leaderboard で非常に高い rating を持った frontier agent。

しかし 2026-09-18 に再提出した live trajectory は、おおむね 900 前後へ向かう挙動が観測された。

live rating は暫定であり final BT そのものではない。

それでも、

**「一度 frontier だった固定routeを永久の正解とみなしてはいけない」**

という実例として重要。

Kaito27 raw source:

```text
SHA256:
f48c21166eac68d1b05a401f04f94a2eb6154e65415af64893672365ff33c7b8
```

## 6.2 Kaito27 live replay 3試合

このチャットで解析した3試合:

| Opponent | Kaito27 | Opponent | Margin |
| --- | ---: | ---: | ---: |
| Focus | 64,950 | 69,331 | -4,381 |
| Ztr0 | 76,884 | 68,411 | +8,473 |
| Trip Meiners | 54,421 | 54,897 | -476 |

Kaito27 自身は3試合で unit trajectory がほぼ完全固定。

共通:

- land: step 161 / 241
- WHEAT seed: 148
- STRAWBERRY: 37
- MELON: 19
- final livestock: 9 cow / 4 sheep

Focus と Trip Meiners は互いに unit action が **716/720 turns 一致**。

Kaito27 とも約 500/720 turns が一致し、最初の大きな分岐は step 125 付近。

一方 Ztr0 はほぼ別系統で、Kaito27 が +8,473 で勝った。

重要な示唆:

- Kaito27 が全体として完全に弱い、と3試合からは言えない
- 同系統 opening / route family の新しい continuation に競り負けている可能性がある
- shared market 上で似た agent 同士が同じ商品を同時に売ることで matchup が変わる
- strategy lineage と population composition が strength に大きく影響する

したがって、

```text
昔強かったagentを捨てる
```

でも、

```text
昔強かったから守り続ける
```

でもない。

**現在 population における matchup vector を再評価する。**

---

# 7. 最新 top meta から見えること

`public_agents/lonespear/daily_meta.py --top 10` による 2026-09-16 snapshot:

```text
top Elo:    3172
median Elo: 3039
```

top 10 episodes = 20 player-games の aggregate:

```text
productive %  53.1%
movement %    43.8%
PASS %         3.1%

avg seeds/player:
WHEAT       154
CARROT       46
STRAWBERRY   37
MELON        15
TOMATO       15

ending money median:
123,149
```

final farm は 3-4 quadrants、crop / livestock mix がかなり多様。

この selected top episode sample から、

```text
唯一の固定 farm composition が正解
```

とは言えない。

一方、過去に解析した Majkel1337 / DSM top replays では、

- opening backbone は比較的固定
- 3Q を D9H6 前後までに完成
- MELON は backbone 的
- CARROT / STRAWBERRY / TOMATO は shop により大きく変化
- sales style は agent によりかなり異なる

という構造が見えた。

これは有力な structural clue だが、selected replay sample なので universal rule としてハードコードしない。

---

# 8. 過去 experiment と現在の解釈

詳細な E1-E20 一覧は:

```text
docs/experiment_index.md
```

ここでは今後の判断に重要なものだけ書く。

## E14-E16 — simple selling guards

- E14 MILK guard
- E15 FERTILIZER guard
- E16 anti-clone guard

E11 に simple overlay を足したが悪化。

教訓:

**selling は production / inventory / demand と切り離して単独最適化しない。**

## E17 — idle-hand rescue

E11 の PASS を活用する WATER rescue。

direct / holdout が完全一致。

実質 no-op。

教訓:

```text
PASS が多い
=> 何か作業を足せば強い
```

ではない。

## E18 — late-shop tape switch

late shop を見て既存 E11 tape へ途中switch。

telemetry:

```text
new_shop_events=86
route_candidates=46
safe_switches=2
unsafe_rejects=40
same_plan=4
no_supported_pair=40
```

既存 coordinated tape 間の途中switchは state mismatch が大きい。

この方式は新しい根拠なく再試行しない。

## E19 — early SW prebuild

E11 の予定している SW strawberry cells を早く使う狙い。

初期版は mechanism が発動しなかった。

後の版では early land は発動したが、strawberry seed がなく preplant が動かないなど、仮説と実装が一致していなかった。

E番号の immutable rule が確立する前に同番号内で変更が入った歴史がある。

**今後は絶対に繰り返さない。**

## E20 — early 3Q + native strawberry seed prefetch

mechanism は明確に発動。

主な telemetry:

```text
early_land_activated=16
seed_prefetch_activated=32
preplants=28
waters=72
```

E11 direct:

```text
0-0-16
```

旧 strong holdouts では E11/E20 とも全勝する opponent が多かった。

過去には「E11に16敗」「margin低下」を理由に reject とした。

### 現在の再解釈

E20 が**未知 leaderboard population でも弱いことは、この結果だけでは証明されていない。**

理由:

- E11 direct は1 matchup
- holdout panel が saturated
- margin は BT objective ではない
- E20 は明確に別behaviorを発動している

したがって historical status は残すが、

```text
E11に負けた = globalに弱い
```

という一般則には使わない。

明確に崩壊した agent と、単に E11 matchup が悪かった candidate は区別する。

---

# 9. 現在の開発原則

ここは最重要。

## 9.1 E11 direct H2H を gate にしない

以前:

```text
candidate
  ↓
E11に負ける
  ↓
reject
```

としていた。

これは現在の方針ではない。

E11 は opponent family の1つ。

candidate が E11 に負けても、他の active population に広く勝てれば最終 BT が高い可能性がある。

逆に E11 に勝っても、他familyに崩壊すれば価値は低い。

## 9.2 mean margin を目的化しない

coin difference は diagnostic。

特に、

```text
E11 16-0
candidate 16-0
```

の opponent に対して、

```text
+20k vs +15k
```

だから E11 の方が BT で強い、とは言わない。

W/D/L が飽和している panel は discriminator として弱い。

## 9.3 評価は目的ではない

何回も、

```text
評価する
→ panelが弱い
→ 評価器を直す
→ また評価する
```

だけを繰り返さない。

evaluation framework は agent を強くするための道具。

十分な評価原則が分かったら、実際の strategy exploration へ戻る。

## 9.4 Adaptivity 自体を目的にしない

```text
adaptiveにした
```

には価値がない。

adaptive behavior が unknown population への勝率を上げる場合だけ価値がある。

固定routeがまだ強い領域もあり得る。

## 9.5 「E11の負け条件を全部消す」ことも目的ではない

E11 の known losses を全部 patch すると known opponents に overfit する可能性がある。

見るべきなのは、

**複数 opponent families / market states で再現する structural weakness。**

loss だけでなく win replay も control として解析する。

## 9.6 micro-patch 無限ループを避ける

以前のように、

```text
1箇所変更
→ 16 games
→ また1箇所変更
→ 16 games
...
```

を主経路にしない。

diagnostic が十分集まったら、意味の違う complete strategy family を**batchで複数作る**。

目安:

```text
3-8 candidates
```

を同じ条件で screen し、悪い branch をまとめて落とす。

survivor 1-2 family だけを深掘りする。

## 9.7 feature ではなく strategy system を見る

top replay から、

```text
3Qが早い
SELLが多い
TOMATOが多い
```

という feature 1個だけをコピーしない。

重要なのは、

```text
opening
capital allocation
land timing
worker routing
crop mix
livestock
production
inventory
selling
market pressure
```

がどう連動しているか。

強い agent から盗むべきなのは isolated trick より**system**。

## 9.8 baseline を神格化しない

E11 も Kaito27 も strategy family の1本。

新しい public frontier / current leaderboard behavior が明らかに強いなら baseline を更新してよい。

ただし historical baseline は消さない。

## 9.9 local evaluation と leaderboard evidence を役割分担する

local:

- same seeds
- both seats
- controlled counterfactual
- reproducibility
- crash detection
- mechanism verification

leaderboard:

- actual unknown population
- real shared-market interactions
- current meta
- final objective に最も近い evidence

local だけで真の population strength を証明しようとしない。

leaderboard だけで noisy な score chase もしない。

---

# 10. 推奨 evaluation protocol

candidate 間の比較では、可能な限り以下を守る。

1. same seeds
2. both seats
3. strong + diverse opponent families
4. W/D/L を primary
5. matchup ごとに見る
6. margin は diagnostic
7. tuning seeds を holdout に再利用しない
8. broken/error candidate を win-loss aggregate に混ぜない
9. mechanism telemetry を取る
10. panel が全員 100% なら、その panel で ranking を続けない

local BT を計算する場合も、panel composition が偏っていれば結果も偏る。

数字が出ることと、意味のある推定であることは別。

---

# 11. Strategy portfolio の考え方

Kaggle Staff clarification では、final team score は active 2 submissions のうち良い方。

したがって final pair は、単純に同じ agent の微差2本にする必要はない。

理想:

```text
Agent A:
broad generalist / robust

Agent B:
Aと failure mode が相関しにくい complement / hedge
```

A/B がほぼ同じ lineage なら、同じ opponent に両方負ける可能性が高い。

2本目は「弱い奇策」ではなく、**十分強く、matchup coverage が異なる戦略**を狙う。

final直前は新feature開発より、

- crash
- package integrity
- import
- runtime
- validation episode
- exact artifact hash

を優先する。

---

# 12. 現在考えるべき strategy families

これは固定された正解ではなく、現在の探索方向。

## Family A — robust backbone

- 強い opening
- 早い資本回転
- 3Q を適切な時期に使用
- market/shop state に応じた midgame allocation
- fragile な opponent-specific tricks を減らす

## Family B — market aggressive

- 生産自体も強い
- shared market の timing / inventory pressure を強く利用
- DSM 的な高頻度 small sells も参考にするが、そのままコピーしない
- opponent lineage / seat / collision への耐性を見る

## Family C — hedge / different production mix

- Family A と failure mode を共有しにくい
- crop / livestock / sale mix が意味のあるレベルで異なる
- 同じ fixed continuation の clone を2本作らない

この3 family は「adaptive / non-adaptive」の分類ではない。

**unknown population に異なる勝ち筋を持つか**で分類する。

---

# 13. Current meta を見る方法

新しい agent を作る前に、定期的に frontier を再確認する。

見るもの:

- current top episodes
- public notebooks / public agents
- recent discussions
- latest strong source code
- replay action fingerprints
- strategy lineage
- shop/crop/livestock/sell patterns
- active population の clone / copy 増加

特に、

```text
昔 strong だった public route
```

が大量コピーされると、同系統 continuation 同士の競争や shared-market collision により value が変わり得る。

frontier scan は「新しいものを見つけること」自体が目的ではない。

**今どの strategy region が active population で有効か把握するために行う。**

---

# 14. 次にやること

## Immediate

**Focus / Trip Meiners 系の lineage を特定する。**

やること:

1. Kaito27 vs Focus / Trip の action fingerprint を保存
2. 手元の Kaito48 / Rayk / Boatlee / Prvsiyan / その他 public agents と照合
3. exact match / nearest lineage を特定
4. Kaito27 から何が変わった continuation なのか差分解析
5. 2026-09-16 current top episodes に同系統が存在するか確認
6. E11 family と比較し、strategy systems の違いを整理

## その次

frontier map ができたら、

**新しい complete candidate を複数まとめて作る。**

E番号は新規番号を使う。

注意:

`evaluation/population_arena_v1/arena.py` に E21 参照が残っているが、現時点では実体 E21 は存在しない。

この stale reference を「E21が既にある」と解釈しない。

実際に新しい agent を作った時点で、その experiment number を確定する。

## その後

同じ discriminating population panel で batch evaluation。

E11 H2H は diagnostic の1つに留める。

survivor を leaderboard に出し、actual active population evidence を取る。

締切前に generalist + complement の2本へ収束させる。

---

# 15. ChatGPT / Codex 作業規約

## 15.1 毎回ゴールから逆算する

チャットが長くなると、直前の局所課題を目的だと誤認しやすい。

各 major decision で一度、

```text
これは最終 BT を上げるために何を確認しているのか？
```

を確認する。

説明できない作業は止めるか優先度を下げる。

## 15.2 ユーザーに「次は？」と聞かせない

Kaggriculture の分析結果を返すときは、基本的に最後に以下を含める。

```text
今回わかったこと
判断
次にやること
```

ユーザーが毎回「次は？」と聞かなくてよい状態にする。

## 15.3 同じ指摘を繰り返させない

ユーザーから受けた重要な correction は、その場だけで謝って終わらない。

一般化できるなら README の原則へ昇格する。

例:

- E11 direct を gate にしない
- cache をroutine clearしない
- E番号を使い回さない
- 評価を目的化しない
- adaptivityを目的化しない
- micro-patchを延々繰り返さない
- final objective から外れたらメタに戻る

## 15.4 不要な確認質問をしない

repo / README / current conversation に答えがあることを再質問しない。

重いtaskでも、必要情報が十分なら best effort で進める。

## 15.5 GitHub

この ChatGPT プロジェクトでは GitHub を**読み取り用**として扱う。

勝手に GitHub へ write / commit / push しようとしない。

変更ファイルが必要な場合はローカル artifact を作り、ユーザーが確認・commit/pushする。

Codex がユーザーのローカル repo 上で明示的に作業している場合は、その task の指示に従う。

---

# 16. Historical agent series

詳細は `docs/experiment_index.md` を正とする。

## Legacy v-series

主な流れ:

- v4 stable melon baseline
- v5 seed prefetch: rejected
- v6 dynamic melon: rejected
- v7 simple diversification: rejected
- v8 livestock rewrite: collapse
- v9 livestock stabilization
- v10 8 cows + 6 sheep + 8 hands
- v11 market-aware selling
- v12 Seyamalam public strong baseline
- v15 Kaito48 family

## h-series

- h1 overhiring collapse
- h2 capital allocation
- h3 strong vs v11 but weak vs v15
- h4 weak vs h3 / v15

重要な教訓:

**非推移性は古い自作seriesでも既に観測されている。**

1本の baseline に対する改善を general strength と同一視しない。

---

# 17. Learned policy / RL の位置づけ

RL / learned policy を使うこと自体は目的ではない。

もし使うなら、720-turn end-to-end PPO にいきなり飛ばず、

- strong low-level executor
- macro decision
- counterfactual rollouts
- state-conditioned choice

のように、改善理由を追いやすい構造を優先する。

候補 state:

- day / hour
- cash / cash diff
- shops
- market price / inventory / trend
- own crops / seeds / inventory
- livestock
- land
- workers
- opponent visible state

候補 macro actions:

- land timing
- crop emphasis
- livestock allocation
- worker allocation
- sell / hold mode

学習 objective も最終的には W/D/L と population performance に結びつける。

---

# 18. 判断を変えるときのルール

過去READMEに書いた方針だからという理由で守り続けない。

新しい evidence が出たら判断を更新する。

ただし過去の結果を消さない。

例:

```text
Past:
E20はE11に0-16なのでreject

Current interpretation:
E11 direct lossだけではglobal rejectを証明しない
```

このように、

**historical decision と current policy を両方残す。**

これにより後で、

```text
なぜ当時そう判断したか
何が分かって方針が変わったか
```

を追えるようにする。

---

# 19. README 更新チェックリスト

重要な作業区切りで README 更新を検討する。

更新対象:

- 新experimentを実行した
- candidateのstatusが変わった
- current frontierの理解が変わった
- Kaggle公式evaluation条件が変わった
- baselineの位置づけが変わった
- ユーザーから再発防止すべき重要な指摘があった
- 「次の道筋」が変わった
- 過去の判断を覆す evidence が出た

更新しないもの:

- 一時的な思いつき
- まだ mechanism 未確認の仮説を確定事項として
- 1 replay だけの現象を普遍則として
- live leaderboard の瞬間値を恒久的な strength として

---

# 20. 現在の要約

2026-09-18 時点。

- 最終目的: unknown active population に対する Bradley-Terry 最大化
- E11: strong frozen baseline / strategy family の1本。神格化しない
- Kaito27: historical frontier。current populationでは価値が変化した可能性
- shared market / non-transitivity / strategy lineage を重視
- margin は補助
- E11 direct は gate ではない
- saturated panel で margin ranking しない
- evaluation framework を目的化しない
- adaptivityを目的化しない
- known loss patchingを universal robustness と同一視しない
- wins も control として structural weakness を確認する
- micro-patch loop より complete strategy families を batch探索
- E番号 immutable
- cache/results preserve
- final 2 submissions は generalist + complement を狙う
- 直近の仕事は Focus / Trip lineage identification と current frontier map
- その後、意味の違う complete candidates をまとめて実装する

---

## 最後の原則

**本来の目的を忘れないこと。**

局所的には正しそうな作業でも、最終 Bradley-Terry を上げる道筋に接続していなければ優先しない。

「E11を改善すること」も「adaptive agentを作ること」も「最新topを真似ること」も目的ではない。

目的は、

> **最終時点で active な未知・多様な相手群に対して勝つ確率を最大化し、Kaggriculture の最終 Bradley-Terry 評価を最大化すること。**

そのために baseline、public frontier、replay analysis、local arena、leaderboard、複数 strategy families を使う。
