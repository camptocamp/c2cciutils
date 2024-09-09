"""
Automatically generated file from a JSON schema.
"""


from typing import Any, Literal, TypedDict, Union

AUDIT_DEFAULT = {"snyk": True, "outdated_versions": True}
""" Default value of the field path 'configuration audit' """


AUDIT_SNYK_FILES_NO_INSTALL_DEFAULT: list[Any] = []
""" Default value of the field path 'Audit snyk config files_no_install' """


AUDIT_SNYK_FIX_ARGUMENTS_DEFAULT = ["--all-projects"]
""" Default value of the field path 'Audit snyk config fix_arguments' """


AUDIT_SNYK_FIX_PULL_REQUEST_ARGUMENTS_DEFAULT = ["--fill", "--label=dependencies"]
""" Default value of the field path 'Audit snyk config fix_github_create_pull_request_arguments' """


AUDIT_SNYK_MONITOR_ARGUMENTS_DEFAULT = ["--all-projects"]
""" Default value of the field path 'Audit snyk config monitor_arguments' """


AUDIT_SNYK_PIPENV_SYNC_ARGUMENTS_DEFAULT: list[Any] = []
""" Default value of the field path 'Audit snyk config pipenv_sync_arguments' """


AUDIT_SNYK_PIP_INSTALL_ARGUMENTS_DEFAULT = ["--user"]
""" Default value of the field path 'Audit snyk config pip_install_arguments' """


AUDIT_SNYK_TEST_ARGUMENTS_DEFAULT = ["--all-projects", "--fail-on=all", "--severity-threshold=medium"]
""" Default value of the field path 'Audit snyk config test_arguments' """


class Audit(TypedDict, total=False):
    """
    Audit.

    The audit configuration

    default:
      outdated_versions: true
      snyk: true
    """

    outdated_versions: "AuditOutdatedVersions"
    snyk: "AuditWithSnyk"


AuditOutdatedVersions = bool
"""
Audit outdated versions.

Audit of outdated version
"""


class AuditSnykConfig(TypedDict, total=False):
    """
    Audit snyk config.

    The audit Pipfile configuration
    """

    test_arguments: list[str]
    """
    audit snyk test arguments.

    The snyk test arguments

    default:
      - --all-projects
      - --fail-on=all
      - --severity-threshold=medium
    """

    monitor_arguments: list[str]
    """
    audit snyk monitor arguments.

    The snyk monitor arguments

    default:
      - --all-projects
    """

    fix_arguments: list[str]
    """
    audit snyk fix arguments.

    The snyk fix arguments

    default:
      - --all-projects
    """

    fix_github_create_pull_request_arguments: list[str]
    """
    audit snyk fix pull request arguments.

    The snyk fix pull request extra arguments

    default:
      - --fill
      - --label=dependencies
    """

    pip_install_arguments: list[str]
    """
    audit snyk pip install arguments.

    The snyk pip install arguments

    default:
      - --user
    """

    pipenv_sync_arguments: list[str]
    """
    audit snyk pipenv sync arguments.

    The snyk pipenv sync arguments

    default:
      []
    """

    files_no_install: list[str]
    """
    audit snyk files no install.

    The list of files to not install

    default:
      []
    """


AuditWithSnyk = Union["AuditSnykConfig", bool]
"""
Audit with snyk.

The audit snyk configuration

oneOf
"""


CODESPELL_ARGUMENTS_DEFAULT = ["--quiet-level=2", "--check-filenames", "--ignore-words-list=ro"]
""" Default value of the field path 'Codespell arguments' """


CODESPELL_DICTIONARIES_DEFAULT = ["clear", "rare", "informal", "code", "names", "en-GB_to_en-US"]
""" Default value of the field path 'Codespell internal_dictionaries' """


CODESPELL_IGNORE_REGULAR_EXPRESSION_DEFAULT = ["(.*/)?poetry\\.lock", "(.*/)?package-lock\\.json"]
""" Default value of the field path 'Codespell ignore_re' """


class Codespell(TypedDict, total=False):
    """
    Codespell.

    The codespell check configuration
    """

    internal_dictionaries: list[str]
    """
    codespell dictionaries.

    List of argument that will be added to the codespell command

    default:
      - clear
      - rare
      - informal
      - code
      - names
      - en-GB_to_en-US
    """

    arguments: list[str]
    """
    codespell arguments.

    List of argument that will be added to the codespell command

    default:
      - --quiet-level=2
      - --check-filenames
      - --ignore-words-list=ro
    """

    ignore_re: list[str]
    r"""
    codespell ignore regular expression.

    List of regular expression that should be ignored

    default:
      - (.*/)?poetry\.lock
      - (.*/)?package-lock\.json
    """


# configuration.
#
# C2C CI utils configuration file
Configuration = TypedDict(
    "Configuration",
    {
        "print_versions": "PrintVersions",
        "codespell": "Codespell",
        "audit": "Audit",
        "pr-checks": "PullRequestChecks",
        "publish": "Publish",
        "version": "Version",
        "k8s": "K8SConfiguration",
        "dpkg": "Dpkg",
    },
    total=False,
)


DB_CONFIGURATION_DEFAULT: dict[str, Any] = {}
""" Default value of the field path 'K8s configuration db' """


DOCKER_DISPATCH_EVENT_TYPE_DEFAULT = "image-update"
""" Default value of the field path 'dispatch config event-type' """


DOCKER_DISPATCH_REPOSITORY_DEFAULT = "camptocamp/argocd-gs-gmf-apps"
""" Default value of the field path 'dispatch config repository' """


DOCKER_REPOSITORY_DEFAULT = {
    "github": {"server": "ghcr.io", "versions": ["version_tag", "version_branch", "rebuild"]},
    "dockerhub": {},
}
""" Default value of the field path 'Publish Docker config repository' """


# DB configuration.
#
# Database configuration
#
# default:
#   {}
DbConfiguration = TypedDict(
    "DbConfiguration",
    {
        # K8S DB chart options.
        #
        # default:
        #   auth.postgresPassword: mySuperTestingPassword
        #   persistence.enabled: 'false'
        #   tls.autoGenerated: 'true'
        #   tls.enabled: 'true'
        #   volumePermissions.enabled: 'true'
        "chart-options": dict[str, str],
    },
    total=False,
)


# dispatch config.
#
# Send a dispatch event to an other repository
DispatchConfig = TypedDict(
    "DispatchConfig",
    {
        # Docker dispatch repository.
        #
        # The repository name to be triggered
        #
        # default: camptocamp/argocd-gs-gmf-apps
        "repository": str,
        # Docker dispatch event type.
        #
        # The event type to be triggered
        #
        # default: image-update
        "event-type": str,
    },
    total=False,
)


class Dpkg(TypedDict, total=False):
    """
    dpkg.

    The configuration use t manage the dpkg packages
    """

    packages_mapping: dict[str, str]
    """
    dpkg packages mapping.

    The mapping of source package found in the image to package present in repology.org
    """

    ignored_packages: list[str]
    """
    dpkg ignored packages.

    The list of packages that should be ignored
    """


# K3d configuration.
#
# default:
#   {}
K3DConfiguration = TypedDict(
    "K3DConfiguration",
    {
        # K3D install commands.
        #
        # default:
        #   - - k3d
        #     - cluster
        #     - create
        #     - test-cluster
        #     - --no-lb
        #     - --no-rollback
        "install-commands": list[list[str]],
    },
    total=False,
)


K3D_CONFIGURATION_DEFAULT: dict[str, Any] = {}
""" Default value of the field path 'K8s configuration k3d' """


K3D_INSTALL_COMMANDS_DEFAULT = [["k3d", "cluster", "create", "test-cluster", "--no-lb", "--no-rollback"]]
""" Default value of the field path 'K3d configuration install-commands' """


class K8SConfiguration(TypedDict, total=False):
    """
    K8s configuration.

    default:
      {}
    """

    k3d: "K3DConfiguration"
    db: "DbConfiguration"


K8S_CONFIGURATION_DEFAULT: dict[str, Any] = {}
""" Default value of the field path 'configuration k8s' """


K8S_DB_CHART_OPTIONS_DEFAULT = {
    "persistence.enabled": "false",
    "tls.enabled": "true",
    "tls.autoGenerated": "true",
    "auth.postgresPassword": "mySuperTestingPassword",
    "volumePermissions.enabled": "true",
}
""" Default value of the field path 'DB configuration chart-options' """


PRINT_VERSIONS_VERSIONS_DEFAULT = [
    {"name": "c2cciutils", "cmd": ["c2cciutils", "--version"]},
    {"name": "python", "cmd": ["python3", "--version"]},
    {"name": "pip", "cmd": ["python3", "-m", "pip", "--version"]},
    {"name": "twine", "cmd": ["twine", "--version"]},
    {"name": "node", "prefix": "node ", "cmd": ["node", "--version"]},
    {"name": "npm", "prefix": "npm ", "cmd": ["npm", "--version"]},
    {"name": "make", "cmd": ["make", "--version"], "prefix": "make "},
    {"name": "docker", "cmd": ["docker", "--version"]},
    {"name": "docker compose", "cmd": ["docker", "compose", "version"]},
    {"name": "java", "cmd": ["java", "-version"]},
    {"name": "helm", "cmd": ["helm", "version"]},
]
""" Default value of the field path 'Print versions versions' """


PUBLISH_DEFAULT = {
    "pypi": {"versions": ["version_tag"], "packages": "<auto-detected>"},
    "docker": {"images": "<auto-detected>"},
    "helm": {"versions": ["version_tag"], "folders": "<auto-detected>"},
}
""" Default value of the field path 'configuration publish' """


PUBLISH_DOCKER_IMAGE_GROUP_DEFAULT = "default"
""" Default value of the field path 'Publish Docker image group' """


PUBLISH_DOCKER_IMAGE_TAGS_DEFAULT = ["{version}"]
""" Default value of the field path 'Publish Docker image tags' """


PUBLISH_DOCKER_LATEST_DEFAULT = True
""" Default value of the field path 'Publish Docker config latest' """


PUBLISH_DOCKER_REPOSITORY_VERSIONS_DEFAULT = ["version_tag", "version_branch", "rebuild", "feature_branch"]
""" Default value of the field path 'Publish Docker repository versions' """


PUBLISH_DOCKER_SNYK_MONITOR_ARGS_DEFAULT = ["--app-vulns"]
""" Default value of the field path 'Publish Docker config snyk monitor_args' """


PUBLISH_DOCKER_SNYK_TEST_ARGS_DEFAULT = ["--app-vulns", "--severity-threshold=critical"]
""" Default value of the field path 'Publish Docker config snyk test_args' """


PUBLISH_GOOGLE_CALENDAR_DEFAULT: dict[str, Any] = {}
""" Default value of the field path 'publish_google_calendar' """


PUBLISH_GOOGLE_CALENDAR_ON_DEFAULT = ["version_branch", "version_tag", "rebuild"]
""" Default value of the field path 'Publish Google calendar config on' """


PUBLISH_PIP_PACKAGE_GROUP_DEFAULT = "default"
""" Default value of the field path 'publish pypi package group' """


PUBLISH_PYPI_DEFAULT: dict[str, Any] = {}
""" Default value of the field path 'publish_pypi' """


PULL_REQUEST_CHECKS_COMMITS_MESSAGES_FIRST_CAPITAL_DEFAULT = True
""" Default value of the field path 'pull request checks commits messages configuration check_first_capital' """


PULL_REQUEST_CHECKS_COMMITS_MESSAGES_FIXUP_DEFAULT = True
""" Default value of the field path 'pull request checks commits messages configuration check_fixup' """


PULL_REQUEST_CHECKS_COMMITS_MESSAGES_MIN_HEAD_LENGTH_DEFAULT = 5
""" Default value of the field path 'pull request checks commits messages configuration min_head_length' """


PULL_REQUEST_CHECKS_COMMITS_MESSAGES_NO_MERGE_COMMITS_DEFAULT = True
""" Default value of the field path 'pull request checks commits messages configuration check_no_merge_commits' """


PULL_REQUEST_CHECKS_COMMITS_MESSAGES_NO_OWN_REVERT_DEFAULT = True
""" Default value of the field path 'pull request checks commits messages configuration check_no_own_revert' """


PULL_REQUEST_CHECKS_COMMITS_MESSAGES_ONLY_HEAD_DEFAULT = True
""" Default value of the field path 'pull request checks commits spelling configuration only_head' """


PULL_REQUEST_CHECKS_COMMITS_MESSAGES_SQUASH_DEFAULT = True
""" Default value of the field path 'pull request checks commits messages configuration check_squash' """


PULL_REQUEST_CHECKS_DEFAULT = {
    "commits_messages": True,
    "commits_spell": True,
    "pull_request_spell": True,
    "pull_request_labels": True,
    "add_issue_link": True,
}
""" Default value of the field path 'configuration pr-checks' """


PULL_REQUEST_CHECKS_ONLY_HEAD_DEFAULT = True
""" Default value of the field path 'pull request checks pull request spelling configuration only_head' """


class PrintVersions(TypedDict, total=False):
    """
    Print versions.

    The print versions configuration
    """

    versions: list["_PrintVersionsVersionsItem"]
    """
    Print versions versions.

    default:
      - cmd:
        - c2cciutils
        - --version
        name: c2cciutils
      - cmd:
        - python3
        - --version
        name: python
      - cmd:
        - python3
        - -m
        - pip
        - --version
        name: pip
      - cmd:
        - twine
        - --version
        name: twine
      - cmd:
        - node
        - --version
        name: node
        prefix: 'node '
      - cmd:
        - npm
        - --version
        name: npm
        prefix: 'npm '
      - cmd:
        - make
        - --version
        name: make
        prefix: 'make '
      - cmd:
        - docker
        - --version
        name: docker
      - cmd:
        - docker
        - compose
        - version
        name: docker compose
      - cmd:
        - java
        - -version
        name: java
      - cmd:
        - helm
        - version
        name: helm
    """


class Publish(TypedDict, total=False):
    """
    Publish.

    The publishing configurations

    default:
      docker:
        images: <auto-detected>
      helm:
        folders: <auto-detected>
        versions:
        - version_tag
      pypi:
        packages: <auto-detected>
        versions:
        - version_tag
    """

    docker: "PublishDocker"
    pypi: "PublishPypi"
    helm: "PublishHelm"
    google_calendar: "PublishGoogleCalendar"


PublishDocker = Union["PublishDockerConfig", Literal[False]]
"""
Publish Docker.

The configuration used to publish on Docker

oneOf
"""


class PublishDockerConfig(TypedDict, total=False):
    """
    Publish Docker config.

    The configuration used to publish on Docker
    """

    latest: bool
    """
    Publish Docker latest.

    Publish the latest version on tag latest

    default: True
    """

    images: list["PublishDockerImage"]
    """ List of images to be published """

    repository: dict[str, "PublishDockerRepository"]
    """
    Docker repository.

    The repository where we should publish the images

    default:
      dockerhub: {}
      github:
        server: ghcr.io
        versions:
        - version_tag
        - version_branch
        - rebuild
    """

    dispatch: Union["DispatchConfig", Literal[False]]
    """
    Send a dispatch event to an other repository

    default:
      {}

    oneOf
    """

    snyk: "_PublishDockerConfigSnyk"


class PublishDockerImage(TypedDict, total=False):
    """Publish Docker image."""

    group: str
    """
    Publish Docker image group.

    The image is in the group, should be used with the --group option of c2cciutils-publish script

    default: default
    """

    name: str
    """ The image name """

    tags: list[str]
    """
    publish docker image tags.

    The tag name, will be formatted with the version=<the version>, the image with version=latest should be present when we call the c2cciutils-publish script

    default:
      - '{version}'
    """


class PublishDockerRepository(TypedDict, total=False):
    """Publish Docker repository."""

    server: str
    """ The server URL """

    versions: list[str]
    """
    Publish Docker repository versions.

    The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script

    default:
      - version_tag
      - version_branch
      - rebuild
      - feature_branch
    """


PublishGoogleCalendar = Union["PublishGoogleCalendarConfig", Literal[False]]
"""
Publish Google calendar.

The configuration to publish on Google Calendar

default:
  {}

oneOf
"""


class PublishGoogleCalendarConfig(TypedDict, total=False):
    """
    Publish Google calendar config.

    The configuration to publish on Google Calendar
    """

    on: list[str]
    """
    Publish Google calendar on.

    default:
      - version_branch
      - version_tag
      - rebuild
    """


PublishHelm = Union["PublishHelmConfig", Literal[False]]
"""
publish helm.

Configuration to publish Helm charts on GitHub release

oneOf
"""


class PublishHelmConfig(TypedDict, total=False):
    """
    publish helm config.

    Configuration to publish on Helm charts on GitHub release
    """

    folders: list[str]
    """ The folders that will be published """

    versions: list[str]
    """ The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script """


PublishPypi = Union["PublishPypiConfig", Literal[False]]
"""
publish pypi.

Configuration to publish on pypi

default:
  {}

oneOf
"""


class PublishPypiConfig(TypedDict, total=False):
    """
    publish pypi config.

    Configuration to publish on pypi
    """

    packages: list["PublishPypiPackage"]
    """ The configuration of packages that will be published """

    versions: list[str]
    """ The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script """


class PublishPypiPackage(TypedDict, total=False):
    """
    publish pypi package.

    The configuration of package that will be published
    """

    group: str
    """
    Publish pip package group.

    The image is in the group, should be used with the --group option of c2cciutils-publish script

    default: default
    """

    path: str
    """ The path of the pypi package """

    build_command: list[str]
    """ The command used to do the build """


class PullRequestChecks(TypedDict, total=False):
    """
    Pull request checks.

    The PR check configuration

    default:
      add_issue_link: true
      commits_messages: true
      commits_spell: true
      pull_request_labels: true
      pull_request_spell: true
    """

    commits_messages: "PullRequestChecksCommitsMessages"
    commits_spell: "PullRequestChecksCommitsSpelling"
    pull_request_spell: "PullRequestChecksPullRequestSpelling"
    pull_request_labels: "PullRequestChecksRequestLabels"
    add_issue_link: "PullRequestChecksAddIssueLink"


PullRequestChecksAddIssueLink = bool
""" pull request checks add issue link. """


PullRequestChecksCommitsMessages = Union["PullRequestChecksCommitsMessagesConfiguration", bool]
"""
pull request checks commits messages.

Check the pull request commits messages

oneOf
"""


class PullRequestChecksCommitsMessagesConfiguration(TypedDict, total=False):
    """
    pull request checks commits messages configuration.

    The commit message check configuration
    """

    check_fixup: bool
    """
    pull request checks commits messages fixup.

    Check that we don't have one fixup commit in the pull request

    default: True
    """

    check_squash: bool
    """
    pull request checks commits messages squash.

    Check that we don't have one squash commit in the pull request

    default: True
    """

    check_first_capital: bool
    """
    pull request checks commits messages first capital.

    Check that the all the commits message starts with a capital letter

    default: True
    """

    min_head_length: int
    """
    pull request checks commits messages min head length.

    Check that the commits message head is at least this long, use 0 to disable

    default: 5
    """

    check_no_merge_commits: bool
    """
    pull request checks commits messages no merge commits.

    Check that we don't have merge commits in the pull request

    default: True
    """

    check_no_own_revert: bool
    """
    pull request checks commits messages no own revert.

    Check that we don't have reverted one of our commits in the pull request

    default: True
    """


PullRequestChecksCommitsSpelling = Union["PullRequestChecksCommitsSpellingConfiguration", bool]
"""
pull request checks commits spelling.

oneOf
"""


class PullRequestChecksCommitsSpellingConfiguration(TypedDict, total=False):
    """
    pull request checks commits spelling configuration.

    Configuration used to check the spelling of the commits
    """

    only_head: bool
    """
    pull request checks commits messages only head.

    default: True
    """


PullRequestChecksPullRequestSpelling = Union["PullRequestChecksPullRequestSpellingConfiguration", bool]
"""
pull request checks pull request spelling.

oneOf
"""


class PullRequestChecksPullRequestSpellingConfiguration(TypedDict, total=False):
    """
    pull request checks pull request spelling configuration.

    Configuration used to check the spelling of the title and body of the pull request
    """

    only_head: bool
    """
    pull request checks only head.

    default: True
    """


PullRequestChecksRequestLabels = bool
"""
pull request checks request labels.

According the create changelog configuration
"""


class Version(TypedDict, total=False):
    """
    Version.

    The version configurations
    """

    branch_to_version_re: "VersionTransform"
    tag_to_version_re: "VersionTransform"


VersionTransform = list["_VersionTransformItem"]
"""
Version transform.

A version transformer definition
"""


_PUBLISH_DOCKER_CONFIG_DISPATCH_DEFAULT: dict[str, Any] = {}
""" Default value of the field path 'Publish Docker config dispatch' """


class _PrintVersionsVersionsItem(TypedDict, total=False):
    cmd: list[str]
    """ The command that should be used """

    name: str
    """ The name """

    prefix: str
    """ Prefix added when we print the version """


class _PublishDockerConfigSnyk(TypedDict, total=False):
    """Checks the published images with Snyk"""

    monitor_args: Union[list[str], Literal[False]]
    """
    Publish docker snyk monitor args.

    The arguments to pass to the Snyk container monitor command

    default:
      - --app-vulns

    oneOf
    """

    test_args: Union[list[str], Literal[False]]
    """
    Publish docker snyk test args.

    The arguments to pass to the Snyk container test command

    default:
      - --app-vulns
      - --severity-threshold=critical

    oneOf
    """


_VersionTransformItem = TypedDict(
    "_VersionTransformItem",
    {
        # The from regular expression
        "from": str,
        # The expand regular expression: https://docs.python.org/3/library/re.html#re.Match.expand
        "to": str,
    },
    total=False,
)
