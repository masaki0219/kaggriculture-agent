Kaggle の Featured Simulation Competition Kaggriculture 用エージェントを改善していくリポジトリです。

Competition: https://www.kaggle.com/competitions/kaggriculture

この README は単なるプロジェクト紹介ではなく、ChatGPT との複数チャットにまたがる共有メモ・実験記録・引き継ぎ書として使用します。

重要

新しいチャットを始めたら、ChatGPT は過去チャットの記憶より先に、この README と GitHub 上の最新コードを確認すること。

README / 最新コードと会話メモリが食い違う場合は、GitHub を優先する。

1. 目的

残り期間で Kaggriculture エージェントをできるだけ強くする。

単にコードを書くことではなく、

仮説を立てる

変更を実装する

ローカル対戦で旧版と比較する

勝率を確認する

良い変更だけ残す

結果と判断理由を README に残す

というサイクルを高速で回す。

実装は ChatGPT / AI を積極的に利用するが、

何を変えたか

なぜ変えたか

本当に強くなったか

を常に追跡できる状態にする。

2. 競技について重要なこと

Competition: Kaggriculture

提出締切: 2026-10-01

2026-09-16 時点で残り約2週間

最終評価では Bradley-Terry による評価が使われる

Leaderboard の reward の大きさだけではなく、対戦相手に勝つ確率を重視する

競技ルール・評価方式・submission条件などは変更される可能性があるため、重要な判断の前には Kaggle 公式情報を再確認する

参考:

https://www.kaggle.com/competitions/kaggriculture/overview

https://www.kaggle.com/competitions/kaggriculture/overview/evaluation

3. 現在のファイル

agent_v12.py

現在の基準エージェント / Current Best。

2026-09-16 に、これまでの自作系列から方針転換し、公開強豪
Seyamalam/Kaggriculture の現行 main.py をローカルでそのまま呼び出す
wrapper を agent_v12.py として採用した。

現時点の agent_v12.py は独自戦略ではなく、公開強豪を凍結 baseline として採用したもの。

目的は、今後の独自改善をこの強い baseline から 1 変更ずつ検証し、
「公開agentに追いつく」段階ではなく「公開agentを超える」段階へ進むこと。

compare_v12.py

agent_v12.py を旧版・公開agentと比較するローカル benchmark。

現在の標準:

seed 0〜9

同じ seed で席順を交換

20 games / opponent

W / D / L

score

mean reward

mean margin

min / max reward

旧自作系列

これまでの主な candidate:

v4: stable melon baseline

v7: simple crop diversification

v8: first livestock rewrite

v9: stabilized livestock economy

v10: livestock scale-up

v11: market-aware selling

v4〜v11 は、Kaggriculture の主要メカニズムを理解し、
何が効くかを切り分けるために重要だった。

一方で、公開上位agentとの差が大きかったため、
今後はこれらを主戦力として継続改良するのではなく、
agent12 を強い固定 baseline として、その上に独自改善を重ねる。

公開比較agent

ローカル benchmark で主に使用:

public_agents/gzmcr/main.py

public_agents/lonespear/main.py

public_agents/seyamalam/main.py

公開agentは比較対象であると同時に、ライセンス条件の範囲で
戦略・実装研究の参考にもする。

4. 現在の戦略

現在の Current Best は agent12。

agent12 は Seyamalam の現行公開agentを baseline としているため、
固定 MELON 専業ではなく、複数の高度な仕組みを統合している。

確認できている主な特徴:

land expansion

大規模な hired hands

COW / SHEEP を中心とする livestock economy

WHEAT / MELON / STRAWBERRY 等を組み合わせた複合作物

feed logistics

shed capacity management

market order scheduling

late-game liquidation

opponent / state-aware adaptation

fixed / learned expert route

market timing adaptation

公開元の標準設定には概ね、

hands = 13
cows = 8
sheep = 6
strawberries = 34
opening_wheat = 10
opening_melons = 9

などが含まれている。

重要なのは、今後これをそのまま使い続けることではなく、
この baseline がまだ負ける局面を特定し、独自差分で改善すること。

したがって今後の開発単位は、

agent12
  ↓
1つの仮説だけ変更
  ↓
agent13 candidate
  ↓
paired benchmark
  ↓
勝敗で採否

とする。

5. 既知の論点・未検証点

ここは「バグと確定したもの」だけではなく、
Current Best を超えるために優先して検証すべき問題を記録する。

A. Midgame production scale

Seyamalam 自身の公開 loss analysis では、
ある敗戦で相手が中盤により多くの hands と animal を持ち、
最終的に premium product の生産量差で負けている。

したがって、

相手の hands 数

相手の animal 数

自分との bank 差

land 差

を見て、中盤の追加投資を早める適応戦略は有力候補。

B. Sheep / WOOL throughput

別の公開敗戦では、相手が sheep を 1 頭多く保持し、
WOOL を 30 units 多く売ったことが最終差の大部分を説明している。

固定 8 cows + 6 sheep が常に最適とは限らない。

候補:

opponent sheep count を見る

WOOL price / opponent pipeline を見る

必要なら sheep 7頭目以降を許可する

C. Opponent-aware portfolio

最終的には、

opponent farm
market prices
market inventory
town demand
bank lead / deficit
remaining horizon

から、

COW / SHEEP 比率

crop mix

hands 数

land investment

sell timing

を変える agent を目指す。

D. Public-baseline overfitting

agent12 は非常に強いが、1つの公開agentをそのまま基準にしている。

そのため、

GzmCR

lonespear

別タイプの公開agent

未知 holdout

に対して継続評価し、
Seyamalam mirror 専用の変更にならないよう注意する。

E. Submission self-contained 化

現在の agent_v12.py はローカル wrapper。

Kaggle submission 時には public_agents/seyamalam/main.py を外部参照できないため、
最終提出候補は self-contained single file にする必要がある。

元コードの copyright / license / attribution は維持する。

6. 残り期間の開発方針

残り約2週間なので、

ゼロから公開上位agentを再実装して追いつく開発はしない。

強い公開baselineを固定し、
その未解決弱点を狙って 1 変更ずつ改善する。

P0: Current Best の固定

agent_v12.py を frozen baseline とする。

agent12 自体を直接いじらず、
次の candidate は別ファイルとして作る。

P1: agent13 — adaptive production scale

最優先候補:

opponent hands が多い

opponent animals が多い

bank で負けている

day がまだ中盤

という条件で、

hands を早めに増やす

COW / SHEEP の追加購入を許可する

P2: Sheep / WOOL adaptation

相手の sheep / WOOL exposure が高い場合に、
標準 6 sheep を超える candidate を試す。

P3: Portfolio adaptation

その後、

livestock mix

crop mix

market timing

land timing

を opponent state に応じて変える。

P4: Strong holdout

旧版に勝つことは promotion 条件にしない。

最低でも、

agent12

GzmCR

lonespear

Seyamalam

可能なら別の公開上位agent

で paired benchmark を行う。

7. 実験方法

基本ルール

可能な限り、

1回の比較で変更点を限定する。

ただし、残り期間が短いため、大幅な戦略変更そのものをcandidateとして試すことは許容する。

推奨フロー

Current Best
     ↓
仮説
     ↓
Candidate
     ↓
20〜40 games
     ↓
明確に弱い
     ├─ Yes → 捨てる
     └─ No
          ↓
      100〜500 games
          ↓
      採用 / 不採用
          ↓
      README更新

8. 実験ログ

失敗した実験も削除しない。

同じ戦略を別チャットで再度試すことを防ぐため。

Date

Baseline

Candidate

Games

Result

Change

Decision

2026-09-16

v3

v4

100

v4 100勝0敗

smarter MELON watering

採用

2026-09-16

v4

v5

100

4勝80敗16分

seed prefetch

不採用

2026-09-16

v4

v6

100

1勝99敗

dynamic MELON target 8/10/12

不採用

2026-09-16

v4

v7

100

1勝99敗

10 MELON + 4 WHEAT

不採用

2026-09-16

v4

v8

20

0勝20敗

livestock rewrite

不採用。seed依存で経済崩壊

2026-09-16

v8

v9

20

13勝7敗

staged livestock / cash reserve

安定化に成功

2026-09-16

v9

v10

20

20勝0敗

8 cows + 6 sheep + 8 hands

採用

2026-09-16

v10

v11

20

16勝4敗

market-aware premium selling

採用

2026-09-16

v11

agent12

20

20勝0敗

Seyamalam public strong baseline

Current Best に昇格

2026-09-16

GzmCR

agent12

20

agent12 20勝0敗

public holdout

baseline確認

2026-09-16

lonespear

agent12

20

agent12 20勝0敗

public holdout

baseline確認

2026-09-16

Seyamalam

agent12

20

10勝10敗

exact same base policy mirror

expected

agent12 benchmark summary

10 seeds × seat swap = 20 games / opponent。

Opponent

agent12 W-D-L

Mean agent12 reward

Mean opponent reward

v11

20-0-0

141,008.0

20,987.6

v10

20-0-0

142,193.8

22,009.3

v4

20-0-0

140,077.3

11,783.9

starter

20-0-0

155,534.5

3,540.1

GzmCR

20-0-0

96,074.9

67,660.6

lonespear

20-0-0

91,010.4

56,612.7

Seyamalam

10-0-10

69,860.9

69,860.9

Total:

W-D-L = 130-0-10
score = 92.9%

ただし Seyamalam 戦は同一policy mirrorであり、
この 92.9% をそのまま「独自agentの強さ」と解釈しない。

agent12 は 強い frozen baseline。

9. Current Best

Current Best: agent_v12.py
Status: Frozen public-strong baseline
Base: Seyamalam/Kaggriculture current main.py
Last verified: 2026-09-16

根拠

ローカル paired benchmark で、

v11: 20-0

v10: 20-0

v4: 20-0

starter: 20-0

GzmCR: 20-0

lonespear: 20-0

Seyamalam: 10-10 mirror

を確認。

解釈上の注意

agent12 は現時点で独自agentではなく、
Seyamalam 公開agentを wrapper で呼んでいる baseline。

したがって今後の目標は、

agent12 を超える agent13

を作ること。

Current Best が変わったら、必ずここを更新する。

10. 次にやること

現在の優先順位:

agent12 を frozen baseline として維持

Seyamalam の現行コード内の adaptive mechanism を正確に読む

agent13 candidate を作る

最初の仮説は midgame production scale または +1 sheep / WOOL adaptation

agent12 と paired comparison

GzmCR / lonespear / Seyamalam holdout で regression check

明確に勝率改善した変更だけ採用

promotion したら README を更新

Kaggle提出候補は self-contained single file 化

attribution / license を保持した状態で submission smoke test

次の agent13 で重要なのは、
「機能をたくさん足す」ことではなく、

公開baselineの既知の敗因を1つだけ狙うこと。

11. ChatGPTとの運用ルール

新しいチャットを開始したら

Kaggriculture agent の開発について話し始めた場合、ChatGPT は最初に、

README.md を読む

GitHub の最新ファイル一覧を見る

必要な最新コードを読む

Current Best を確認する

Experiment Log を確認する

Next Actions を確認する

agent_v12.py が frozen baseline であることを確認する

その上で提案する。

過去チャットの記憶だけで現在の状態を判断しない。

GitHubと記憶が矛盾した場合

優先順位:

最新コード
↓
README
↓
過去チャット / ChatGPTメモリ

コードを変更するとき

最低限、以下を説明する。

何を変更するか

なぜ強くなる可能性があるか

デメリット / リスク

どう比較するか

実験後

重要な結果が出たら、

Experiment Log

Current Best

Known Issues

Next Actions

を更新する。

12. READMEに残すべき情報

最低限、以下をGitHubに残す。

Current Best agent

Current Bestを決定した実験

Leaderboard上の重要な観測

観測した日付

競技ルール・評価方式の重要な更新

実験結果

失敗した戦略

失敗した理由

既知のバグ

怪しい挙動

次に試す仮説

締切までの優先順位

各ファイルの役割

特に、

失敗した戦略を記録すること。

成功例だけ残すと、別チャットで同じ失敗を繰り返す可能性がある。

13. README更新の基準

常に、

次のチャットのChatGPTが、過去チャットを読まなくても開発を再開できるか

を基準にする。

最低限、

今どこまで進んでいるか
何が一番強いか
何を試したか
何が失敗したか
何を次にやるか

が分かる状態を維持する。

Last updated: 2026-09-16 (agent12 baseline adoption)