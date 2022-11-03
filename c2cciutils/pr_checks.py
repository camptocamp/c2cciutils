"""
The pull request checking functions.

Commits, messages and labels.
"""
import os
import re
import subprocess  # nosec
from tempfile import NamedTemporaryFile
from typing import Any, Dict, List, Optional

import requests
import yaml

import c2cciutils.configuration


def _commit_intro(need_separator: bool, commit: Dict[str, Any]) -> bool:
    head = commit["commit"]["message"].split("\n")[0]
    if need_separator:
        print("-" * 30)
    print(f'{commit["commit"]["tree"]["sha"]}: {head}')
    return True


def print_event(github_event: Dict[str, Any], **kwargs: Any) -> bool:
    """
    Print the github object.
    """
    del kwargs
    print(yaml.dump(github_event, default_flow_style=False, Dumper=yaml.SafeDumper))
    return True


def commits_messages(
    config: c2cciutils.configuration.PullRequestChecksCommitsMessagesConfiguration,
    commits: List[Dict[str, Any]],
    **kwargs: Any,
) -> bool:
    """
    Check the commits messages.

    - They should start with a capital letter.
    - They should not be too short.
    - They should not be a squash or fixup commit.
    - They should not be a merge commit.
    - They should not be a revert commit.
    """
    del kwargs

    need_separator = False
    success = True
    first_capital = re.compile(r"^[A-Z]")
    commit_hash = set()
    for commit in commits:
        need_head = True
        commit_hash.add(commit["sha"])
        message_lines = commit["commit"]["message"].split("\n")
        head = message_lines[0]
        if config.get(
            "check_fixup", c2cciutils.configuration.PULL_REQUEST_CHECKS_COMMITS_MESSAGES_FIXUP_DEFAULT
        ) and head.startswith("fixup! "):
            if need_head:
                need_separator = _commit_intro(need_separator, commit)
            need_head = False
            print("::error::Fixup message not allowed")
            success = False
        if config.get(
            "check_squash", c2cciutils.configuration.PULL_REQUEST_CHECKS_COMMITS_MESSAGES_SQUASH_DEFAULT
        ) and head.startswith("squash! "):
            if need_head:
                need_separator = _commit_intro(need_separator, commit)
            need_head = False
            print("::error::Squash message not allowed")
            success = False
        if (
            config.get(
                "check_first_capital",
                c2cciutils.configuration.PULL_REQUEST_CHECKS_COMMITS_MESSAGES_FIRST_CAPITAL_DEFAULT,
            )
            and first_capital.match(head) is None
        ):
            if need_head:
                need_separator = _commit_intro(need_separator, commit)
            need_head = False
            print("::error::The first letter of message head should be a capital")
            success = False
        min_length = config.get(
            "min_head_length",
            c2cciutils.configuration.PULL_REQUEST_CHECKS_COMMITS_MESSAGES_MIN_HEAD_LENGTH_DEFAULT,
        )
        if min_length > 0 and len(head) < min_length:
            if need_head:
                need_separator = _commit_intro(need_separator, commit)
            need_head = False
            print(f"The message head should be at least {min_length} characters long")
            success = False
        if (
            config.get(
                "check_no_merge_commits",
                c2cciutils.configuration.PULL_REQUEST_CHECKS_COMMITS_MESSAGES_NO_MERGE_COMMITS_DEFAULT,
            )
            and len(commit["parents"]) != 1
        ):
            if need_head:
                need_separator = _commit_intro(need_separator, commit)
            need_head = False
            print("::error::The merge commit are not allowed")
            success = False
        if config.get(
            "check_no_own_revert",
            c2cciutils.configuration.PULL_REQUEST_CHECKS_COMMITS_MESSAGES_NO_OWN_REVERT_DEFAULT,
        ) and (
            head.startswith("Revert ")
            and len(message_lines) == 3
            and message_lines[2].startswith("This reverts commit ")
        ):
            revert_commit_hash = message_lines[2][len("This reverts commit ") : -1]
            if revert_commit_hash in commit_hash:
                if need_head:
                    need_separator = _commit_intro(need_separator, commit)
                need_head = False
                print(f"Revert own commits is not allowed ({revert_commit_hash})")
                success = False
                continue
    return success


def commits_spell(
    config: c2cciutils.configuration.PullRequestChecksCommitsSpellingConfiguration,
    full_config: c2cciutils.configuration.Configuration,
    commits: List[Dict[str, Any]],
    **kwargs: Any,
) -> bool:
    """Check the spelling of the commits body."""
    del kwargs

    spellcheck_cmd = c2cciutils.get_codespell_command(full_config)

    success = True
    need_separator = False
    for commit in commits:
        with NamedTemporaryFile("w+t", encoding="utf-8", suffix=".yaml") as temp_file:
            if config.get(
                "only_head", c2cciutils.configuration.PULL_REQUEST_CHECKS_COMMITS_MESSAGES_ONLY_HEAD_DEFAULT
            ):
                head = commit["commit"]["message"].split("\n")[0]
                temp_file.write(head)
            else:
                temp_file.write(commit["commit"]["message"])
            temp_file.flush()
            spell = subprocess.run(  # nosec # pylint: disable=subprocess-run-check
                spellcheck_cmd + [temp_file.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            if spell.returncode != 0:
                need_separator = _commit_intro(need_separator, commit)
                print("::error::Code spell error")
                print(spell.stderr)
                print(spell.stdout)
                success = False
    return success


def pull_request_spell(
    config: c2cciutils.configuration.PullRequestChecksPullRequestSpellingConfiguration,
    full_config: c2cciutils.configuration.Configuration,
    github_event: Dict[str, Any],
    **kwargs: Any,
) -> bool:
    """Check the spelling of the pull request title and message."""
    del kwargs

    spellcheck_cmd = c2cciutils.get_codespell_command(full_config)

    with NamedTemporaryFile("w+t") as temp_file:
        temp_file.write(github_event["event"]["pull_request"]["title"])
        temp_file.write("\n")
        if not config.get(
            "only_head", c2cciutils.configuration.PULL_REQUEST_CHECKS_ONLY_HEAD_DEFAULT
        ) and github_event["event"]["pull_request"].get("body"):
            temp_file.write("\n")
            temp_file.write(github_event["event"]["pull_request"]["body"])
            temp_file.write("\n")
        temp_file.flush()
        spell = subprocess.run(  # nosec # pylint: disable=subprocess-run-check
            spellcheck_cmd + [temp_file.name], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        if spell.returncode != 0:
            print("::error::Code spell error in pull request")
            print(spell.stderr)
            print(spell.stdout)
            return False
    return True


def pull_request_labels(github_event: Dict[str, Any], **kwargs: Any) -> bool:
    """Check it the label are set correctly for the changelog generation."""
    del kwargs

    if github_event["actor"] == "renovate[bot]":
        return True

    if not os.path.exists(".github/changelog-config.yaml"):
        return True

    required_labels = []
    with open(".github/changelog-config.yaml", encoding="utf-8") as changelog_config_file:
        changelog_config = yaml.load(changelog_config_file, Loader=yaml.SafeLoader)
        for section in changelog_config.values():
            if "labels" in section:
                required_labels.extend(section["labels"])

    print(f"Requird one onf the following labels: {', '.join(required_labels)}")

    if required_labels:
        labels = [
            label["name"]
            for label in github_event["event"]["pull_request"]["labels"]
            if label["name"] in required_labels
        ]
        if len(labels) == 0:
            print(f"No required label found: {', '.join(required_labels)}")
            return True
        if len(labels) > 1:
            print(f"Too many required labels found: {', '.join(labels)}")
            return False
    return True


GET_ISSUE_RE = [
    re.compile(r"^([A-Z]{3,6}-[0-9]+)-.*$"),
    re.compile(r"^([a-z]{3,6}-[0-9]+)-.*$"),
    re.compile(r"^.*-([A-Z]{3,6}-[0-9]+)$"),
    re.compile(r"^.*-([a-z]{3,6}-[0-9]+)$"),
]


def _get_issue_number(name: str) -> Optional[str]:
    for re_ in GET_ISSUE_RE:
        match = re_.match(name)
        if match is not None:
            return match.group(1)
    return None


def add_issue_link(github_event: Dict[str, Any], **kwargs: Any) -> bool:
    """Add a comment with the link to Jira if needed."""
    del kwargs

    issue_number = _get_issue_number(github_event["event"]["pull_request"]["head"]["ref"])

    if issue_number is None:
        return True

    issue_number = issue_number.upper()

    if issue_number in github_event["event"]["pull_request"].get("body", "").upper():
        return True

    comments_response = requests.get(
        github_event["event"]["pull_request"]["_links"]["comments"]["href"],
        timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
        headers=c2cciutils.add_authorization_header({}),
    )
    comments_response.raise_for_status()
    comments = comments_response.json()

    for comment in comments:
        if issue_number in comment.get("body", "").upper():
            return True

    response = requests.post(
        github_event["event"]["pull_request"]["_links"]["comments"]["href"],
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {github_event['token']}",
        },
        json={"body": f"See also: [{issue_number}](https://jira.camptocamp.com/browse/{issue_number})"},
        timeout=int(os.environ.get("C2CCIUTILS_TIMEOUT", "30")),
    )

    if not response.ok:
        print(f"Unable to add the comment: {response.text}")
    return response.ok
