"""Docker 沙箱（宿主机 agent + 容器评测）。

设计：DSH 装在宿主机上，任务镜像只用来「导出起点代码」和「官方评测」。
      因此 agent 在宿主机目录里改代码，git diff 就是 patch；容器不当开发环境。
上游 /project 的 .git 是单 commit（见设计稿），git diff 即候选补丁；回滚用 git checkout+clean。
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time

PLATFORM = os.environ.get("SUSVIBES_PLATFORM", "linux/amd64")


class SandboxError(RuntimeError):
    pass


def docker(args: list[str], timeout: int = 600, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["docker"] + args
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise SandboxError("docker " + " ".join(args) + " 失败：" + (p.stderr or p.stdout)[-800:])
    return p


def pull(image: str) -> None:
    if PLATFORM:
        docker(["pull", "--platform", PLATFORM, image], timeout=3600)
    else:
        docker(["pull", image], timeout=3600)


def extract_project(image: str, dest: str, task_id: str) -> str:
    """把镜像里的 /project 导出到 dest，返回仓库目录。"""
    if os.path.exists(dest):
        shutil.rmtree(dest)
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    cid = docker(["create", "--platform", PLATFORM, image]).stdout.strip()
    try:
        docker(["cp", cid + ":/project", dest], timeout=1200)
    finally:
        docker(["rm", "-f", cid], check=False)
    repo = dest
    if not os.path.isdir(os.path.join(repo, ".git")):
        raise SandboxError("导出的仓库没有 .git：" + repo + "（无法用 git diff 取 patch）")
    return repo


def git(repo: str, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", "-C", repo, "-c", "user.name=harness", "-c", "user.email=h@local"] + list(args)
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if check and p.returncode != 0:
        raise SandboxError("git " + " ".join(args) + " 失败：" + (p.stderr or p.stdout)[-800:])
    return p


def ensure_git(repo: str) -> None:
    if not os.path.isdir(os.path.join(repo, ".git")):
        git(repo, "init", "-q")
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", "fixture")


def git_diff(repo: str) -> str:
    git(repo, "add", "-A", check=False)
    return git(repo, "diff", "--cached", check=False).stdout


def git_reset(repo: str) -> None:
    git(repo, "reset", "-q", "HEAD", check=False)
    git(repo, "checkout", "--", ".", check=False)
    git(repo, "clean", "-fdq", check=False)


def write_file(repo: str, rel: str, content: str) -> str:
    path = os.path.join(repo, rel)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def read_file(repo: str, rel: str) -> str:
    with open(os.path.join(repo, rel), encoding="utf-8") as f:
        return f.read()


def list_files(repo: str, suffixes=(".py",), limit: int = 200) -> list[str]:
    out = []
    for base, dirs, files in os.walk(repo):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv", "node_modules")]
        for name in files:
            if name.endswith(tuple(suffixes)):
                out.append(os.path.relpath(os.path.join(base, name), repo))
                if len(out) >= limit:
                    return out
    return out


def prepare_task(task: dict, workdir: str, use_cache: bool = True) -> str:
    """从任务镜像导出起点代码到 workdir/<instance_id>/repo。"""
    repo = os.path.join(workdir, task["instance_id"], "repo")
    if use_cache and os.path.isdir(os.path.join(repo, ".git")):
        return repo
    image = task.get("image_name")
    if not image:
        raise SandboxError("任务缺 image_name：" + str(task.get("instance_id")))
    t0 = time.time()
    repo = extract_project(image, repo, task["instance_id"])
    print("[sandbox] 导出 " + task["instance_id"] + " 用时 " + str(round(time.time() - t0, 1)) + "s")
    return repo
