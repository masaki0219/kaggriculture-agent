Kaggriculture Agent

Kaggle の Featured Simulation Competition Kaggriculture 用エージェントを改善していくリポジトリです。

Competition: https://www.kaggle.com/competitions/kaggriculture

この README は単なるプロジェクト紹介ではなく、ChatGPT との複数チャットにまたがる 共有メモ・実験記録・引き継ぎ書 として使用します。

重要

新しいチャットを始めたら、ChatGPT は過去チャットの記憶より先に、この README と GitHub 上の最新コードを確認すること。

README / 最新コードと会話メモリが食い違う場合は、GitHub を優先する。

ただし、README 更新後にこのチャット内で新しい実験結果が出た場合は、その最新結果を README に反映すること。

1. 目的

残り期間で Kaggriculture エージェントをできるだけ強くする。

最終目的は Leaderboard 上の Bradley-Terry 評価を最大化すること。

単純な reward の大きさ、平均 margin、特定 opponent への圧勝、自作度の高さは最終目的ではない。
強く多様な未知 opponent に勝つ確率を高めることを優先する。

開発サイクルは以下を基本とする。

仮説を立てる

変更を実装する

Current Best と同一 seed・両席で比較する

W / D / L と holdout 勝率を確認する

良い変更だけ残す

結果と判断理由を README に残す

2. 競技について重要なこと

Competition: Kaggriculture

提出締切: 2026-10-01

最終評価: Bradley-Terry 系の pairwise 評価

reward magnitude より勝敗を重視

shared market があるため matchup effect / non-transitivity を前提にする

重要判断の前には Kaggle 公式ルール・evaluation・submission 条件を再確認する

ローカル対戦はあくまで proxy。未知の leaderboard population に対する強さが最終対象

3. Current Best

E11 = Prvsiyan Frontier exact

2026-09-17 時点のローカル Current Best。

E11 は ChatGPT がゼロから作った戦略ではない。公開されている Prvsiyan Frontier / Kaggriculture Frontier | The Moon Counts Melons の公開エージェントを、そのままローカル benchmark で使用できるよう wrapper 化したもの。

戦略本体: Prvsiyan の公開 agent

ローカル名 E11 / wrapper / benchmark: このプロジェクト側

exact source SHA256: 02b1fee4b0e48027d4d3baeeb99518346f4fc5a14724cdb202d09a3425b15a79

source bytes: 89193

submission archive: submission_e11.tar.gz

archive SHA256: f0e698738d95ad3822d3128c814aeb8548d8b58e2e156bd1a3865a376ccdc1ad

engine: 1.32.7

E11 自体は 凍結 baseline として扱う。新しい変更は別 candidate として作成し、E11 exact を上書きしない。

Kaggle 提出

2026-09-17 に submission_e11.tar.gz として提出。

Status: Complete

Description: E11 Prvsiyan Frontier exact

提出直後に Submissions ページで 600.0 と表示された

その後 leaderboard 上では 1687.3 / rank 2095 を確認した時点がある

600.0 は初期の表示状態で、E11 の固定的な最終実力値ではない。Leaderboard rating は対戦の蓄積で動くため、ローカル勝率や mean margin と同じ尺度として扱わない。

4. E11 を Current Best とした根拠

Elite round robin

seed 1000 から 8 seeds、両席 = 16 games / pair。

Matchup

E11 W-D-L

Mean margin

Boatlee v29

16-0-0

+18,729

Kaito v43 current

16-0-0

+20,093

Kaito v27 current

16-0-0

+37,721

Kaito v27 + guard

16-0-0

+37,795

v15 / Kaito v48

16-0-0

+20,034

qeinstein champion

16-0-0

+17,522

qeinstein candidate7

16-0-0

+8,557

qeinstein portfolio

16-0-0

+19,303

この arena では 144-0-0。

Fresh holdout: seeds 10000-10011

24 games / opponent。

Opponent

E11 W-D-L

Mean margin

Boatlee v29

24-0-0

+24,984

v15 / Kaito v48

24-0-0

+24,301

qeinstein champion

24-0-0

+23,727

qeinstein candidate7

24-0-0

+9,210

合計 96-0-0。

Final confirmation: seeds 20000-20039

40 fresh seeds × 両席 × 6 opponents = 480 games。

Opponent

E11 W-D-L

Score

Mean margin

Boatlee v29

80-0-0

100.0%

+21,400

Kaito v43 current

80-0-0

100.0%

+19,991

v15 / Kaito v48

80-0-0

100.0%

+20,174

qeinstein champion

80-0-0

100.0%

+21,297

qeinstein candidate7

80-0-0

100.0%

+10,649

qeinstein portfolio

76-0-4

95.0%

+20,414

Total: 476-0-4 / 99.2% / mean margin +18,988。

5. Kaggle 公開リプレイから見えたこと

5.1 上位層 6リプレイ / 12 player-runs

上位公開リプレイから見えた最重要パターンは、opening はかなり固定しつつ、midgame の crop / livestock / sales を town shop 構成に応じて変えていること。

観測した Majkel1337 / DSM では、

12/12 が最終的に 3 quadrants

2区画目は D6H6 前後

3区画目は D9H6 前後

MELON はおおむね固定

CARROT / STRAWBERRY / TOMATO は seed / shop 構成ごとに大きく変動

DSM はほぼ毎turn SELL

Majkel は SELL するturnが約 37-41%

SELL方法は一意ではない

early cash は積極的に再投資

したがって「DSM の SELL 方法だけコピーする」のような単独移植は根拠が弱い。

公開リプレイは少数の selected games なので、傾向をそのまま一般化せず、ローカル A/B で因果確認する。

5.2 E11 の Kaggle 公開リプレイ 3試合

結果:

Episode

Opponent

E11

Opponent

Margin

109935536

Ankit Hemant Lade

100,272

110,997

-10,725

109955997

Farmula One

105,153

108,068

-2,915

109948968

woldy

76,205

63,896

+12,309

合計 1W2L。mean margin は約 -444。

共通パターン:

2区画目: 3試合とも D6H7

3区画目: 3試合とも D11H2

3試合すべて MELON 12

WHEAT 163

STRAWBERRY 33

CARROT 31

TOMATO は 0 / 0 / 10

PASS 比率: 約 6-8%、平均約 7.2%

SELL-turn 比率: 約 34-36%

最終 hands: 約 11-13

shop 構成は大きく違うのに、植付け構成がほぼ同じ。

したがって E11 の opening 自体が弱いというより、固定 script を midgame まで引っ張りすぎている可能性が高い。

5.3 現在の優先仮説

第3区画が上位観測例より約44 turns 遅い

D9-D11 の資本投入・土地利用が遅い

worker routing / PASS が多い

post-Day9 の生産が shop demand に十分適応していない

SELL logic は production と分離して単独最適化しない

4th quadrant は優先度低。まず 3Q の使い切り

6. E11 の内部構造について分かったこと

E11 は単純な「if 文で Day11 に BUY_LAND」ではない。

内部では _POLICY.tapes[state.plan] のような runtime policy tape / precomputed action tape を使用している。

確認済み事項:

13本の action tape がある

各 tape は約719 turns の coordinated action sequence

shop 情報に応じて plan を選択する

core plan の選択は主に step 144 時点で最初の2店舗を使う

native の土地購入・移動・植付け・worker 行動が tape 内で一体化している

raw Python 上の BUY_LAND 文字列だけを変更しても native D6 / D11 land schedule は変わらない

第3区画購入付近は HIRE / BUY_LAND / livestock / fertilizer / strawberry 系の処理と結びついた開発ブロック

late overlay として weed repair、sales-first、topup、late investment などが存在する

重要な意味:

BUY_LAND だけ前倒しする浅い patch は危険。

土地を早く開けても、worker の移動・植付け・watering が D11 前提のままなら、資本だけ寝かせる可能性がある。

一方、公式 engine 上では farmer / hands は日単位でリセットされるため、既存 tape の worker index を壊さずに「その日だけ extra hand を追加して補助作業をさせる」方向には検証価値がある。

7. E11 派生実験

E14: MILK guard

E11 vs E14 = 19-0-5。

不採用。

E15: FERTILIZER guard

E11 vs E15 = 22-0-2。

不採用。

E16: anti-clone guard

E11 vs E16 = 22-0-2。

不採用。

E17: idle-hand crop rescue

目的:

E11 の PASS が多いという観測から、native tape を崩さず、PASS 中の hand に短い WATER rescue をさせる。

設計:

Day6-17

16-21時

hand のみ

E11 の final action が PASS

native tape も往復期間ずっと PASS

weed repair queue がない

inventory を持っていない

consecutive_unwatered >= 1

最大7 commands

元の位置へ戻る

1日最大2回

screening:

E17 vs E11: 0-10-0 meanMargin=+0

Holdouts:

e2_boatlee29         E11=10-0-0 +21554   E17=10-0-0 +21554
v15_kaito48          E11=10-0-0 +18462   E17=10-0-0 +18462
qeinstein_champion   E11=10-0-0 +21690   E17=10-0-0 +21690
qeinstein_candidate7 E11=10-0-0 +14600   E17=10-0-0 +14600

判断: 不採用 / no-op。

理由:

direct も holdout も完全一致

今回の条件では実質的に terminal outcome を変えない

「PASS が多い = 任意の補助作業を足せば強くなる」という仮説は弱い

20 seeds への拡大はしない。

E18: late-shop tape switch

目的:

後発 shop の出現後に、別 plan の tape へ安全に切り替えることで、E11 の固定 midgame を改善できないか検証。

実行:

python experiments/e018_late_shop/arena.py --seeds 8 --seed-start 31000

結果:

E18 vs E11: 0-14-2 meanMargin=-117

telemetry:
new_shop_events=86
route_candidates=46
safe_switches=2
unsafe_rejects=40
same_plan=4
no_supported_pair=40

Strong holdouts:

Opponent

E11

E18

備考

e2_boatlee29

16-0-0 / +23194

16-0-0 / +23194

switches=0

v15_kaito48

16-0-0 / +21965

16-0-0 / +21961

switches=2

qeinstein_champion

16-0-0 / +22109

16-0-0 / +22109

switches=0

qeinstein_candidate7

16-0-0 / +17504

16-0-0 / +17663

switches=2

判断: 即不採用。

理由:

E11 直接比較で 2敗

46 route candidates に対し safe switch は 2回だけ

後発 shop への適応という発想より、「途中で既存 tape を別 plan に差し替える」という実装方式がほぼ成立しない

plan ごとに worker position / farm geometry / inventory trajectory が既に分岐しているため、late switch は state mismatch を起こしやすい

この方向は再試行しない。
次に shop-aware adaptation を行うなら、tape switch ではない方式を使う。

8. E19: early SW prebuild

Status: 次の A/B 候補。未 promotion。

Files:

experiments/e019_early_sw/agent.py

experiments/e019_early_sw/arena.py

狙い

E11 が D11 前後に行う第3区画 SW 開発を、D9-D10 に部分的に先行させる。

E18 のように plan 全体を切り替えず、現在選ばれている E11 tape を維持したまま、その tape が後で使う予定の SW strawberry cell を先行利用する。

基本設計

E11 exact を parent とする

選択中 tape を解析

D11 に E11 自身が SW へ STRAWBERRY を植える予定の target cell を最大2個取得

cash / seed / market slot が安全なら D9-D10 に第3区画を前倒し購入

extra daily hand 1人で target cell へ移動・PLANT・WATER

E11 の既存 hand の index / command は変更しない

D11 以降は native E11 へ戻す

既に3区画なら、重複する pre-D18 native BUY_LAND のみ抑制

late 4th-land logic は触らない

追加の STRAWBERRY seed は原則買わず、既存 seed を先に使う

E11 自身が後で使う予定の cell だけを触る

初期 screening

python experiments/e019_early_sw/arena.py --seeds 8 --seed-start 32000

見る telemetry:

eligible_games

early_land_requests

early_land_activated

activation_failures

extra_hires

preplants

waters

native_land_suppressed

no_targets

no_seed

cash_waits

market_full

Promotion 条件

E11 direct で W/D/L regression がない

mechanism が実際に発動している

strong holdouts でも非劣化

その後 fresh seeds / opponent panel を拡大

mean margin の改善だけでは promotion しない

9. 主要候補の整理

E2 Boatlee v29: 強いが E11 に 0-16、final confirmation でも 0-80

E6 Boatlee + collision guard: E2 に 0-16。不採用

E9 Boatlee + tomato approximation: Kaito v58 相手に 4-12。不採用

E10 Kaito v27 current: E11 に 0-16。不採用

E12 Kaito v43 current: E11 に 0-16、final confirmation でも 0-80

E13 Kaito v27 + guard: E11 に 0-16。不採用

10. 旧自作系列

v4: stable melon baseline

v5: seed prefetch → 4-80-16 vs v4。不採用

v6: dynamic melon → 1-99。不採用

v7: simple diversification → 1-99。不採用

v8: first livestock rewrite → 0-20。崩壊

v9: stabilized livestock → 13-7 vs v8

v10: 8 cows + 6 sheep + 8 hands → 20-0 vs v9

v11: market-aware selling → 16-4 vs v10

v12: Seyamalam public strong baseline → 20-0 vs v11

v15: Kaito v48 wrapper 系統

h-series:

h1: overhiring で崩壊

h2: capital allocation 問題

h3: v11 に 9-0-1、v15 に 0-10

h4: h3 に 0-10、v15 に 0-10

Decision: h-series は主経路として停止。

11. Arena / 評価設計についての注意

過去の arena v1 では discovery / screening 設計に問題があった。

162 unique agents を見つけた

duplicate 103

panel は E11 + reacting aurax / evgen / market smart + sub-009-moev2

非panel候補 157体が screen で全て 0%

top4 選択が実質 discovery order 依存になった

Kaito58 / ShapeTop10 など重要候補を正しく比較できていなかった

したがって arena v1 の「E11 が 162候補すべてより最強」という解釈はしない。

E11 がその stage2 の 8 opponent に 100% だった事実は使えるが、全候補に対する優越性の証明ではない。

以後:

opponent discovery と ranking を分離する

broken / duplicate を除外

diverse strong panel を明示的に作る

fresh seeds を使う

both seats を使う

tuning seeds を holdout に再利用しない

12. 重要な戦略知見

Common-pool market

Kaggriculture は単独 farm 最適化だけではなく、2人が同じ market inventory / price dynamics を共有する common-pool game。

同じ premium item を同時刻に大量 sell すると自己衝突が起きるため、将来的な frontier は

strong farm program + opponent-aware market timing

になる可能性がある。

ただし E11 exact に単純な sell-delay overlay を重ねた E14-E16 はすべて悪化した。

Crop demand substitution

公開実験では strawberry oversupply と tomato undersupply を利用した置換が有効なケースがある。

ただし独自近似 E9 は悪化したため、「方向性が正しそう」というだけで再実装しない。元実装・game dynamics・counterfactual を確認する。

Fixed opening + adaptive midgame

上位公開リプレイから現在もっとも有力な構造仮説。

opening は安定した backbone を持つ

midgame から shop / market / inventory に応じて資源配分を変える

E11 は opening が弱いというより、適応へ切り替わるタイミングが遅い、または適応幅が小さい可能性がある。

SELL は production とセットで考える

上位例でも DSM と Majkel1337 の SELL 方針は大きく違う。

したがって、

SELL 頻度だけ

SELL delay だけ

threshold だけ

を独立にコピーしない。

production / inventory / shop demand とセットで評価する。

13. Learned policy / RL を使う場合

720-turn end-to-end PPO をいきなりやるより、E11 を low-level executor として残し、macro decision だけ学習させる方向を優先する。

候補 state:

day / hour

cash / cash difference

unlocked shops

market prices / inventory / trends

own seeds / crops / inventory

livestock

land count

worker count

opponent visible crop / livestock / land

候補 macro actions:

land timing

crop emphasis

livestock allocation

worker target

sell / hold mode

まずは discrete counterfactual rollout を作り、

Q(s,a) = P(win | s,a)

を LightGBM / XGBoost 等で学習する方が検証しやすい。

最終 reward は W/D/L を基準とする。

end-to-end PPO / hierarchical PPO は、macro action の明確なシグナルが出てから。

14. 現在の実験ルール

旧版への勝利だけでは promotion しない

同じ seed、両席で比較

tuning に使った seed は holdout として再利用しない

まず少数 seed で screening

direct E11 comparison で敗北が出る改造は原則即 reject

通過候補だけ 100-500 games に拡大

W / D / L を最優先

mean reward / mean margin は補助指標

broken candidate は勝敗に混ぜない

mechanism が発動していない A/B は「効果なし」ではなく「仮説未検証」と扱う

一度明確に reject した方向を理由なく再試行しない

E11 exact を直接上書きしない

15. 次にやること

P0: E11 exact を Current Best として維持

E19 が明確に勝つまでは E11 を差し替えない。

P1: E19 early SW prebuild を screening

python experiments/e019_early_sw/arena.py --seeds 8 --seed-start 32000

まず mechanism 発動と direct W/D/L を見る。

early_land_activated == 0
→ trigger / implementation の問題。仮説未検証。

activation あり + direct loss
→ E19 reject。

activation あり + non-regression
→ strong holdouts、fresh seeds へ拡大。

P2: Kaggle 実リプレイを増やす

E11 の live opponent に対する losses / close games を集める。

特に確認するもの:

3rd land timing

shop composition と crop allocation

PASS / routing

market sell timing

opponent-specific failure mode

P3: post-Day9 adaptive allocation

E19 の land hypothesis が通るか否かを確認した後、shop-aware crop allocation を tape switch ではない方式で試す。

候補:

current tape を維持した局所 production override

macro policy

counterfactual rollout による action choice

P4: 公開 frontier の継続探索

締切まで E11 より新しい / 強い公開 agent が出ていないか監視する。

16. Current Best summary

Current Best: E11 / Prvsiyan Frontier exact

Status: Frozen public-frontier baseline / submitted

Local evidence:

elite arena: 144-0-0

fresh holdout: 96-0-0

final confirmation: 476-0-4

final confirmation score: 99.2%

mean margin: +18,988

Kaggle submission:

file: submission_e11.tar.gz

status: Complete

initial displayed score: 600.0

later observed leaderboard rating: 1687.3

later observed rank: 2095

submitted: 2026-09-17

Latest experiments:

E14 MILK guard: REJECT

E15 FERTILIZER guard: REJECT

E16 anti-clone guard: REJECT

E17 idle-hand rescue: REJECT / no-op

E18 late-shop switch: REJECT (0-14-2 vs E11)

E19 early SW prebuild: NEXT TEST / not promoted

原則

ここから先も本来の目的を忘れないこと。

「自作であること」「変更量が多いこと」「平均 reward が高いこと」「E11 と違うこと」ではなく、

Kaggriculture の最終 Bradley-Terry を最大化することが目的。

E11 を壊してまで独自性を足さない。

公開 artifact を使う場合はライセンス・provenance・submission conditions を確認する。

新しい変更は必ず E11 exact に対する再現可能な W/D/L 改善で正当化する。

githubに書き込もうとするな。
