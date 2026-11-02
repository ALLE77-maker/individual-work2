"""Build the English report from audited measurements only."""
from html import escape
import json
from pathlib import Path
import statistics

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Preformatted,
)

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables'
S=json.loads((ROOT/'results/main/summary.json').read_text())
C=json.loads((ROOT/'results/main/config.json').read_text())
F=json.loads((ROOT/'results/state_fix/summary.json').read_text())
FM=F['metrics']
IDENTITY=json.loads((ROOT/'IDENTITY.json').read_text())
assert S['audit']['independent_grid_scores_agree'] and S['episodes']==60
OUT.mkdir(exist_ok=True)
B=S['conditions']['baseline']
M=S['conditions']['letter_consistency']
delta=S['mean_paired_word_difference']*100
def pct(value): return f'{100*value:.2f}%'
def rate(group,key): return f"{pct(group[key]['mean'])} +/- {100*group[key]['sample_sd']:.2f} pp"
def quantity(group,key): return f"{group[key]['mean']:.2f} +/- {group[key]['sample_sd']:.2f}"
def label(condition): return 'Original prompt' if condition=='baseline' else 'Letter-consistency prompt'
def direction(): return 'increased' if delta>0 else 'decreased' if delta<0 else 'did not change'

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleCustom',fontName='Helvetica-Bold',fontSize=26,leading=31,textColor=colors.HexColor('#102d44'),spaceAfter=16))
styles.add(ParagraphStyle(name='SectionCustom',fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=colors.HexColor('#102d44'),spaceAfter=12))
styles.add(ParagraphStyle(name='BodyCustom',fontName='Helvetica',fontSize=10.5,leading=15,spaceAfter=10))
styles.add(ParagraphStyle(name='SmallCustom',fontName='Helvetica',fontSize=8.5,leading=12,spaceAfter=8))
styles.add(ParagraphStyle(name='TableCustom',fontName='Helvetica',fontSize=8.8,leading=12))
story=[]
markdown=[]
def heading(text,title=False):
    story.append(Paragraph(escape(text),styles['TitleCustom' if title else 'SectionCustom']))
    markdown.append(('# ' if title else '## ')+text+'\n')
def p(text,small=False):
    story.append(Paragraph(escape(text),styles['SmallCustom' if small else 'BodyCustom']))
    markdown.append(text+'\n')
def table(rows,widths=None):
    cells=[[Paragraph(escape(str(value)),styles['TableCustom']) for value in row] for row in rows]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e6eef3')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#102d44')),
        ('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),
        ('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),
        ('BOTTOMPADDING',(0,0),(-1,-1),8),
        ('LINEBELOW',(0,0),(-1,0),0.8,colors.HexColor('#8197a8')),
        ('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#d5dfe6')),
    ]))
    story.extend([t,Spacer(1,12)])
    markdown.append('| '+' | '.join(str(v) for v in rows[0])+' |')
    markdown.append('| '+' | '.join('---' for _ in rows[0])+' |')
    markdown.extend('| '+' | '.join(str(v) for v in row)+' |' for row in rows[1:])
    markdown.append('')
def page(): story.append(PageBreak())

heading('Reproducing LiTS Crosswords',True)
p('A local-model reproduction and a terminal-state preservation fix')
p(f"{IDENTITY['name']}  |  Student ID {IDENTITY['student_id']}\nFTEC5660: Agentic AI for Business and FinTech")
p('Experiment date: 22 October 2026 (Hong Kong).')
heading('Abstract')
p(f"This study runs the authors' LiTS implementation on ten fixed mini crossword puzzles using a free local, quantized Qwen2.5-3B-Instruct model. An initial prompt experiment produces 60 actual episodes across three seeds, with 0% word accuracy in both conditions. Debugging reveals that a terminal error step makes the current-state accessor return the initial blank board, discarding earlier observations. A separate paired offline replay tests one isolated accessor fix on all 30 original-prompt episodes. It restores the observed board in {F['changed_board_episodes']} episodes and recovers {pct(FM['fixed_character_accuracy']['mean'])} character accuracy, while word accuracy remains 0%. The work reproduces executable agent and environment behavior, identifies a reporting defect, and does not reproduce the paper's numerical performance.")
heading('1. Project and reproduction target')
p('LiTS is project 3 on the assignment list. Its modular agent architecture separates action generation, transitions and rewards. This study reuses the original EnvChain, EnvGroundedPolicy and CrosswordsTransition implementations rather than rebuilding the agent. The task requires repeated observation, word selection and board updates, so it meets the assignment definition of a multi-step agentic system.')
p('The numerical reference is the Crosswords chain row in Table 3 of Li and Tao (2026): 6.67% puzzle exact match and 10.33% word accuracy on 30 examples using Claude 3.5 Sonnet. This study uses ten fixed examples and a different model. Those reference numbers provide context only. Differences cannot be attributed solely to the model or treated as confirmation or rejection of the original result.')
p('The original question was whether an explicit letter-consistency instruction improves final word accuracy. It did not. The debugging follow-up then tests an isolated state-accessor fix. This follow-up was designed after observing the initial failures and is disclosed separately. Its purpose is accurate state reporting, not an improvement in model reasoning.')
page()

heading('2. Setup and experimental controls')
table([
    ['Item','Recorded setting'],
    ['Code',f"LiTS commit {C['upstream_commit']}"],
    ['Data','First ten puzzles, IDs 0-9, from mini0505.json (156 puzzles in the source file)'],
    ['Model',C['model_repository']+'; MLX, 4-bit weights'],
    ['Model revision',C['model_revision']],
    ['Hardware','Apple Silicon arm64, 24 GiB system memory; existing user laptop'],
    ['Runtime',f"Python {C['python'].split()[0]}; MLX {C['versions']['mlx']}; mlx-lm {C['versions']['mlx-lm']}; Transformers {C['versions']['transformers']}"],
    ['Decoding','Temperature 0.8, top_p 0.95, top_k 50, at most 32 generated tokens per call'],
    ['Agent budget','10 steps; upstream three-attempt validation retry; depth-limit temperature forcing disabled in both conditions'],
    ['Trials','Seeds 17, 42 and 2026; reset at the start of each paired episode'],
    ['API and data access','No API keys, no paid API calls, no live web access during inference'],
], [95,415])
p('The protocol was written before the measured runs. Puzzle 10 was reserved for the pilot and warm-up. The ten reported puzzle IDs were selected by position, with no filtering based on outcomes. The same seed initializes each paired baseline and modification episode. Condition order alternates deterministically across episodes. Divergent trajectories consume different random draws, so paired seeds are a variance-control convention rather than identical token samples.')
p('Two package initializers use lazy imports to avoid pulling unused training and memory dependencies into the chain-only runtime. These infrastructure changes apply equally to both conditions. The submission includes an exact patch. The agent loop, validation, environment transitions, retry logic and official goal checker retain their pinned upstream implementations.')
p('The lightweight environment uses Transformers '+C['versions']['transformers']+' rather than the upstream full-install pin of 4.51.3. It supplies tokenization for the MLX adapter. This setup difference applies equally to the original and modified prompts. The exact resolved environment is included.',small=True)
p('Model substitution: The underlying LLM differs from the paper, so results are not directly comparable. Local inference also changes hardware, quantization and latency conditions. Electricity and existing hardware costs are not priced.',small=True)
page()

heading('3. Initial prompt experiment and evaluation')
p('The modification appends the following instruction to the original crossword user prompt. No other experimental condition changes.')
p(C['modification'].strip())
p('The instruction uses only the visible board. Ground-truth answers remain in the evaluator. The original crossword template declares a goals variable but does not insert it into the prompt. The saved prompts allow this separation to be audited. The local adapter receives only formatted policy prompts, not the dataset answers.')
table([
    ['Metric','Definition'],
    ['Word accuracy (primary)','Number of correct horizontal and vertical final words divided by 10, averaged across ten puzzles per seed'],
    ['Puzzle exact match','Fraction of puzzles with all 10 words correct'],
    ['Character accuracy','Number of correct final board cells divided by 25'],
    ['Invalid proposal rate','Rejected format or currently filled-position proposals divided by all model calls, including retries'],
    ['Letter conflict rate','Valid-format proposals that disagree with at least one visible letter, divided by valid proposals'],
    ['Efficiency','Model calls, generated tokens and inference seconds per puzzle episode'],
    ['Terminal error rate','Fraction of episodes containing an error step that terminates the trajectory'],
],[110,400])
p('For each metric, the analysis first computes a score over the ten puzzles for each seed, then reports the mean, sample standard deviation and sample variance across the three seed-level scores. The sample variance divides by n-1. Repeated runs on the same ten puzzles are not 30 independent puzzle samples. No statistical significance claim follows from three seeds. Final metrics on this page use the original accessor, including its observed terminal-error behavior.')
p('The upstream validator checks action syntax, five-letter length and whether a position is unfilled. It does not enforce intersection consistency. Therefore the added instruction can change semantic behavior without changing executable action validity. Incorrect crossing words may overwrite earlier correct letters.')
p('The independent scorer reconstructs all ten words directly from the final grid. It agrees with the upstream goal checker on every reported episode. Four hand-checked tests cover perfect, blank, malformed and one-letter-error grids. One wrong cell correctly breaks two words. Raw calls include invalid retries, so reported costs do not silently discard failures.')
page()

heading('4. Initial experiment: measured negative result')
table([
    ['Condition','Word accuracy','Puzzle exact match','Character accuracy'],
    ['Paper chain reference (different model, 30 puzzles)','10.33%','6.67%','Not reported here'],
    ['Local original prompt',rate(B,'word_accuracy'),rate(B,'exact_match'),rate(B,'character_accuracy')],
    ['Local letter-consistency prompt',rate(M,'word_accuracy'),rate(M,'exact_match'),rate(M,'character_accuracy')],
],[135,125,125,125])
p('Local entries show mean +/- sample standard deviation across three seeds. Percentage-point variability describes repeated runs on the fixed subset. The paper row is a contextual reference under different conditions.')
rows=[['Seed','Original word acc.','Modified word acc.','Paired difference']]
for seed in C['seeds']:
    a=next(t for t in S['trials'] if t['condition']=='baseline' and t['seed']==seed)
    b=next(t for t in S['trials'] if t['condition']=='letter_consistency' and t['seed']==seed)
    rows.append([seed,pct(a['word_accuracy']),pct(b['word_accuracy']),f"{100*(b['word_accuracy']-a['word_accuracy']):+.2f} pp"])
table(rows,[65,145,145,155])
table([
    ['Word-accuracy statistic','Original','Modified'],
    ['Mean',pct(B['word_accuracy']['mean']),pct(M['word_accuracy']['mean'])],
    ['Sample SD',f"{100*B['word_accuracy']['sample_sd']:.3f} pp",f"{100*M['word_accuracy']['sample_sd']:.3f} pp"],
    ['Sample variance',f"{10000*B['word_accuracy']['sample_variance']:.3f} pp^2",f"{10000*M['word_accuracy']['sample_variance']:.3f} pp^2"],
],[220,145,145])
p(f'The mean paired difference is {delta:+.2f} pp. All 60 episodes terminate after validation failures, so the prompt intervention does not establish an improvement. These zero final scores also motivated an audit of state handling. Full per-episode results and the six seed-level rows accompany the report as JSON and CSV. The follow-up below preserves these measurements rather than replacing them.')
page()

heading('5. Inference effort and the terminal-state defect')
table([
    ['Metric (per episode unless stated)','Original','Modified'],
    ['Model calls',quantity(B,'mean_calls'),quantity(M,'mean_calls')],
    ['Generated tokens',quantity(B,'mean_output_tokens'),quantity(M,'mean_output_tokens')],
    ['Inference time, seconds',quantity(B,'mean_inference_seconds'),quantity(M,'mean_inference_seconds')],
    ['Invalid proposals',rate(B,'invalid_proposal_rate'),rate(M,'invalid_proposal_rate')],
    ['Letter conflicts among valid proposals',rate(B,'letter_conflict_rate'),rate(M,'letter_conflict_rate')],
    ['Terminal error episodes',rate(B,'terminal_error_rate'),rate(M,'terminal_error_rate')],
],[230,140,140])
p(f"Across all reported conditions, the model made {S['total_model_calls']:,} calls and generated {S['total_output_tokens']:,} tokens. Measured inference time totaled {S['total_inference_seconds']/60:.2f} minutes. Paid API usage was USD 0. These timing values exclude downloading, model loading, warm-up and report preparation. Input length and retries can change runtime even though the nominal step limit stays fixed.")
case=F['illustrative_pair']
def rows_from_text(text):
    import re
    return re.search(r'Current Board:\n((?:[A-Z_]{5}\n){5})',text).group(1).strip().splitlines()
original_rows=rows_from_text(case['original_final_state'])
fixed_rows=rows_from_text(case['fixed_final_state'])
p(f"Illustrative original-prompt trajectory: puzzle {case['puzzle_id']}, seed {case['seed']}. Four valid placements precede a failed proposal. EnvChain appends an error step without next_state. The original accessor checks only that final step and returns the initial blank board. The preserved step history still contains the observed board. The example is selected by the largest character-accuracy difference, then lowest seed and puzzle ID.")
table([
    ['Original accessor','Last observed board','Ground truth'],
    *[[original_rows[i],fixed_rows[i],case['ground_truth_rows'][i]] for i in range(5)],
    ['Character acc. '+pct(case['original_character_accuracy']),'Character acc. '+pct(case['fixed_character_accuracy']),'100%'],
],[170,170,170])
p('An underscore is an unfilled cell. This defect affects reporting after an error; it does not mean the model had solved the puzzle. In this example the original calls are unchanged and the recovered board still has zero correct complete words. The error flag must remain visible.')
page()

heading('6. Isolated modification: preserve the last observation')
p('The modification changes only EnvState.env_state. Instead of inspecting the final step alone, it searches the recorded steps in reverse order and returns the first nonempty next_state. It uses init_state only when no observation exists. The patch contains no new model, prompt, action policy or transition rule.')
p('The follow-up protocol, PROTOCOL_STATE_FIX.md, was written after the initial experiment. All 30 original-prompt episodes enter a paired offline replay. Each pair has identical initial state, recorded actions, observations, terminal error and model-call count. The original accessor and a subclass implementing exactly the proposed fix read the same data. This is an offline software intervention, not 30 new live agent runs.')
table([
    ['Replay outcome','Original accessor','Preserving accessor'],
    ['Observed-placement episodes retaining their board','0 / 8','8 / 8'],
    ['All episodes retaining their last observation',f"{pct(FM['original_retains_last_observed']['mean'])}",f"{pct(FM['fixed_retains_last_observed']['mean'])}"],
    ['Mean final character accuracy',f"{pct(FM['original_character_accuracy']['mean'])}",f"{pct(FM['fixed_character_accuracy']['mean'])} +/- {100*FM['fixed_character_accuracy']['sample_sd']:.2f} pp"],
    ['Mean final word accuracy','0.00%','0.00%'],
    ['Terminal validation-error episodes','30 / 30','30 / 30'],
    ['New model calls for replay','0','0'],
],[230,140,140])
rows=[['Seed','Original character acc.','Preserved character acc.']]
for trial in F['trials']:
    rows.append([trial['seed'],pct(trial['original_character_accuracy']),pct(trial['fixed_character_accuracy'])])
table(rows,[70,220,220])
p(f"Across three seed-level averages, preserved character accuracy has sample SD {100*FM['fixed_character_accuracy']['sample_sd']:.3f} pp and sample variance {10000*FM['fixed_character_accuracy']['sample_variance']:.3f} pp^2. In the 22 episodes without an executed placement, both accessors correctly return the initial board. The recovered score reflects previously observed letters, not newly improved word proposals.")
p('A separate deterministic test fills five rows with known benchmark answers, verifies the official checker reaches 100%, then appends a synthetic error step. The original accessor drops to the blank initial board, while the fix retains the solved board and the error flag. This validates environment behavior and the accessor mechanism. Because it uses the answer key, it is explicitly excluded from LLM performance results.')
page()

heading('7. Debug diary and reproducibility audit')
table([
    ['Blocker or risk','Resolution and evidence'],
    ['Restricted network access','Downloaded the public repository and model with explicit network approval. Inference runs locally after assets are available.'],
    ['Model download truncation','Checked expected safetensors byte length against the tensor header. Resumed via checked byte ranges and recorded a SHA256 manifest.'],
    ['Large dependency graph','Stopped broad installation and used a chain-only environment plus two lazy-import adaptations. Both experimental conditions share these adaptations.'],
    ['Metric implementation risk','Added an independent grid evaluator and four hand-checked tests. Checked every final score and per-call total against saved evidence.'],
    ['Random outcomes','Prespecified three seeds, saved decoding settings and report seed-level variability.'],
    ['Incomplete run recovery','Episode files support resumption. Interrupted call logs are preserved separately and excluded from completed episode totals.'],
    ['Lost terminal observation','Traced the reset to EnvState.env_state after an error step. Paired replay and a deterministic answer-key software test isolate and verify the fix.'],
],[145,365])
p('The repository contains the pre-experiment protocol, the pinned upstream revision, the runtime patch, install/run commands, the exact prompt change, model and dataset hashes, the resolved environment, completed episode logs and independently audited summaries. Each raw call records its prompt, response, decoding settings and token counts. No API keys are needed for this local setup.')
heading('8. Limits of the conclusions')
p('The paper uses a stronger hosted model and 30 examples, while this study uses a quantized local 3B model and ten examples. The paper does not specify the exact Crosswords subset IDs or full chain setup in the experimental appendix. The experiment therefore cannot isolate the source of a paper-to-local accuracy gap. It also does not reproduce the paper\'s MCTS comparison or the separate action-diversity experiment.')
p('The unsuccessful prompt study has an accuracy floor and a high invalid-proposal rate, so it cannot determine whether letter-consistency guidance helps a capable solver. The follow-up fix has stronger software evidence because identical observations isolate the accessor change. However, it repairs reporting only, and offline replay cannot establish a benefit to future live trajectories. Three seeds and ten related puzzles remain a small descriptive sample.')
p('Local latency depends on the laptop workload and includes call overhead. The hardware and model differ from the paper, so its dollar costs and timing values should not be compared numerically with the local timing results.')
page()

heading('9. Conclusions and future use')
p(f"The authors' chain workflow executed {S['episodes']} measured episodes with a free local model. Both prompt conditions obtained zero final word accuracy, so the paper's numerical performance did not reproduce in this setup. The logged trajectories reproduce executable action, transition and validation behavior and expose a terminal-state reporting defect. One isolated accessor modification restores the observed board in all {F['changed_board_episodes']} affected original-prompt episodes, recovering {pct(FM['fixed_character_accuracy']['mean'])} mean character accuracy. Word accuracy and the validation-failure rate remain unchanged.")
p('For future users, first validate the dataset and action format on an excluded puzzle. Pin the code and model, keep invalid attempts in cost totals, and inspect the last actual observation when an agent terminates with an error. Apply the included snapshot-preservation patch as a reporting correction. Improve the local model or output constraint separately, since combining that change with the accessor fix would obscure which intervention produced an effect.')
heading('Reproduction commands')
for line in ['python scripts/setup_runtime.py','python scripts/download_assets.py','python scripts/run_experiment.py --pilot','python scripts/run_experiment.py','python scripts/analyze_results.py','python scripts/replay_state_fix.py','python scripts/test_scoring.py']:
    p(line,small=True)
p('Run commands inside the documented environment from the repository root. The first setup step retrieves the exact upstream revision and applies the saved infrastructure patch. The README gives the installation commands and the supported Apple Silicon runtime. The evidence audit can run without loading a language model.')
heading('References')
p('[1] Xinzhe Li and Yaguang Tao. 2026. LiTS: A Modular Framework for LLM Tree Search. ACL System Demonstrations, pp. 47-56. https://aclanthology.org/2026.acl-demo.5/',small=True)
p('[2] LiTS authors. Source repository and included Crosswords benchmark. https://github.com/xinzhel/lits-llm. Exact revision recorded in config.json.',small=True)
p('[3] Qwen Team. Qwen2.5-3B-Instruct. https://huggingface.co/Qwen/Qwen2.5-3B-Instruct. Local quantized distribution: https://huggingface.co/mlx-community/Qwen2.5-3B-Instruct-4bit. Exact revision and file hashes recorded in model_manifest.json.',small=True)
heading('Assistance disclosure')
p('This submission package was prepared with AI assistance for code, experiment execution, analysis and writing. The included logs record actual local model calls.',small=True)

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#ccd9e2'));canvas.line(48,40,547,40)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526a7b'))
    canvas.drawString(48,27,f"FTEC5660  /  WU Yile  /  1155269932")
    canvas.drawRightString(547,27,str(doc.page));canvas.restoreState()

doc=SimpleDocTemplate(str(OUT/'Reproducibility_Report.pdf'),pagesize=(595.28,841.89),
                      leftMargin=43,rightMargin=42,topMargin=43,bottomMargin=55,
                      title='Reproducing LiTS Crosswords',author=IDENTITY['name'])
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'Reproducibility_Report.md').write_text('\n'.join(markdown))

print('Built report and editable source from audited measurements.')
