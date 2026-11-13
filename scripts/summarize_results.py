import os
import json
import glob

results_root = r'C:\Users\zhangxiaoji\.gemini\antigravity\scratch\vibe-coding-recurrence-benchmark\results'
models = ['qwen2.5coder_7b', 'deepseek-flash']

for m in models:
    print(f"\n================ MODEL: {m} ================")
    mdir = os.path.join(results_root, m)
    for f in sorted(glob.glob(os.path.join(mdir, '*.json'))):
        cname = os.path.basename(f).replace('.json', '')
        with open(f, 'r', encoding='utf-8') as fp:
            d = json.load(fp)
        rounds_stat = []
        for r in d['rounds']:
            sec_icon = 'PASS' if r['probe_pass'] else 'FAIL'
            fn_icon = 'PASS' if r['func_pass'] else 'FAIL'
            st = r['recurrence_status']
            rounds_stat.append(f"R{r['round']}:({fn_icon}|{sec_icon}|{st})")
        print(f"{cname:<28} -> " + " | ".join(rounds_stat))
