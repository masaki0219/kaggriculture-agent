import contextlib, hashlib, io, json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

def play(job):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import kaggle_environments
        from kaggle_environments import make
        from kaggle_environments.agent import Agent, get_last_callable
    assert kaggle_environments.__version__ == '1.32.7'
    source=Path(job['candidate']).resolve()
    rival=Path(job['opponent']).resolve()
    assert hashlib.sha256(source.read_bytes()).hexdigest()==job['sha256']
    selected=get_last_callable(source.read_text(encoding='utf-8'),path=str(source))
    assert selected is selected.__globals__.get('agent'), 'Kaggle selected the wrong export'
    originals=Agent.act
    calls={str(source):0,str(rival):0}
    errors=[]
    max_time={str(source):0.,str(rival):0.}
    def tracked(self,obs):
        action,log=originals(self,obs)
        key=str(Path(self.raw).resolve())
        calls[key]+=1
        max_time[key]=max(max_time[key],float(log.get('duration',0)))
        if isinstance(action,Exception) or not isinstance(action,dict) or 'Traceback (most recent call last)' in log.get('stderr',''):
            errors.append({'step':calls[key],'agent':key,'stderr':log.get('stderr','')[:1000]})
        return action,log
    Agent.act=tracked
    try:
        agents=[str(source),str(rival)]
        if job['seat']==1:agents.reverse()
        with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
            env=make('kaggriculture',configuration={'episodeSteps':720,'seed':job['seed']},debug=False)
            env.run(agents)
        assert len(env.steps)==720
        assert all(str(s.status)=='DONE' for s in env.steps[-1])
        assert not errors and all(n==719 for n in calls.values()), (calls,errors)
        seat=job['seat']
        own=float(env.steps[-1][seat].reward)
        opponent=float(env.steps[-1][1-seat].reward)
        if 'expected_own' in job:
            assert (own,opponent)==(job['expected_own'],job['expected_opponent'])
        timeline=[]
        for step in []:
            state=env.steps[step]
            farm=state[seat].observation.farms[seat]
            action=env.steps[step+1][seat].action if step<719 else None
            timeline.append({'step':step,'target_tile':farm.tiles[4][2],
                             'hand_3':action.get('hands',[])[2] if action and len(action.get('hands',[]))>2 else None})
        return {'seat':seat,'seed':job['seed'],'reward':own,'opponent_reward':opponent,
                'margin':own-opponent,'states':720,'candidate_calls':calls[str(source)],
                'opponent_calls':calls[str(rival)],'runtime_errors':len(errors),
                'max_candidate_seconds':max_time[str(source)],'timeline':timeline}
    finally:
        Agent.act=originals

if __name__=='__main__':
    jobs=json.loads(Path(sys.argv[1]).read_text())
    with ProcessPoolExecutor(max_workers=8,max_tasks_per_child=1) as pool:
        rows=list(pool.map(play,jobs))
    Path(sys.argv[2]).write_text(json.dumps(rows,indent=2)+'\n')
