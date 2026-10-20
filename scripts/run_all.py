"""Orquestra todos os experimentos em contêineres Linux (Docker). Funciona em Windows, macOS e Linux.

    python scripts/run_all.py            # tudo
    python scripts/run_all.py env c1c2   # apenas alguns passos
Passos: env, c1c2, c3c4, c5scale, c5limit, c6, sync, evidence
"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG = "genresearch"
VOL = "genres_data"


def docker(args, stdout=None, check=True, extra=()):
    cmd = ["docker", "run", "--rm", "-v", f"{ROOT}:/work", "-v", f"{VOL}:/workdata",
           "-e", "REPS=" + os.environ.get("REPS", "3"), *extra, "-w", "/work/scripts", IMG, *args]
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, stdout=stdout, check=check)


def step_env():
    os.makedirs(f"{ROOT}/results/env", exist_ok=True)
    with open(f"{ROOT}/results/env/ambiente_container.txt", "w", encoding="utf-8") as f:
        docker(["bash", "env_capture.sh"], stdout=f)
    with open(f"{ROOT}/results/env/ambiente_host_docker.txt", "w", encoding="utf-8") as f:
        subprocess.run(["docker", "info"], stdout=f)
        subprocess.run(["docker", "version"], stdout=f)


def step_limit():
    """C5/C6 com limite de memória do cgroup. memory-swap == memory desliga o swap do contêiner."""
    docker(["python", "c5_pressure.py", "prepare", "1024"])
    out = f"{ROOT}/results/c5_limit"
    os.makedirs(out, exist_ok=True)
    cases = [("2048m", "2048m", "read"), ("2048m", "2048m", "mmap"),
             ("384m", "384m", "read"), ("384m", "384m", "mmap")]
    summary = []
    for mem, swap, mode in cases:
        for rep in (1, 2, 3):
            name = f"limit_{mem}_{mode}_rep{rep}"
            with open(f"{out}/{name}.jsonl", "w", encoding="utf-8") as f:
                p = docker(["python", "c5_pressure.py", "limit", "1024", mode], stdout=f, check=False,
                           extra=["--memory", mem, "--memory-swap", swap])
            summary.append({"memory_limit": mem, "swap_limit": swap, "mode": mode, "rep": rep,
                            "exit_code": p.returncode,
                            "oom_killed": p.returncode == 137})
    import csv
    with open(f"{ROOT}/results/c5_limit_summary.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)


STEPS = {
    "env": step_env,
    "c1c2": lambda: docker(["python", "c1_c2_read_mmap.py"]),
    "c3c4": lambda: docker(["python", "c3_c4_pipeline.py"]),
    "c5scale": lambda: docker(["python", "c5_pressure.py", "scale"]),
    "c5limit": step_limit,
    "c6": lambda: docker(["python", "c6_failures.py"]),
    "sync": lambda: docker(["python", "sync_demo.py"]),
    "evidence": lambda: docker(["bash", "evidence.sh"], extra=["--cap-add=SYS_PTRACE"]),
    "analyze": lambda: docker(["python", "analyze.py"]),
}

if __name__ == "__main__":
    for name in (sys.argv[1:] or list(STEPS)):
        print(f"\n===== {name} =====", flush=True)
        STEPS[name]()
