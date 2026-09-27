import csv,json,hashlib
from collections import Counter,defaultdict
from pathlib import Path
src=Path(__file__).resolve().parent/'source_review.csv'
raw=src.read_bytes(); parsed=list(csv.reader(raw.decode('utf-8-sig').splitlines()))
header=parsed[0]; rows=[]; repairs=[]
for line,r in enumerate(parsed[1:],2):
    if len(r)>9:
        repairs.append({'line':line,'action':'Rejoined excess final columns with commas to recover the unquoted human note','original_column_count':len(r)})
        r=r[:8]+[','.join(r[8:])]
    if len(r)!=9: raise ValueError((line,len(r)))
    row=dict(zip(header,r)); row['source_line']=line
    rating=r[7].strip().lower()
    if rating=='usnure':
        repairs.append({'line':line,'action':'Normalized usnure to unsure for analysis; original preserved'})
        rating='unsure'
    assert rating in ('','0','1','2','unsure')
    row['normalized_rating']=rating; rows.append(row)
groups=defaultdict(list); unique=defaultdict(list)
for r in rows:
    groups[(r['anonymous_run_id'],r['anonymous_group_id'])].append(r)
    unique[(r['anonymous_run_id'],r['anonymous_group_id'],r['node_id'])].append(r)
def stats(rs):
    c=Counter(r['normalized_rating'] for r in rs)
    rated=len(rs)-c['']; numeric=c['0']+c['1']+c['2']
    return {'displayed_rows':len(rs),'recorded_ratings':rated,'blank_rows':c[''],'rating_0':c['0'],'rating_1':c['1'],'rating_2':c['2'],'unsure':c['unsure'],'numeric_ratings':numeric,'numeric_rating_2_percent':100*c['2']/numeric if numeric else None}
runstats={}; groupstats=[]
for run in sorted({r['anonymous_run_id'] for r in rows}):
    rs=[r for r in rows if r['anonymous_run_id']==run]; s=stats(rs)
    gs=[v for (a,b),v in groups.items() if a==run]
    s.update(total_groups=len(gs),groups_with_ratings=sum(any(r['normalized_rating'] for r in g) for g in gs),groups_with_multiple_values=sum(len({r['normalized_rating'] for r in g if r['normalized_rating']})>1 for g in gs))
    s['sample_kind']={k:stats([r for r in rs if r['sample_kind']==k]) for k in ('central','random','peripheral')}
    runstats[run]=s
for (run,gid),rs in sorted(groups.items()):
    groupstats.append({'run':run,'group_id':gid,'group_size':int(rs[0]['group_size']),**stats(rs),'distinct_recorded_values':sorted({r['normalized_rating'] for r in rs if r['normalized_rating']}),'notes':[{'source_line':r['source_line'],'node_id':r['node_id'],'rating':r['normalized_rating'],'text':r['human_notes_blank']} for r in rs if r['human_notes_blank'].strip()]})
duplicates=[]; dedup=Counter(); populated_keys=0
for key,rs in unique.items():
    ratings=[r['normalized_rating'] for r in rs if r['normalized_rating']]
    if not ratings: continue
    populated_keys+=1; values=set(ratings)
    if len(values)==1: dedup[next(iter(values))]+=1
    else: dedup['unresolved_multiple_values']+=1
    if len(ratings)>1: duplicates.append({'run':key[0],'group_id':key[1],'node_id':key[2],'source_lines':[r['source_line'] for r in rs if r['normalized_rating']],'ratings':ratings})
summary={'source':str(src),'sha256':hashlib.sha256(raw).hexdigest(),'reviewer':'Adnan, project developer; anonymous run labels; guided discussion occurred; not independent expert review','unit':'Recorded rating entry; scope mixes member-level and group-level judgments','repairs':repairs,'overall':stats(rows),'runs':runstats,'groups':groupstats,'duplicate_rated_node_keys':duplicates,'dedup_sensitivity':{'unique_run_group_node_keys_with_rating':populated_keys,'counts':dict(dedup)},'original_source_unchanged':True}
out=Path(__file__).resolve().parent
(out/'metrics.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
(out/'annotations_audit.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
def table(headers,body): return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in body])
t=stats(rows)
parts=['# Quantitative developer review of the 2020 hierarchy','Prepared 26 September 2026. Reviewer: Adnan, project developer. Anonymous configurations A/B/C were retained; the identity key was not opened for this analysis.',
'## What this report measures',
'This is a quantitative descriptive analysis of recorded developer judgments, supplemented by qualitative notes. The reviewer reports inspecting most groups. Some entries concern individual members; others summarize groups. Consequently, the primary unit is a **recorded rating entry**, not a uniformly assessed group or an independent node. No missing rating is interpreted as positive, negative, or uninspected. The counts are exact for the provided file, but they do not establish a population-level coherence rate or a ranking of clustering configurations.',
'## Main findings',
f'The sheet contains {len(rows)} displayed rows: 36 groups, 12 per run, with 15 central/random/peripheral sample rows per group. There are {t["recorded_ratings"]} filled ratings (22.2% of displayed rows), spanning 22/36 groups (61.1%). The other 14 groups have no recorded rating. This is documentation coverage, not a claim about how much the reviewer read. Each row is a sampled example, not necessarily a unique node; these samples do not cover every node in the original graph.',
table(['Run','Displayed rows','Rated entries','Groups with entries / 12','0','1','2','Unsure'],[[run,s['displayed_rows'],s['recorded_ratings'],s['groups_with_ratings'],s['rating_0'],s['rating_1'],s['rating_2'],s['unsure']] for run,s in runstats.items()]+[['Total',540,t['recorded_ratings'],'22 / 36',t['rating_0'],t['rating_1'],t['rating_2'],t['unsure']]]),
'## Rating distribution',
'The intended rubric was 0 = no clear coherence, 1 = broad/mixed coherence, 2 = clear coherence, and unsure = insufficient confidence. The mixed rating scope means these labels apply to recorded judgments, not automatically to whole groups.',
table(['Recorded rating','Count','Share of all 120 entries','Share of 95 numeric entries'],[[v,t[k],f'{100*t[k]/t["recorded_ratings"]:.1f}%',f'{100*t[k]/t["numeric_ratings"]:.1f}%' if v!='unsure' else 'Excluded'] for v,k in [('0','rating_0'),('1','rating_1'),('2','rating_2'),('unsure','unsure')]]),
'Of the 95 numeric entries, 88 (92.6%) are 1 or 2. This indicates broad/mixed or clear coherence in those recorded judgments; **it must not be described as 92.6% of groups being coherent**. Clear-coherence ratings account for 38/95 (40.0%) of numeric entries. Uncertainty remains substantial: 25/120 (20.8%) entries are unsure. No ordinal-score average is needed to describe this distribution.',
'## Central, random and peripheral entries',
'These are sampling categories, not separate independent experiments. Central/peripheral selection uses the clustering representation. Counts show how annotation is distributed; they do not establish causal effects of member position.',
table(['Run','Sample kind','Rated','0','1','2','Unsure'],[[run,k,s['recorded_ratings'],s['rating_0'],s['rating_1'],s['rating_2'],s['unsure']] for run,v in runstats.items() for k,s in v['sample_kind'].items()]),
'## Repeated members and mixed judgments',
f'After grouping recorded entries by (run, group, node ID), {populated_keys} distinct keys have ratings. This grouping is a duplicate audit, not a conversion into node-level truth: a rating on that row may summarize its whole group.',
table(['Deduplicated-key status','Count'],sorted(dedup.items())),
'Repeated samples with identical ratings are counted once in the sensitivity audit. Different ratings for the same key are retained as unresolved; none are averaged or arbitrarily selected. The primary 120-entry table intentionally retains every annotation, including repeated sample positions.',
table(['Run','Group','Node','Recorded values','CSV lines'],[[d['run'],d['group_id'],d['node_id'],', '.join(d['ratings']),', '.join(map(str,d['source_lines']))] for d in duplicates]),
'Nine groups have more than one distinct recorded value (seven in A and two in C). Different values within a group can legitimately express variation between members. They should not automatically be called reviewer conflicts. The 13 groups with a single distinct value likewise cannot automatically be treated as 13 explicit whole-group judgments.',
'## Qualitative interpretation',
'The notes identify plausible themes involving molecular/crystal machine learning, amorphous carbon, materials properties, fracture, and software ecosystems. They also identify uncertainty about author collections, generic chemical names, shared keywords, and relations between platform-specific evidence. Some positive numeric ratings accompany tentative language; values were preserved rather than silently recoded. Notes reflect the reviewer’s understanding and were not treated as independently verified scientific facts.',
'The review is evidence that the developer inspected outputs and identified both plausible connections and possible failures. It does not measure label overclaim: that requires assessing specific generated assertions against source evidence. Coherence annotations must not be substituted for label-faithfulness scores.',
'## Limitations and appropriate claims',
'1. Reviewer is the developer, not an independent domain expert; the review was supported by discussion with an assistant. Configuration identities were concealed using anonymous labels, but this does not remove developer familiarity or confirmation bias.\n2. Member-level and group-level rating scope was not recorded consistently. No scope was inferred solely from one or several ratings in a group.\n3. Annotation density differs markedly by run and by sampling category. There is no defensible best-run ranking from these counts.\n4. Missing entries were left missing, and unsure was not converted to zero.\n5. Examples were selected by central/random/peripheral sampling and may repeat nodes; they are not a simple random sample of all corpus nodes.\n6. No human-rated null partition or second reviewer is present. This review complements, rather than replaces, the separate automated null-model evaluation.\n7. No confidence interval or significance test is reported: treating mixed-scope, dependent entries as independent trials would imply unsupported precision.',
'## CSV integrity and reproducibility',
'The original Downloads CSV was not modified. One row (CSV line 2) contains an unquoted comma in the final note, producing a tenth column. The analysis rejoined the final fragments with a comma to preserve the note. One rating spelled usnure was normalized to unsure. All original fields, source line numbers, normalized ratings, and complete notes are retained in annotations_audit.json. All per-group counts and duplicate diagnostics are in metrics.json.',
f'Source SHA-256: `{summary["sha256"]}`',
'## Text suitable for the assessment report',
'> A developer review was conducted using anonymously labelled outputs from three 2020 clustering configurations. The sheet contained 540 sampled-member rows across 36 top-level groups. The developer recorded 120 ratings spanning 22 groups: 38 ratings of 2, 50 of 1, 7 of 0, and 25 unsure. Among the 95 numeric annotations, 40.0% received the highest rating and 92.6% received either 1 or 2. These are descriptive annotation proportions, not group-level coherence rates: the reviewer mixed member-level and group-level judgments, and annotation density differed across configurations. Qualitative notes identified recognizable themes alongside uncertainty about author collections, keyword-driven similarity, and peripheral members. The review is reported as developer error analysis with quantitative annotation summaries; it does not establish a winning configuration or an independently validated semantic-coherence rate.',
'## Per-group audit',
'Rows are ordered by anonymous run and group ID. Multiple distinct values are preserved, not treated as an error by default.',
table(['Run','Group','Original group size','Filled rows / 15','0','1','2','Unsure','Distinct values'],[[g['run'],g['group_id'],g['group_size'],g['recorded_ratings'],g['rating_0'],g['rating_1'],g['rating_2'],g['unsure'],', '.join(g['distinct_recorded_values']) or 'Missing'] for g in groupstats])]
(out/'developer_review_report.md').write_text('\n\n'.join(parts)+'\n',encoding='utf-8')
print(json.dumps({'overall':t,'runs':runstats,'dedup':summary['dedup_sensitivity'],'repairs':repairs},indent=2))
