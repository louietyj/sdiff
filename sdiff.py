import argparse
import re
import subprocess
from typing import Dict, List, Tuple


def run_print(cmd: List[str]) -> None:
    print(">>", " ".join(cmd))
    subprocess.check_output(cmd)


def get_commits(branch_base: str) -> Dict[int, Tuple[str, str]]:
    commit_hashes = (
        subprocess.check_output(
            ["git", "log", f"{branch_base}-MASTER", "--not", "main", "--format=%H"]
        )
        .decode()
        .strip()
        .split("\n")
    )
    commit_msgs = (
        subprocess.check_output(
            ["git", "log", f"{branch_base}-MASTER", "--not", "main", "--format=%s"]
        )
        .decode()
        .strip()
        .split("\n")
    )
    found_commits: Dict[int, Tuple[str, str]] = {}
    for commit_hash, commit_msg in zip(commit_hashes, commit_msgs):
        match = re.match(r"\[(\d+)/n\].*", commit_msg)
        if match:
            found_commits[int(match[1])] = (commit_hash, commit_msg)
    return found_commits


def get_branches(branch_base: str) -> Dict[int, str]:
    all_branches = (
        subprocess.check_output(
            ["git", "branch", "--list", "--format=%(refname:short)"]
        )
        .decode()
        .strip()
        .split("\n")
    )
    found_branches: Dict[int, str] = {}
    for branch in all_branches:
        match = re.match(f"{branch_base}-(\\d+)(-.*)?", branch)
        if match:
            found_branches[int(match[1])] = branch
    return found_branches


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("branch_base")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    found_commits = get_commits(args.branch_base)
    found_branches = get_branches(args.branch_base)
    if set(found_commits) != set(found_branches):
        raise Exception(
            "Mismatched branches / commits: "
            + str(set(found_commits).symmetric_difference(set(found_branches)))
        )
    for i in sorted(found_commits):
        print(found_branches[i], "->", found_commits[i][1])
    if input("Confirm [y/n]: ").strip() == "y":
        for i in sorted(found_commits):
            run_print(["git", "branch", "-f", found_branches[i], found_commits[i][0]])
        run_print(
            ["git", "push", "origin"]
            + list(found_branches.values())
            + [f"{args.branch_base}-MASTER", "--force-with-lease"]
        )


if __name__ == "__main__":
    main()
