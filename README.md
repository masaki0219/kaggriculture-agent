Kaggle の Featured Simulation Competition Kaggriculture 用エージェントを改善していくリポジトリです。

Competition: https://www.kaggle.com/competitions/kaggriculture

この README は単なるプロジェクト紹介ではなく、ChatGPT との複数チャットにまたがる共有メモ・実験記録・引き継ぎ書として使用します。

重要

新しいチャットを始めたら、ChatGPT は過去チャットの記憶より先に、この README と GitHub 上の最新コードを確認すること。

README / 最新コードと会話メモリが食い違う場合は、GitHub を優先する。

1. 目的

残り期間で Kaggriculture エージェントをできるだけ強くする。

最終目的は Leaderboard 上の Bradley-Terry 評価を最大化すること。単純な reward の大きさや、特定 opponent への平均 margin ではなく、強く多様な未知 opponent に勝つ確率を優先する。

開発サイクルは次を基本とする。

仮説を立てる

変更を実装する

ローカル対戦で Current Best と比較する

W / D / L と holdout 勝率を確認する

良い変更だけ残す

結果と判断理由を README に残す

2. 競技について重要なこと

Competition: Kaggriculture

提出締切: 2026-10-01

最終評価は Bradley-Terry

reward magnitude より勝率を重視

重要判断の前には Kaggle 公式ルール・evaluation・submission条件を再確認する

3. Current Best

E11 = Prvsiyan Frontier exact

2026-09-17 時点のローカル Current Best。

E11 は ChatGPT がゼロから作った戦略ではない。公開されている Prvsiyan Frontier / Kaggriculture Frontier | The Moon Counts Melons の現行公開エージェントを、そのままローカル benchmark で使用できるよう wrapper 化したもの。

戦略本体: Prvsiyan の公開 agent

E11 というローカル名、wrapper、benchmark: ChatGPT 側

E14/E15/E16: E11 に独自差分を重ねた派生。すべて不採用

Kaggle 提出

2026-09-17 に submission_e11.tar.gz として提出。

Status: Complete

Description: E11 Prvsiyan Frontier exact

Kaggle displayed Score: 600.0

この 600.0 は Kaggle の Submissions ページに表示された提出スコアであり、ローカル benchmark の勝率や BT-like rating と同じ尺度ではない。

4. E11 を Current Best とした根拠

Elite round robin

seed 1000 から 8 seeds、両席 = 16 games / pair。

Matchup

E11 W-D-L

Mean margin

vs Boatlee v29

16-0-0

+18,729

vs Kaito v43 current

16-0-0

+20,093

vs Kaito v27 current

16-0-0

+37,721

vs Kaito v27 + guard

16-0-0

+37,795

vs v15 / Kaito v48

16-0-0

+20,034

vs qeinstein champion

16-0-0

+17,522

vs qeinstein candidate7

16-0-0

+8,557

vs qeinstein portfolio

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

Total: 476-0-4, score 99.2%, mean margin +18,988。

5. E11 派生実験

E14: MILK guard

E11 vs E14 = 19-0-5。不採用。

E15: FERTILIZER guard

E11 vs E15 = 22-0-2。不採用。

E16: anti-clone guard

E11 vs E16 = 22-0-2。不採用。

結論: 現時点では E11 exact を触らない方が強い。

6. 主要候補の整理

E2 Boatlee v29: 強いが E11 に 0-16、final confirmation でも 0-80

E6 Boatlee + collision guard: E2 に 0-16。不採用

E9 Boatlee + tomato approximation: Kaito v58 相手に 4-12。不採用

E10 Kaito v27 current: E11 に 0-16。不採用

E12 Kaito v43 current: E11 に 0-16、final confirmation でも 0-80

E13 Kaito v27 + guard: E11 に 0-16。不採用

7. 旧自作系列

v4: stable melon baseline

v5: seed prefetch → 4-80-16 vs v4、不採用

v6: dynamic melon → 1-99、不採用

v7: simple diversification → 1-99、不採用

v8: first livestock rewrite → 0-20、崩壊

v9: stabilized livestock → 13-7 vs v8

v10: 8 cows + 6 sheep + 8 hands → 20-0 vs v9

v11: market-aware selling → 16-4 vs v10

v12: Seyamalam public strong baseline → 20-0 vs v11

v15: Kaito v48 wrapper 系統

h-series

h1: overhiring で崩壊

h2: capital allocation 問題

h3: v11 に 9-0-1、v15 に 0-10

h4: h3 に 0-10、v15 に 0-10

Decision: h-series は主経路として停止。

8. 重要な戦略知見

Common-pool market

Kaggriculture は単独 farm 最適化だけではなく、2人が同じ market inventory / price dynamics を共有する common-pool game。

同じ premium item を同時刻に大量 sell すると自己衝突が起きる。したがって将来的な frontier は

strong farm program + opponent-aware market timing

になる可能性が高い。

ただし E11 exact に単純な sell-delay overlay を重ねた E14-E16 はすべて悪化した。

Crop demand substitution

公開実験では strawberry oversupply と tomato undersupply を使った置換が有効なケースがある。ただし独自近似 E9 は悪化したため、元実装を正確に再現しない限り採用しない。

9. 現在の実験ルール

旧版への勝利だけでは promotion しない

同じ seed、両席で比較

tuning に使った seed は holdout として再利用しない

まず 20-40 games で screening

通過候補のみ 100-500 games で確認

W / D / L を最優先

mean reward / mean margin は補助指標

broken candidate は勝敗に混ぜない

10. 次にやること

P0: E11 exact を凍結

現時点では E11 exact が最強。浅い overlay は追加しない。

P1: Kaggle 実スコア確認

submission_e11.tar.gz は提出済み。displayed score は 600.0。

ローカル 99.2% と Kaggle 上の score / 実対戦分布の差を確認する。

P2: 公開 frontier の継続探索

締切まで、E11 より新しい / 強い公開 agent が出ていないか監視する。

P3: E11 を超える独自差分

live leaderboard や再現可能な losses に共通弱点が見えた場合だけ targeted に修正する。

11. Current Best summary

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

displayed score: 600.0

submitted: 2026-09-17

原則

ここから先も最終目的を忘れないこと。

「自作であること」ではなく、Kaggriculture の最終 Bradley-Terry を最大化することが目的。

ただし、公開 artifact を使う場合はライセンス・provenance・submission conditions を確認する。