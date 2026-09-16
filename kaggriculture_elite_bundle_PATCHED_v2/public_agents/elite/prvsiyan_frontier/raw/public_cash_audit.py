"""Audit deterministic worker/market phases from independent public observations.

No environment rollout, agent execution, random seed or future state is supplied
to the calculation. The next recorded state is used only as a verification target.
"""
import argparse
import ast
from collections import Counter
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def official_worker_market_prefix(game):
    engine_path = Path(game.__file__)
    tree = ast.parse(engine_path.read_text(encoding='utf-8'))
    interpreter = copy.deepcopy(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'interpreter'))
    stop = next(i for i, n in enumerate(interpreter.body) if isinstance(n, ast.Expr)
        and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name)
        and n.value.func.id == '_process_market')
    interpreter.name = '_audit_workers_and_market'
    interpreter.body = interpreter.body[:stop + 1]
    module = ast.fix_missing_locations(ast.Module(body=[interpreter], type_ignores=[]))
    scope = dict(game.__dict__)
    exec(compile(module, str(engine_path), 'exec'), scope)
    return scope['_audit_workers_and_market']


def audit(replay_path, expected_digest=None, compare_ledger=None):
    raw = Path(replay_path).read_bytes()
    if expected_digest:
        assert hashlib.sha256(raw).hexdigest() == expected_digest
    replay = json.loads(raw)
    assert len(replay['steps']) == 720
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        from kaggle_environments.envs.kaggriculture import kaggriculture as game
        from kaggle_environments.utils import structify
    engine_path = Path(game.__file__)
    # Execute the exact official prefix through the market phase; omit town,
    # decay, dawn, new shops and framework state propagation entirely.
    phase = official_worker_market_prefix(game)
    env = SimpleNamespace(configuration=structify(replay['configuration']), done=False)
    cfg = replay['configuration']
    turns_per_day = max(1, int(cfg.get('turnsPerDay', 24)))
    originals = game._commit_unit, game._do_hire, game._do_buy_land
    events, identities = [], {}
    current_step = [-1]

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        before = farm['money']
        ok = originals[0](op, item, price, farm, private, market, shed_capacity)
        if ok:
            events.append(dict(step=current_step[0], seat=identities[id(farm)], op=op,
                item=item, cash_delta=farm['money'] - before, price=float(price)))
        return ok

    def hire(farm, private, board_size, mult=1):
        before, count = farm['money'], len(farm['hands'])
        result = originals[1](farm, private, board_size, mult)
        if len(farm['hands']) > count:
            events.append(dict(step=current_step[0], seat=identities[id(farm)], op='HIRE',
                item='HAND', cash_delta=farm['money'] - before))
        return result

    def land(farm, board_size):
        before, count = farm['money'], len(farm['unlocked_quadrants'])
        result = originals[2](farm, board_size)
        if len(farm['unlocked_quadrants']) > count:
            events.append(dict(step=current_step[0], seat=identities[id(farm)], op='BUY_LAND',
                item='LAND', cash_delta=farm['money'] - before))
        return result

    game._commit_unit, game._do_hire, game._do_buy_land = commit, hire, land
    private_checks = 0
    try:
        for step in range(719):
            current_step[0] = step
            observations = [copy.deepcopy(s['observation']) for s in replay['steps'][step]]
            assert observations[0]['farms'] == observations[1]['farms']
            state = [SimpleNamespace(observation=structify(obs),
                action=copy.deepcopy(replay['steps'][step + 1][seat].get('action') or {}))
                for seat, obs in enumerate(observations)]
            assert len(state) == 2 and state[0].observation.farms
            state[0].observation.step = step
            identities.clear()
            identities.update({id(farm): seat for seat, farm in enumerate(state[0].observation.farms)})
            before_money = [f['money'] for f in state[0].observation.farms]
            event_start = len(events)
            phase(state, env)
            for seat in (0, 1):
                expected = replay['steps'][step + 1][seat]['observation']
                calculated = state[0].observation.farms[seat]['money']
                assert calculated == expected['farms'][seat]['money'], ('cash', step, seat, calculated, expected['farms'][seat]['money'])
                assert sum(e['cash_delta'] for e in events[event_start:] if e['seat'] == seat) == calculated - before_money[seat]
                if (step + 1) % turns_per_day:
                    assert state[seat].observation.private == expected['private'], ('private', step, seat)
                    private_checks += 1
    finally:
        game._commit_unit, game._do_hire, game._do_buy_land = originals
    players = []
    for seat in (0, 1):
        cash, units = Counter(), Counter()
        for event in events:
            if event['seat'] == seat:
                name = event['op'] + ':' + event['item']
                cash[name] += event['cash_delta']
                units[name] += 1
        starting = replay['steps'][0][0]['observation']['farms'][seat]['money']
        assert starting + sum(cash.values()) == replay['steps'][-1][seat]['reward']
        players.append(dict(seat=seat, cashflows=dict(cash), units=dict(units)))
    concordance = None
    if compare_ledger:
        prior = json.loads(Path(compare_ledger).read_bytes())
        assert prior['players'] == players
        fields = ('step', 'seat', 'op', 'item', 'cash_delta')
        assert [{k: e[k] for k in fields} for e in events] == [{k: e[k] for k in fields} for e in prior['events']]
        concordance = dict(path=str(Path(compare_ledger).resolve()), sha256=digest(compare_ledger),
            all_events_and_aggregates_equal=True)
    return dict(episode_id=replay['info']['EpisodeId'], replay_sha256=hashlib.sha256(raw).hexdigest(),
        official_engine_sha256=digest(engine_path), cash_transition_checks=1438,
        nondawn_private_state_checks=private_checks, recorded_rewards=[s['reward'] for s in replay['steps'][-1]],
        qualification='719 independently reset public snapshots, exact official worker/market prefix. Both cash transitions checked every turn; both private states checked outside dawn. This attributes executed public cash flows without a continuous full-engine rollout or adaptive counterfactual. Rival private state is used only for offline accounting, never agent decisions.',
        players=players, events=events, full_engine_ledger_concordance=concordance)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('replay', type=Path)
    parser.add_argument('--expected-sha256')
    parser.add_argument('--compare-ledger', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    report = audit(args.replay, args.expected_sha256, args.compare_ledger)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('episode_id', 'cash_transition_checks',
        'nondawn_private_state_checks', 'players', 'full_engine_ledger_concordance')}, indent=2))


if __name__ == '__main__':
    main()
