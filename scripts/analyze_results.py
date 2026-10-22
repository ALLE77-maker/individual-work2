"""Independently audit saved grids and compute descriptive paired statistics."""
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[1]
RESULTS=ROOT/'results/main'

def independent_scores(text, ground_truth):
    match=re.search(r'Current Board:\n((?:[A-Z_]{5}\n){5})',text)
    if not match:
        raise ValueError('Missing final board')
    rows=match.group(1).strip().splitlines()
    predicted=rows+[''.join(row[c] for row in rows) for c in range(5)]
    truth=''.join(ground_truth).upper()
    true_rows=[truth[k:k+5] for k in range(0,25,5)]
    answers=true_rows+[''.join(row[c] for row in true_rows) for c in range(5)]
    words=sum(a==b for a,b in zip(predicted,answers))/10
    chars=sum(a==b for a,b in zip(''.join(rows),truth))/25
    return words,chars,int(predicted==answers)

def main():
    config=json.loads((RESULTS/'config.json').read_text())
    dataset=ROOT/'vendor/lits-llm/demos/crosswords/data/mini0505.json'
    assert hashlib.sha256(dataset.read_bytes()).hexdigest()==config['dataset_sha256']
    data=json.loads(dataset.read_text())
    episodes=[]
    evidence={}
    for condition in config['conditions']:
        for seed in config['seeds']:
            for puzzle in config['puzzle_ids']:
                stem=f'{condition}_s{seed}_p{puzzle:03d}'
                path=RESULTS/f'{stem}.json'
                episode=json.loads(path.read_text())
                assert (episode['condition'],episode['seed'],episode['puzzle_id'])==(condition,seed,puzzle)
                word,char,exact=independent_scores(episode['final_state'],data[puzzle][1])
                assert abs(word-episode['word_accuracy'])<1e-12
                assert abs(char-episode['character_accuracy'])<1e-12
                assert exact==episode['exact_match']
                assert word==episode['official_goal_check'][1]
                calls_path=RESULTS/f'{stem}.calls.jsonl'
                calls=[json.loads(line) for line in calls_path.read_text().splitlines()]
                assert len(calls)==episode['n_calls']
                assert sum(c['output_tokens'] for c in calls)==episode['output_tokens']
                assert sum(not c['valid_action'] for c in calls)==episode['invalid_proposals']
                assert abs(sum(c['inference_seconds'] for c in calls)-episode['inference_seconds'])<1e-8
                assert all((c['condition'],c['seed'],c['puzzle_id'])==(condition,seed,puzzle) for c in calls)
                # Blank ground-truth variable in the upstream prompt is never rendered.
                assert all('Letter-consistency rule:' in c['prompt'] for c in calls) if condition!='baseline' else all('Letter-consistency rule:' not in c['prompt'] for c in calls)
                for check_path in [path,calls_path]:
                    evidence[check_path.relative_to(ROOT).as_posix()]=hashlib.sha256(check_path.read_bytes()).hexdigest()
                episodes.append(episode)
    assert len(episodes)==60
    trials=[]
    for condition in config['conditions']:
        for seed in config['seeds']:
            rows=[e for e in episodes if e['condition']==condition and e['seed']==seed]
            calls=sum(r['n_calls'] for r in rows)
            valid=sum(r['valid_proposals'] for r in rows)
            trials.append({
                'condition':condition,'seed':seed,'puzzles':len(rows),
                'word_accuracy':statistics.mean(r['word_accuracy'] for r in rows),
                'character_accuracy':statistics.mean(r['character_accuracy'] for r in rows),
                'exact_match':statistics.mean(r['exact_match'] for r in rows),
                'mean_calls':statistics.mean(r['n_calls'] for r in rows),
                'mean_output_tokens':statistics.mean(r['output_tokens'] for r in rows),
                'mean_inference_seconds':statistics.mean(r['inference_seconds'] for r in rows),
                'invalid_proposal_rate':sum(r['invalid_proposals'] for r in rows)/calls if calls else 0,
                'letter_conflict_rate':sum(r['letter_conflicts'] for r in rows)/valid if valid else 0,
                'terminal_error_rate':statistics.mean(r['terminal_error'] for r in rows),
            })
    grouped={}
    metrics=[k for k in trials[0] if k not in {'condition','seed','puzzles'}]
    for condition in config['conditions']:
        selected=[t for t in trials if t['condition']==condition]
        grouped[condition]={}
        for metric in metrics:
            values=[t[metric] for t in selected]
            grouped[condition][metric]={
                'mean':statistics.mean(values), 'sample_sd':statistics.stdev(values),
                'sample_variance':statistics.variance(values),'trial_values':values,
            }
    paired=[]
    for seed in config['seeds']:
        a=next(t for t in trials if t['condition']=='baseline' and t['seed']==seed)
        b=next(t for t in trials if t['condition']=='letter_consistency' and t['seed']==seed)
        paired.append({'seed':seed,**{metric:b[metric]-a[metric] for metric in metrics}})
    # Select an illustrative paired episode by absolute accuracy difference, with fixed tie-breaks.
    candidates=[]
    for seed in config['seeds']:
        for puzzle in config['puzzle_ids']:
            a=next(e for e in episodes if e['condition']=='baseline' and e['seed']==seed and e['puzzle_id']==puzzle)
            b=next(e for e in episodes if e['condition']=='letter_consistency' and e['seed']==seed and e['puzzle_id']==puzzle)
            candidates.append((abs(b['word_accuracy']-a['word_accuracy']),seed,puzzle,a,b))
    illustrative=sorted(candidates,key=lambda row:(-row[0],row[1],row[2]))[0]
    summary={
        'unique_puzzles':10,'seeds':config['seeds'],'episodes':len(episodes),
        'trials':trials,'conditions':grouped,'paired_differences':paired,
        'mean_paired_word_difference':statistics.mean(p['word_accuracy'] for p in paired),
        'total_model_calls':sum(e['n_calls'] for e in episodes),
        'total_output_tokens':sum(e['output_tokens'] for e in episodes),
        'total_inference_seconds':sum(e['inference_seconds'] for e in episodes),
        'paid_api_cost_usd':0,
        'illustrative_pair':{'selection':'largest absolute word-accuracy difference, then lowest seed and puzzle ID',
                             'seed':illustrative[1],'puzzle_id':illustrative[2],
                             'baseline':illustrative[3],'letter_consistency':illustrative[4]},
        'audit':{'complete_episode_count':60,'independent_grid_scores_agree':True,
                 'per_call_token_counts_agree':True,'dataset_hash_agrees':True},
    }
    (RESULTS/'summary.json').write_text(json.dumps(summary,indent=2))
    (RESULTS/'evidence_manifest.json').write_text(json.dumps(evidence,indent=2))
    for name,rows in [('trial_metrics',trials),('paired_differences',paired)]:
        with (RESULTS/f'{name}.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)
    print(json.dumps({k:v for k,v in summary.items() if k in ['episodes','mean_paired_word_difference','total_model_calls','audit']},indent=2))

if __name__=='__main__':
    main()
