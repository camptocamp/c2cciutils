#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess  # nosec

import multi_repo_automation as mra
import ruamel.yaml.comments

import c2cciutils


def main() -> None:
    """Create a new version with its stabilization branch."""

    args_parser = argparse.ArgumentParser(
        description="Create a new version with its stabilization branch",
        usage="""
This will:
- Stash all your changes
- Checkout the master branch
- Pull it from origin
- Push it to a new stabilization branch
- Checkout a new branch named new-version
- Do the changes for the new version
  - Update the SECURITY.md config
  - Update the Renovate config
  - Update the audit workflow
  - Create the backport label
- Push it
- Create a pull request
- Go back to your old branch

If you run the tool without any version it will check that everything is OK regarding the SECURITY.md available on GitHub.
    """,
    )
    args_parser.add_argument(
        "--version",
        help="The version to create",
    )
    args_parser.add_argument(
        "--force",
        action="store_true",
        help="Force create the branch and push it",
    )
    args_parser.add_argument(
        "--supported-until",
        help="The date until the version is supported, can also be To be defined or Best effort",
        default="Best effort",
    )
    args_parser.add_argument(
        "--upstream-supported-until",
        help="The date until the version is supported upstream",
    )
    arguments = args_parser.parse_args()

    # Get the repo information e.g.:
    # {
    #     "name": "camptocamp/c2cciutils",
    #     "remote": "origin",
    #     "dir": "/home/user/src/c2cciutils",
    # }
    # can be override with a repo.yaml file
    repo = mra.get_repo_config()

    # Stash all your changes
    subprocess.run(["git", "stash", "--all", "--message=Stashed by release creation"], check=True)
    old_branch_name = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        stdout=subprocess.PIPE,
        check=True,
    ).stdout.strip()

    # Checkout the master branch
    subprocess.run(["git", "checkout", repo.get("master_branch", "master")], check=True)

    # Pull it from origin
    subprocess.run(
        ["git", "pull", repo.get("remote", "origin"), repo.get("master_branch", "master")], check=True
    )

    # Push it to a new stabilization branch
    if arguments.version:
        subprocess.run(
            [
                "git",
                "push",
                *(["--force"] if arguments.force else []),
                repo.get("remote", "origin"),
                f"HEAD:{arguments.version}",
            ],
            check=not arguments.force,
        )

    version = arguments.version
    branch_name = "new-version" if version is None else f"new-version-{version}"

    # Checkout a new branch named new-version
    if arguments.force:
        subprocess.run(["git", "branch", "-D", branch_name])  # pylint: disable=subprocess-run-check
    subprocess.run(["git", "checkout", "-b", branch_name], check=True)

    # # # Do the changes for the new version # # #

    remotes = [r for r in mra.run(["git", "remote"], stdout=subprocess.PIPE).stdout.split() if r != ""]
    remote_branches = [
        b.strip()[len("remotes/") :]
        for b in mra.run(["git", "branch", "--all"], stdout=subprocess.PIPE).stdout.split()
        if b != "" and b.strip().startswith("remotes/")
    ]
    if "upstream" in remotes:
        remote_branches = [b[len("upstream") + 1 :] for b in remote_branches if b.startswith("upstream/")]
    elif "origin" in remotes:
        remote_branches = [b[len("origin") + 1 :] for b in remote_branches if b.startswith("origin/")]
    else:
        remote_branches = ["/".join(b.split("/")[1:]) for b in remote_branches]

    config = c2cciutils.get_config()
    branch_re = c2cciutils.compile_re(config["version"].get("branch_to_version_re", []))
    branches_match = [c2cciutils.match(b, branch_re) for b in remote_branches]
    version_branch = {m.groups()[0] if m.groups() else b: b for m, c, b in branches_match if m is not None}

    stabilization_branches = [
        version_branch.get(version, version) for version in mra.get_stabilization_versions(repo)
    ]
    modified_files = []

    if version:
        stabilization_branches.append(version)

        if os.path.exists("SECURITY.md"):
            modified_files.append("SECURITY.md")
            with mra.Edit("SECURITY.md") as security_md:
                security_md_lines = security_md.data.split("\n")
                index = -1
                for i, line in enumerate(security_md_lines):
                    if line.startswith("| "):
                        index = i

                new_line = f"| {version} | {arguments.supported_until} |"
                if arguments.upstream_supported_until:
                    new_line += f" {arguments.upstream_supported_until} |"

                security_md.data = "\n".join(
                    [*security_md_lines[: index + 1], new_line, *security_md_lines[index + 1 :]]
                )

    stabilization_branches_with_master = [*stabilization_branches, repo.get("master_branch", "master")]

    for labels in mra.gh_json("label", ["name"], "list"):
        if labels["name"].startswith("backport "):
            if labels["name"].replace("backport ", "") not in stabilization_branches_with_master:
                mra.gh("label", "delete", labels["name"], "--yes")

    for branch in stabilization_branches_with_master:
        mra.gh(
            "label",
            "create",
            "--force",
            f"backport {branch}",
            "--color=5aed94",
            f"--description=Backport the pull request to the '{branch}' branch",
        )

    if os.path.exists(".github/renovate.json5"):
        modified_files.append(".github/renovate.json5")
        with mra.EditRenovateConfig(".github/renovate.json5") as renovate_config:
            if stabilization_branches:
                if "baseBranches: " in renovate_config.data:
                    renovate_config.data = re.sub(
                        r"(.*baseBranches: )\[[^\]]*\](.*)",
                        rf"\1{json.dumps(stabilization_branches_with_master)}\2",
                        renovate_config.data,
                    )
                else:
                    renovate_config.add(
                        f"baseBranches: {json.dumps(stabilization_branches_with_master)},\n", "baseBranches"
                    )

    if stabilization_branches and os.path.exists(".github/workflows/audit.yaml"):
        modified_files.append(".github/workflows/audit.yaml")
        with mra.EditYAML(".github/workflows/audit.yaml") as yaml:
            for job in yaml["jobs"].values():
                matrix = job.get("strategy", {}).get("matrix", {})
                if "include" in matrix and version:
                    new_include = dict(matrix["include"][-1])
                    new_include["branch"] = version
                    matrix["include"].append(new_include)

                if "branch" in matrix and stabilization_branches:
                    yaml_stabilization_branches = ruamel.yaml.comments.CommentedSeq(stabilization_branches)
                    yaml_stabilization_branches._yaml_add_comment(  # pylint: disable=protected-access
                        [
                            ruamel.yaml.CommentToken("\n\n", ruamel.yaml.error.CommentMark(0), None),
                            None,
                            None,
                            None,
                        ],
                        len(stabilization_branches) - 1,
                    )
                    job["strategy"]["matrix"]["branch"] = yaml_stabilization_branches

    # Commit the changes
    message = f"Create the new version '{version}'" if version else "Update the supported versions"
    if os.path.exists(".pre-commit-config.yaml"):
        subprocess.run(["pre-commit", "run", "--color=never", "--all-files"], check=False)
    subprocess.run(["git", "add", *modified_files], check=True)
    subprocess.run(["git", "commit", f"--message={message}"], check=True)

    # Push it
    subprocess.run(
        [
            "git",
            "push",
            *(["--force"] if arguments.force else []),
            repo.get("remote", "origin"),
            branch_name,
        ],
        check=True,
    )

    # Create a pull request
    url = mra.gh(
        "pr",
        "create",
        f"--title={message}",
        "--body=",
        f"--head={branch_name}",
        f"--base={repo.get('master_branch', 'master')}",
    ).strip()

    # Go back to your old branch
    subprocess.run(["git", "checkout", old_branch_name, "--"], check=True)

    if url:
        subprocess.run([mra.get_browser(), url], check=True)
    else:
        mra.gh("browse")


if __name__ == "__main__":
    main()
