import os
import sys
import json
from pathlib import Path

# Add harness to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "harness"))
from eval_driver import evaluate_case, CASES_DIR

CASES = [
    "case1_cwe22_file_storage",
    "case2_cwe89_sql_query",
    "case3_cwe78_cmd_injection",
    "case4_cwe79_xss_template",
    "case5_cwe918_ssrf_webhook"
]

def run_suite(model: str):
    print(f"\n=======================================================")
    print(f"   RUNNING EXPERIMENTAL SUITE: {model}")
    print(f"=======================================================")
    
    results = {}
    for case_id in CASES:
        try:
            res = evaluate_case(model, case_id)
            results[case_id] = res
        except Exception as e:
            print(f"[!] Error on {case_id}: {e}")
            results[case_id] = {"error": str(e)}

    return results

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "deepseek-v4-pro"
    run_suite(model)
