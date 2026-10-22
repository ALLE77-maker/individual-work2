"""Paired offline replay of one accessor fix on recorded original-prompt episodes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import statistics
import sys

ROOT=Path(__file__).resolve().parents[1]
UPSTREAM=ROOT/'vendor/lits-llm'
sys.path[:0]=[str(UPSTREAM),str(UPSTREAM/'demos')]
from lits.structures.env_grounded import EnvState,EnvStep,EnvAction
from lits_benchmark.crosswords import CrosswordsTransition,load_crosswords
from analyze_results import independent_scores

class SnapshotPreservingEnvState(EnvState):
    @property
    def env_state(self):
        for step in reversed(self):
            if step.next_state:
                return step.next_state
        return self.init_state

def make_state(cls,episode):
    result=cls(init_state=episode['initial_state'])
    for payload in episode['steps']:
        result.append(EnvStep.from_dict(deepcopy(payload)))
    return result

def sanity_control(examples):
    example=examples[10]
    transition=CrosswordsTransition(base_model=None)
    state=transition.init_state(**example)
    rows=example['query_or_goals'].splitlines()[:5]
    for i,word in enumerate(rows,1):
        action=f'h{i}. {word.lower()}'
        assert transition.validate_action(state.env_state,action)
        state,info=transition.step(state,EnvAction(action),query_or_goals=example['query_or_goals'])
        assert not info['message']
    assert transition.goal_check(example['query_or_goals'],state.env_state)==(True,1.0)
    observed=state.env_state
    state.append(EnvStep(action=EnvAction('invalid'),error='synthetic terminal error for software test',terminate=True))
    assert state.env_state==state.init_state
    fixed=SnapshotPreservingEnvState(init_state=state.init_state)
    fixed.extend(state)
    assert fixed.env_state==observed
    assert fixed[-1].terminate and fixed[-1].error
    assert transition.goal_check(example['query_or_goals'],fixed.env_state)==(True,1.0)
    blank=SnapshotPreservingEnvState(init_state='initial')
    blank.append(EnvStep(error='no observed board',terminate=True))
    assert blank.env_state=='initial'
    return {'type':'deterministic software test, not LLM performance',
            'puzzle_id':10,'known_answer_row_placements':5,
            'word_accuracy_before_synthetic_error':1.0,
            'original_accessor_after_synthetic_error':0.0,
            'fixed_accessor_after_synthetic_error':1.0,
            'error_flag_preserved':True,'empty_history_fallback_passes':True}

def main():
    output=ROOT/'results/state_fix'
    output.mkdir(parents=True,exist_ok=True)
    data_file=UPSTREAM/'demos/crosswords/data/mini0505.json'
    examples=load_crosswords(str(data_file))
    dataset=json.loads(data_file.read_text())
    result=[]
    files=[]
    for seed in [17,42,2026]:
        for puzzle in range(10):
            source=ROOT/f'results/main/baseline_s{seed}_p{puzzle:03d}.json'
            episode=json.loads(source.read_text())
            original=make_state(EnvState,episode)
            fixed=make_state(SnapshotPreservingEnvState,episode)
            assert original.env_state==episode['final_state']
            assert original.init_state==fixed.init_state
            assert [step.to_dict() for step in original]==[step.to_dict() for step in fixed], 'Only state access may change'
            orig=independent_scores(original.env_state,dataset[puzzle][1])
            repaired=independent_scores(fixed.env_state,dataset[puzzle][1])
            last_observed=next((step.next_state for step in reversed(original) if step.next_state),original.init_state)
            assert fixed.env_state==last_observed
            assert bool(fixed[-1].terminate)==bool(original[-1].terminate)
            valid_steps=sum(bool(step.next_state) for step in original)
            result.append({
                'seed':seed,'puzzle_id':puzzle,'valid_transition_steps':valid_steps,
                'has_observed_placement':valid_steps>0,
                'original_retains_last_observed':original.env_state==last_observed,
                'fixed_retains_last_observed':fixed.env_state==last_observed,
                'original_word_accuracy':orig[0],'fixed_word_accuracy':repaired[0],
                'original_character_accuracy':orig[1],'fixed_character_accuracy':repaired[1],
                'original_exact_match':orig[2],'fixed_exact_match':repaired[2],
                'original_final_state':original.env_state,'fixed_final_state':fixed.env_state,
                'terminal_error':bool(original[-1].terminate and original[-1].error),
                'n_calls_unchanged':episode['n_calls'],
                'ground_truth_rows':[''.join(dataset[puzzle][1][5*i:5*i+5]) for i in range(5)],
                'source':source.relative_to(ROOT).as_posix(),
                'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            })
            files.append(source.relative_to(ROOT).as_posix())
    trials=[]
    for seed in [17,42,2026]:
        selected=[r for r in result if r['seed']==seed]
        trials.append({'seed':seed,**{
            key:statistics.mean(r[key] for r in selected)
            for key in ['original_word_accuracy','fixed_word_accuracy','original_character_accuracy',
                        'fixed_character_accuracy','original_exact_match','fixed_exact_match',
                        'original_retains_last_observed','fixed_retains_last_observed','terminal_error']
        }})
    metrics={}
    for key in trials[0]:
        if key=='seed':continue
        vals=[t[key] for t in trials]
        metrics[key]={'mean':statistics.mean(vals),'sample_sd':statistics.stdev(vals),
                      'sample_variance':statistics.variance(vals),'trial_values':vals}
    illustrative=sorted(result,key=lambda r:(-(r['fixed_character_accuracy']-r['original_character_accuracy']),r['seed'],r['puzzle_id']))[0]
    summary={
        'design':'paired offline replay, no new model calls','episodes':30,
        'changed_board_episodes':sum(r['original_final_state']!=r['fixed_final_state'] for r in result),
        'episodes_with_observed_placements':sum(r['has_observed_placement'] for r in result),
        'terminal_error_episodes':sum(r['terminal_error'] for r in result),
        'metrics':metrics,'trials':trials,'illustrative_pair':illustrative,
        'sanity_control':sanity_control(examples),'new_llm_calls':0,
        'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL_STATE_FIX.md').read_bytes()).hexdigest(),
        'audit':{'identical_recorded_steps':True,'all_fixed_accessors_match_last_observation':True,
                 'terminal_error_flags_preserved':True},
    }
    (output/'episodes.json').write_text(json.dumps(result,indent=2))
    (output/'summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
