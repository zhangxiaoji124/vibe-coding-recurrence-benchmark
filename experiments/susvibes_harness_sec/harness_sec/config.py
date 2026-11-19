"""配置加载：优先 PyYAML；没装则用本文件里的迷你解析器（只支持本项目用到的子集）。

支持写法：
    arm: "011"
    m1: k2
    m2: [l2, p]
    m3: [f, c, a]
    params:
      max_retries: 2
"""
from __future__ import annotations

import json
import os


def _strip_comment(line: str) -> str:
    out, quote = [], None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _scalar(text: str):
    text = text.strip()
    if text == "":
        return None
    if text in ("null", "None", "~"):
        return None
    if text in ("true", "True"):
        return True
    if text in ("false", "False"):
        return False
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _parse_mini(text: str) -> dict:
    """迷你 YAML：支持
        key: value
        key: [a, b]
        key:
          - item
          - id: INV-1
            statement: ...
        params:
          max_retries: 2
    不支持多层嵌套字典（如 sast_map 的 bandit.B608.severity）——那是给 PyYAML 的。
    """
    data: dict = {}
    section = None
    list_key = None
    cur_item = None

    def _inline_list(val: str):
        inner = val[1:-1].strip()
        return [_scalar(x) for x in inner.split(",")] if inner else []

    for raw in text.splitlines():
        line = _strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        s = line.strip()

        if indent == 0:
            section, list_key, cur_item = None, None, None
            if s.endswith(":"):
                key = s[:-1].strip()
                data[key] = []          # 先当列表；出现 dict 子项时再转
                section, list_key = key, key
            elif ":" in s:
                k, v = s.split(":", 1)
                val = v.strip()
                data[k.strip()] = _inline_list(val) if (val.startswith("[") and val.endswith("]")) else _scalar(val)
            continue

        if section is None:
            continue

        if s.startswith("- "):
            if not isinstance(data[section], list):
                data[section] = []
            payload = s[2:].strip()
            if ":" in payload:
                k, v = payload.split(":", 1)
                item = {k.strip(): _scalar(v)}
                data[section].append(item)
                cur_item = item
            else:
                data[section].append(_scalar(payload))
                cur_item = None
            continue

        if ":" in s:
            k, v = s.split(":", 1)
            key_s, val = k.strip(), v.strip()
            if cur_item is not None:
                cur_item[key_s] = _scalar(val)
                continue
            if isinstance(data[section], list):
                if not data[section]:
                    data[section] = {}
                    list_key = None
                else:
                    continue
            if val == "":
                data[section][key_s] = []
                list_key = key_s
            elif val.startswith("[") and val.endswith("]"):
                data[section][key_s] = _inline_list(val)
                list_key = None
            else:
                data[section][key_s] = _scalar(val)
                list_key = None
    return data


def load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        text = f.read()
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text) or {}
        return data
    except Exception:
        return _parse_mini(text)


def load_arm(path: str) -> dict:
    """加载一个臂配置并做基本校验。"""
    cfg = load(path)
    if not isinstance(cfg, dict):
        raise ValueError("配置不是 dict：" + path)
    allowed = {"name", "arm", "recipe", "m1", "m2", "m3", "params", "task", "model", "notes"}
    unknown = set(cfg) - allowed
    if unknown:
        raise ValueError("配置里有未知字段 " + str(sorted(unknown)) + "（允许：" + str(sorted(allowed)) + "）")
    cfg.setdefault("name", os.path.splitext(os.path.basename(path))[0])
    cfg.setdefault("arm", cfg["name"])
    cfg.setdefault("params", {}) or {}
    return cfg


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)
