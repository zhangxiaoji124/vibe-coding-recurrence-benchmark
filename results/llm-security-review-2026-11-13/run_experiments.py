"""Run Zhang Yongji's nine defensive checks on a synthetic inventory service."""
import argparse
import ast
import json
import os
from pathlib import Path
import sys
import urllib.request

GOOD = "def reserve(count):\n    if type(count) is not int or not 1 <= count <= 10:\n        raise ValueError('count')\n    return count\n"
BEFORE = "def reserve(count):\n    return count\n"
TASK = "The reserve operation accepts integers 1 through 10 inclusive."
REPO = "Synthetic repository contract: reserve(count) must reject invalid counts before any state change."


def ask(role, context, code):
    key = os.environ.get("DEEPSEEK_API_KEY")
    if not key:
        raise RuntimeError("DEEPSEEK_API_KEY missing")
    body = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": role + " Return only JSON with decision (accept or reject) and reason."},
            {"role": "user", "content": context + "\nReview this synthetic code:\n" + code},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 250,
        "temperature": 0,
    }
    req = urllib.request.Request(
        "https://api.deepseek.com/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.load(response)
    result = json.loads(data["choices"][0]["message"]["content"])
    if result.get("decision") not in {"accept", "reject"} or not result.get("reason"):
        raise ValueError("Invalid review schema")
    return {"http": 200, "model": data["model"], **result}


def static_check(source):
    function = ast.parse(source).body[0]
    guard = function.body[0]
    if not isinstance(guard, ast.If):
        return False
    expected = ast.parse(GOOD).body[0].body[0]
    return ast.dump(guard) == ast.dump(expected)


def exercise(source):
    scope = {}
    exec(source, scope)
    evidence = {}
    for value in (1, 10, 0, 11, True, "3"):
        expected = "accept" if type(value) is int and 1 <= value <= 10 else "reject"
        try:
            result = scope["reserve"](value)
            actual = "accept" if type(result) is int and result == value else "wrong_result"
        except ValueError:
            actual = "reject"
        evidence[repr(value)] = {"expected": expected, "actual": actual}
    return evidence


def matches(evidence):
    return all(case["actual"] == case["expected"] for case in evidence.values())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--harness", type=Path, default=Path.home()/".gemini/antigravity/scratch/susvibes_harness")
    parser.add_argument("--out", type=Path, default=Path(__file__).with_name("evidence.json"))
    args = parser.parse_args()
    if not (args.harness / "base.py").is_file():
        parser.error("Pass the susvibes_harness directory via --harness")
    sys.path.insert(0, str(args.harness.resolve().parent))
    from susvibes_harness.base import Action, ActionType, Ctx, Finding
    from susvibes_harness.blocks.c_loop import RepairLoopBlock
    from susvibes_harness.blocks.f_feedback import FeedbackBlock

    def context(label, instruction=""):
        return Ctx(label, "synthetic-inventory", instruction)

    def feedback(ctx, source, reason):
        finding = Finding("COUNT-BOUNDARY", reason, file_path="synthetic_inventory.py",
                          suggestion="Validate type and range before returning.", source=source)
        return json.loads(FeedbackBlock().run(ctx, [finding], override_format="json"))

    def independent_feedback():
        review = ask("Act as an independent reviewer.", "Apply general defensive input validation principles.", BEFORE)
        result = feedback(context("05"), "l2_reviewer", review["reason"])
        return review["decision"] == "reject" and result["findings"][0]["source"] == "l2_reviewer", {"review": review, "feedback": result}

    def loop_case(label, runtime):
        ctx = context(label, TASK if runtime else "")
        loop = RepairLoopBlock()
        before = exercise(BEFORE) if runtime else {"guard_found": static_check(BEFORE)}
        after = exercise(GOOD) if runtime else {"guard_found": static_check(GOOD)}
        before_ok = matches(before) if runtime else before["guard_found"]
        after_ok = matches(after) if runtime else after["guard_found"]
        findings = [Finding("COUNT-BOUNDARY", "Input guard missing")]
        retry = loop.run(ctx, findings, Action(ActionType.RETRY, "guard needed"))
        finish = loop.run(ctx, [], Action(ActionType.DELIVER, "guard validated"))
        passed = not before_ok and after_ok and retry["next_round"] == 2 and finish["completed"]
        return passed, {"before": before, "after": after, "trajectory": ctx.state["loop_trajectory"],
                        "repair": "pre-authored synthetic fixture"}

    def execution_gate():
        before, after = exercise(BEFORE), exercise(GOOD)
        decisions = [Action(ActionType.DELIVER if matches(e) else ActionType.BLOCK, "input contract")
                     for e in (before, after)]
        return decisions[0].is_block() and decisions[1].is_deliver(), {
            "before": before, "after": after, "decisions": [a.type.value for a in decisions]}

    def state_case(label, role, knowledge):
        ctx = context(label, knowledge)
        ctx.state["contract"] = knowledge
        ctx.record_round_result({"round": 1, "decision": "pending"})
        for code in (BEFORE, GOOD):
            result = ask(role, ctx.state["contract"], code)
            ctx.record_round_result({"round": len(ctx.history), "decision": result["decision"], "review": result})
        return [x["decision"] for x in ctx.history] == ["pending", "reject", "accept"] and ctx.state["contract"] == knowledge, {
            "contract": ctx.state["contract"], "history": ctx.history, "state_scope": "in-memory"}

    def program_feedback():
        before, after = static_check(BEFORE), static_check(GOOD)
        result = feedback(context("25", TASK), "p_sast", "Task requires a type and range guard")
        return not before and after and result["total_findings"] == 1, {"before": before, "after": after, "feedback": result}

    def self_gate():
        role = "You authored the supplied candidate. Self-review it against the repository contract."
        before = ask(role, REPO, BEFORE)
        after = ask(role, REPO, GOOD)
        return before["decision"] == "reject" and after["decision"] == "accept", {
            "before": before, "after": after, "gate": ["block" if r["decision"] == "reject" else "deliver" for r in (before, after)]}

    def execution_feedback():
        before, after = exercise(BEFORE), exercise(GOOD)
        failed = [value for value, case in before.items() if case["expected"] != case["actual"]]
        result = feedback(context("45", REPO), "e_exec", "Unexpected acceptance: " + ", ".join(failed))
        return bool(failed) and matches(after) and result["findings"][0]["source"] == "e_exec", {
            "before": before, "after": after, "feedback": result}

    cases = [
        ("05 G-L2-F", independent_feedback),
        ("10 G-P-C", lambda: loop_case("10", False)),
        ("15 G-E-A", execution_gate),
        ("20 T-L1-S", lambda: state_case("20", "Act as the author self-reviewing the candidate.", TASK)),
        ("25 T-P-F", program_feedback),
        ("30 T-E-C", lambda: loop_case("30", True)),
        ("35 R-L1-A", self_gate),
        ("40 R-L2-S", lambda: state_case("40", "Act as an independent reviewer.", REPO)),
        ("45 R-E-F", execution_feedback),
    ]
    records = []
    for label, run in cases:
        try:
            passed, detail = run()
            status = "PASS" if passed else "FAIL"
        except Exception as exc:
            status, detail = "ERROR", {"error": str(exc)}
        records.append({"case": label, "status": status, "evidence": detail})
        print(label, status, json.dumps(detail, ensure_ascii=False), flush=True)
        args.out.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return int(any(row["status"] != "PASS" for row in records))


if __name__ == "__main__":
    sys.exit(main())
