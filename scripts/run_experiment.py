"""Run upstream LiTS Crosswords with a local MLX model and preserve all evidence."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import logging
import os
from pathlib import Path
import platform
import random
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / 'vendor/lits-llm'
sys.path[:0] = [str(UPSTREAM), str(UPSTREAM / 'demos')]
os.environ.setdefault('HF_HUB_OFFLINE', '1')
os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')

from lits.agents.chain.env_chain import EnvChain
from lits.components.policy.env_grounded import EnvGroundedPolicy
from lits.lm.base import LanguageModel, Output
from lits.prompts.prompt import PromptTemplate
from lits_benchmark.crosswords import (
    CrosswordsTransition, load_crosswords, crosswords_policy_usr_prompt,
)

EXTRA_INSTRUCTION = (
    '\n\nLetter-consistency rule: Every non-underscore letter in the chosen '
    'position is fixed by the current board. Your proposed word must match '
    'all of these letters in their exact positions. Choose another unfilled '
    'position if you cannot find a matching word.'
)

def score_grid(state_text, gt_board):
    """Independent scorer. No upstream reward or goal-check code is used here."""
    match = re.search(r'Current Board:\n((?:[A-Z_]{5}\n){5})', state_text)
    if not match:
        raise ValueError('Missing 5x5 board')
    rows = match.group(1).strip().splitlines()
    truth = ''.join(gt_board).upper()
    predicted = ''.join(rows)
    pred_words = rows + [''.join(rows[r][c] for r in range(5)) for c in range(5)]
    gt_rows = [truth[i:i+5] for i in range(0,25,5)]
    gt_words = gt_rows + [''.join(gt_rows[r][c] for r in range(5)) for c in range(5)]
    correct_words = sum(p==g for p,g in zip(pred_words,gt_words))
    return {
        'word_accuracy': correct_words / 10,
        'exact_match': int(correct_words == 10),
        'character_accuracy': sum(p==g for p,g in zip(predicted,truth))/25,
        'correct_words': correct_words,
        'board': rows,
        'predicted_words': pred_words,
        'ground_truth_words': gt_words,
    }

def extract_state_from_prompt(prompt):
    # The upstream prompt embeds a complete state before its action request.
    start = prompt.find('Current Board:')
    end = prompt.find('\nChoose ONE unfilled position', start)
    if start < 0 or end < 0:
        raise ValueError('Prompt does not match the pinned upstream template')
    return prompt[start:end].strip() + '\n'

def proposal_diagnostics(prompt, response):
    snapshot = extract_state_from_prompt(prompt)
    action = response.strip()
    valid = CrosswordsTransition.validate_action(snapshot, action)
    conflict = None
    if valid:
        position, word = action.split('. ')
        rows = re.search(r'Current Board:\n((?:[A-Z_]{5}\n){5})',snapshot).group(1).strip().splitlines()
        i = int(position[1])-1
        pattern = rows[i] if position[0]=='h' else ''.join(row[i] for row in rows)
        conflict = any(a!='_' and a!=b for a,b in zip(pattern,word.upper()))
    return {'valid_action': valid, 'letter_conflict': conflict}

class LocalMLXModel(LanguageModel):
    """Thin inference adapter. Agent logic remains in the original LiTS classes."""
    def __init__(self, model_path):
        import mlx.core as mx
        from mlx_lm import load
        self.mx = mx
        model, tokenizer = load(str(model_path))
        super().__init__(
            model_name='mlx-community/Qwen2.5-3B-Instruct-4bit',
            model=model, tokenizer=tokenizer, max_new_tokens=32,
        )
        self.sys_prompt = None
        self.calls = []
        self.context = {}
        self.raw_file = None

    def __call__(self, prompt, role='default', temperature=0.8,
                 top_p=0.95, top_k=50, max_new_tokens=32, **kwargs):
        from mlx_lm import stream_generate
        from mlx_lm.sample_utils import make_sampler
        messages = [{'role':'user','content':prompt}]
        if self.sys_prompt:
            messages.insert(0,{'role':'system','content':self.sys_prompt})
        formatted = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True)
        sampler = make_sampler(temp=temperature, top_p=top_p, top_k=top_k)
        start = time.perf_counter()
        pieces = []
        last = None
        for response in stream_generate(
            self.model, self.tokenizer, formatted,
            max_tokens=max_new_tokens or 32, sampler=sampler,
        ):
            pieces.append(response.text)
            last = response
        self.mx.synchronize()
        elapsed = time.perf_counter()-start
        text = ''.join(pieces)
        record = {
            **self.context,
            'call_index': len(self.calls),
            'role': role, 'temperature': temperature,
            'top_p': top_p, 'top_k': top_k,
            'max_new_tokens': max_new_tokens or 32,
            'prompt': prompt, 'system_prompt': self.sys_prompt,
            'formatted_prompt_sha256': hashlib.sha256(formatted.encode()).hexdigest(),
            'output': text,
            'input_tokens': int(last.prompt_tokens) if last else 0,
            'output_tokens': int(last.generation_tokens) if last else 0,
            'inference_seconds': elapsed,
            'finish_reason': getattr(last,'finish_reason',None),
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            **proposal_diagnostics(prompt,text),
        }
        self.calls.append(record)
        if self.raw_file:
            with self.raw_file.open('a') as stream:
                stream.write(json.dumps(record)+'\n')
        return Output(text)

def runtime_versions():
    versions = {}
    for name in ['mlx','mlx-lm','numpy','transformers','tokenizers','pydantic']:
        versions[name] = importlib.metadata.version(name)
    return versions

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pilot',action='store_true')
    parser.add_argument('--output',type=Path,default=ROOT/'results/main')
    args = parser.parse_args()
    runtime_diff=subprocess.check_output(['git','-C',str(UPSTREAM),'diff','--binary'])
    if runtime_diff != (ROOT/'patches/lazy_imports.patch').read_bytes():
        raise RuntimeError('Upstream working files differ from the common runtime patch. Run the original experiment in a clean pinned checkout; test the accessor fix separately.')
    output = args.output if not args.pilot else ROOT/'results/pilot'
    output.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(filename=output/'execution.log',level=logging.INFO,
                        format='%(asctime)s %(levelname)s %(name)s %(message)s')
    dataset_path=UPSTREAM/'demos/crosswords/data/mini0505.json'
    examples=load_crosswords(str(dataset_path))
    ids=[10] if args.pilot else list(range(10))
    seeds=[17] if args.pilot else [17,42,2026]
    conditions=['baseline','letter_consistency']
    manifest=json.loads((ROOT/'references/model_manifest.json').read_text())
    config={
        'upstream_repository':'https://github.com/xinzhel/lits-llm',
        'upstream_commit':subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip(),
        'dataset_sha256':hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        'model_repository':manifest['repository'], 'model_revision':manifest['revision'],
        'model_sha256':manifest['files']['model.safetensors'],
        'puzzle_ids':ids,'seeds':seeds,'conditions':conditions,
        'max_steps':10,'temperature':0.8,'top_p':0.95,'top_k':50,'max_new_tokens':32,
        'modification':EXTRA_INSTRUCTION,'python':sys.version,'platform':platform.platform(),
        'versions':runtime_versions(),'started_utc':datetime.now(timezone.utc).isoformat(),
        'protocol_sha256':hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest(),
    }
    config_path=output/'config.json'
    if config_path.exists():
        previous=json.loads(config_path.read_text())
        for key in ['upstream_commit','dataset_sha256','model_sha256','puzzle_ids','seeds','conditions',
                    'max_steps','temperature','top_p','top_k','max_new_tokens','modification','protocol_sha256']:
            if previous[key] != config[key]:
                raise RuntimeError(f'Configuration mismatch: {key}')
    else:
        config_path.write_text(json.dumps(config,indent=2))
    print('Loading local model',flush=True)
    model=LocalMLXModel(ROOT/'models/qwen2.5-3b')
    base_prompt=crosswords_policy_usr_prompt()
    model.context={'condition':'warmup','seed':0,'puzzle_id':10}
    model.raw_file=output/'warmup.calls.jsonl'
    model.mx.random.seed(0)
    model(base_prompt.format(init_state=examples[10]['init_state_str'],goals='',actions=''),
          max_new_tokens=32)
    results=[]
    for seed in seeds:
        for puzzle_id in ids:
            # Alternate order deterministically to reduce a systematic timing bias.
            order=conditions if (seed+puzzle_id)%2 else list(reversed(conditions))
            for condition in order:
                stem=f'{condition}_s{seed}_p{puzzle_id:03d}'
                episode_path=output/f'{stem}.json'
                if episode_path.exists():
                    results.append(json.loads(episode_path.read_text()))
                    print(f'Resumed completed {stem}',flush=True)
                    continue
                model.calls=[]
                model.context={'condition':condition,'seed':seed,'puzzle_id':puzzle_id}
                model.raw_file=output/f'{stem}.calls.jsonl'
                if model.raw_file.exists():
                    # Preserve interrupted outputs, but never mix them with the new episode.
                    model.raw_file.rename(output/f'{stem}.interrupted-{time.time_ns()}.jsonl')
                random.seed(seed)
                model.mx.random.seed(seed)
                prompt=base_prompt
                if condition=='letter_consistency':
                    prompt=PromptTemplate(base_prompt.template+EXTRA_INSTRUCTION,
                                          input_variables=list(base_prompt.input_variables))
                policy=EnvGroundedPolicy(
                    base_model=model,usr_prompt_spec=prompt,task_name='crosswords',
                    validate_action=CrosswordsTransition.validate_action,
                    n_actions=1,temperature=0.8,top_p=0.95,top_k=50,
                    max_new_tokens=32,max_steps=10,
                    force_terminating_on_depth_limit=False,
                )
                transition=CrosswordsTransition(base_model=None)
                agent=EnvChain(policy=policy,world_model=transition,max_steps=10)
                example=examples[puzzle_id]
                start=time.perf_counter()
                state=agent.run(example['query_or_goals'],example['init_state_str'],query_idx=puzzle_id)
                elapsed=time.perf_counter()-start
                metrics=score_grid(state.env_state,example['board_gt'])
                official=transition.goal_check(example['query_or_goals'],state.env_state)
                assert abs(metrics['word_accuracy']-official[1])<1e-12
                assert metrics['exact_match']==int(official[0])
                steps=[step.to_dict() for step in state]
                scored={
                    **model.context,**metrics,'official_goal_check':list(official),
                    'steps':steps,'initial_state':example['init_state_str'],'final_state':state.env_state,
                    'n_steps':len(state),'n_calls':len(model.calls),
                    'input_tokens':sum(c['input_tokens'] for c in model.calls),
                    'output_tokens':sum(c['output_tokens'] for c in model.calls),
                    'inference_seconds':sum(c['inference_seconds'] for c in model.calls),
                    'episode_seconds':elapsed,
                    'invalid_proposals':sum(not c['valid_action'] for c in model.calls),
                    'letter_conflicts':sum(c['letter_conflict'] is True for c in model.calls),
                    'valid_proposals':sum(c['valid_action'] for c in model.calls),
                    'terminal_error':any(s.get('terminate') and s.get('error') for s in steps),
                    'finished_utc':datetime.now(timezone.utc).isoformat(),
                }
                episode_path.write_text(json.dumps(scored,indent=2))
                state.save(str(output/f'{stem}.trajectory.json'),example['query_or_goals'])
                results.append(scored)
                print(f"{stem}: words={metrics['word_accuracy']:.0%}, calls={len(model.calls)}, time={elapsed:.1f}s",flush=True)
    (output/'episodes.json').write_text(json.dumps(results,indent=2))
    print(f'Completed {len(results)} real agent episodes',flush=True)

if __name__=='__main__':
    main()
