"""
Automatically generated file from a JSON schema.
"""

from typing import Any, Dict, List, Literal, TypedDict, Union

# Audit
#
# The audit configuration
Audit = TypedDict(
    "Audit",
    {
        "npm": "AuditNpm",
        "outdated_versions": "AuditOutdatedVersions",
        "pip": "AuditPip",
        "pipenv": "AuditPipenv",
        "pipfile": "AuditPipfile",
        "pipfile_lock": "AuditPipfileLock",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "print_versions": "PrintVersions",
    },
    total=False,
)


# audit npm
#
# The npm audit configuration
#
# oneOf
AuditNpm = Union["AuditNpmConfig", bool]


# audit npm config
#
# The npm audit configuration
AuditNpmConfig = TypedDict(
    "AuditNpmConfig",
    {
        # The list of CWE id to be ignored
        #
        # default:
        #   []
        "cwe_ignore": List[str],
        # The list of package names to be ignored
        #
        # default:
        #   []
        "package_ignore": List[str],
    },
    total=False,
)


# Audit outdated versions
#
# Audit of outdated version
AuditOutdatedVersions = bool


# Audit pip
#
# Audit the requirements.txt files
AuditPip = bool


# Audit pipenv
#
# The audit Pipfile and Pipfile.lock configuration (old version)
#
# oneOf
AuditPipenv = Union["AuditPipenvConfig", Literal[False]]


# Audit pipenv config
#
# The audit Pipfile and Pipfile.lock configuration (old version)
AuditPipenvConfig = TypedDict(
    "AuditPipenvConfig",
    {
        "python_versions": List[str],
    },
    total=False,
)


# Audit pipfile
#
# The audit Pipfile configuration
#
# oneOf
AuditPipfile = Union["AuditPipfileConfig", bool]


# Audit pipfile config
#
# The audit Pipfile configuration
AuditPipfileConfig = TypedDict(
    "AuditPipfileConfig",
    {
        # Pipfile sections
        #
        # The section to be audited
        #
        # default:
        #   - default
        #   - develop
        "sections": List[str],
    },
    total=False,
)


# Audit pipfile lock
#
# The audit Pipfile.lock configuration
#
# oneOf
AuditPipfileLock = Union["AuditPipfileLockConfig", bool]


# Audit pipfile lock config
#
# The audit Pipfile.lock configuration
AuditPipfileLockConfig = TypedDict(
    "AuditPipfileLockConfig",
    {
        # Pipfile.lock sections
        #
        # The section to be audited
        #
        # default:
        #   - default
        "sections": List[str],
    },
    total=False,
)


# Default value of the field path 'Checks black configuration config properties'
BLACK_CONFIGURATION_PROPERTIES_DEFAULT = {"line-length": 110}


# Default value of the field path 'Checks codespell config  arguments'
CODESPELL_ARGUMENTS_DEFAULT = ["--quiet-level=2", "--check-filenames", "--ignore-words-list=ro"]


# Default value of the field path 'Checks codespell config  internal_dictionaries'
CODESPELL_DICTIONARIES_DEFAULT = ["clear", "rare", "informal", "code", "names", "en-GB_to_en-US"]


# Default value of the field path 'Checks codespell config  ignore_re'
CODESPELL_IGNORE_REGULAR_EXPRESSION_DEFAULT = ["(.*/)?poetry\\.lock", "(.*/)?package-lock\\.json"]


# Checks
#
# The checkers configurations
Checks = TypedDict(
    "Checks",
    {
        "black": "ChecksBlack",
        "black_config": "ChecksBlackConfiguration",
        "prospector_config": "ChecksProspectorConfiguration",
        "codespell": "ChecksCodespell",
        "editorconfig": "ChecksEditorconfig",
        "eof": "ChecksEof",
        "gitattribute": "ChecksGitattribute",
        "isort": "ChecksIsort",
        "print_config": "ChecksPrintConfig",
        "required_workflows": "ChecksRequiredWorkflows",
        "versions": "ChecksVersions",
        "workflows": "ChecksWorkflows",
        "prettier": "ChecksPrettier",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "print_versions": "PrintVersions",
    },
    total=False,
)


# Checks Black
#
# The Black check configuration
#
# oneOf
ChecksBlack = Union["ChecksBlackConfig", bool]


# Checks black config
#
# The Black check configuration
ChecksBlackConfig = TypedDict(
    "ChecksBlackConfig",
    {
        "properties": Dict[str, Any],
        # List of regular expression that should be ignored
        #
        # default:
        #   []
        "ignore_patterns_re": List[str],
    },
    total=False,
)


# Checks Black configuration
#
# The Black configuration check configuration
#
# oneOf
ChecksBlackConfiguration = Union["ChecksBlackConfigurationConfig", bool]


# Checks black configuration config
#
# The Black configuration check configuration
ChecksBlackConfigurationConfig = TypedDict(
    "ChecksBlackConfigurationConfig",
    {
        # Black configuration properties
        #
        # The properties key = value that should be present
        #
        # default:
        #   line-length: 110
        "properties": Dict[str, Union[Union[int, float], str]],
    },
    total=False,
)


# Checks codespell
#
# The codespell check configuration
#
# oneOf
ChecksCodespell = Union["ChecksCodespellConfig", bool]


# Checks codespell config
#
# The codespell check configuration
ChecksCodespellConfig = TypedDict(
    "ChecksCodespellConfig",
    {
        # codespell dictionaries
        #
        # List of argument that will be added to the codespell command
        #
        # default:
        #   - clear
        #   - rare
        #   - informal
        #   - code
        #   - names
        #   - en-GB_to_en-US
        "internal_dictionaries": List[str],
        # codespell arguments
        #
        # List of argument that will be added to the codespell command
        #
        # default:
        #   - --quiet-level=2
        #   - --check-filenames
        #   - --ignore-words-list=ro
        "arguments": List[str],
        # codespell ignore regular expression
        #
        # List of regular expression that should be ignored
        #
        # default:
        #   - (.*/)?poetry\.lock
        #   - (.*/)?package-lock\.json
        "ignore_re": List[str],
    },
    total=False,
)


# Checks editorconfig
#
# The editorconfig configuration check configuration
#
# oneOf
ChecksEditorconfig = Union["ChecksEditorconfigConfig", Literal[False]]


# Checks editorconfig config
#
# The editorconfig configuration check configuration
ChecksEditorconfigConfig = TypedDict(
    "ChecksEditorconfigConfig",
    {
        # The key = value that should be present in the configuration
        "properties": Dict[str, Dict[str, str]],
    },
    total=False,
)


# checks eof
#
# Check the end-of-file
ChecksEof = bool


# checks gitattribute
#
# Run the Git attributes check
ChecksGitattribute = bool


# checks isort
#
# The isort check configuration
#
# oneOf
ChecksIsort = Union["ChecksIsortConfig", bool]


# checks isort config
#
# The isort check configuration
ChecksIsortConfig = TypedDict(
    "ChecksIsortConfig",
    {
        # List of regular expression that should be ignored
        #
        # default:
        #   []
        "ignore_patterns_re": List[str],
    },
    total=False,
)


# Checks Prettier
#
# The Prettier check configuration
#
# oneOf
ChecksPrettier = Union["ChecksPrettierConfig", bool]


# Checks Prettier config
#
# The Prettier check configuration
ChecksPrettierConfig = TypedDict(
    "ChecksPrettierConfig",
    {
        "properties": Dict[str, Any],
    },
    total=False,
)


# Checks print config
#
# The print the configuration including the auto-generated parts
ChecksPrintConfig = bool


# Checks Prospector configuration
#
# The Prospector configuration check configuration
#
# oneOf
ChecksProspectorConfiguration = Union["ChecksProspectorConfigurationConfig", bool]


# Checks prospector configuration config
#
# The Prospector configuration check configuration
ChecksProspectorConfigurationConfig = TypedDict(
    "ChecksProspectorConfigurationConfig",
    {
        # Prospector configuration properties
        #
        # The properties key = value that should be present
        #
        # default:
        #   bandit:
        #     run: true
        #   doc-warnings: true
        #   max-line-length: 110
        #   mypy:
        #     run: true
        #   strictness: veryhigh
        "properties": Dict[str, Any],
    },
    total=False,
)


# checks required workflows
#
# The required workflow check configuration
#
# oneOf
ChecksRequiredWorkflows = Union["ChecksRequiredWorkflowsConfig", Literal[False]]


# checks required workflows config
#
# The required workflow check configuration
ChecksRequiredWorkflowsConfig = Dict[str, "_ChecksRequiredWorkflowsConfigAdditionalproperties"]


# checks versions
#
# The version check configuration
#
# oneOf
ChecksVersions = Union["ChecksVersionsConfig", Literal[False]]


# checks versions config
#
# The version check configuration
ChecksVersionsConfig = TypedDict(
    "ChecksVersionsConfig",
    {
        # Check the versions in the audit workflow
        "audit": bool,
        # Check the versions of the backport labels
        "backport_labels": bool,
        # Check the versions of the protected branches
        "branches": bool,
        # Versions that are not in the `SECURITY.md` but should still be considered
        "extra_versions": List[str],
    },
    total=False,
)


# checks workflows
#
# The workflows checks configuration
#
# oneOf
ChecksWorkflows = Union["ChecksWorkflowsConfig", Literal[False]]


# checks workflows config
#
# The workflows checks configuration
ChecksWorkflowsConfig = TypedDict(
    "ChecksWorkflowsConfig",
    {
        # The images that shouldn't be used
        "images_blacklist": List[str],
        # A timeout should be present
        "timeout": bool,
    },
    total=False,
)


# configuration
#
# C2C CI utils configuration file
Configuration = TypedDict(
    "Configuration",
    {
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "audit": "Audit",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "checks": "Checks",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "pr-checks": "PullRequestChecks",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "publish": "Publish",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "version": "Version",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "k8s": "K8SConfiguration",
    },
    total=False,
)


# Default value of the field path 'K8s configuration db'
DB_CONFIGURATION_DEFAULT: Dict[str, Any] = {}


# Default value of the field path 'dispatch config event-type'
DOCKER_DISPATCH_EVENT_TYPE_DEFAULT = "image-update"


# Default value of the field path 'dispatch config repository'
DOCKER_DISPATCH_REPOSITORY_DEFAULT = "camptocamp/argocd-gs-gmf-apps"


# Default value of the field path 'Publish Docker config repository'
DOCKER_REPOSITORY_DEFAULT = {
    "github": {"server": "ghcr.io", "versions": ["version_tag", "version_branch", "rebuild"]},
    "dockerhub": {},
}


# DB configuration
#
# Database configuration
#
# default:
#   {}
DbConfiguration = TypedDict(
    "DbConfiguration",
    {
        # K8S DB chart options
        #
        # default:
        #   auth.postgresPassword: mySuperTestingPassword
        #   persistence.enabled: 'false'
        #   tls.autoGenerated: 'true'
        #   tls.enabled: 'true'
        #   volumePermissions.enabled: 'true'
        "chart-options": Dict[str, str],
    },
    total=False,
)


# dispatch config
#
# Send a dispatch event to an other repository
DispatchConfig = TypedDict(
    "DispatchConfig",
    {
        # Docker dispatch repository
        #
        # The repository name to be triggered
        #
        # default: camptocamp/argocd-gs-gmf-apps
        "repository": str,
        # Docker dispatch event type
        #
        # The event type to be triggered
        #
        # default: image-update
        "event-type": str,
    },
    total=False,
)


# K3d configuration
#
# default:
#   {}
K3DConfiguration = TypedDict(
    "K3DConfiguration",
    {
        # K3D install commands
        #
        # default:
        #   - - k3d
        #     - cluster
        #     - create
        #     - test-cluster
        #     - --no-lb
        #     - --no-rollback
        "install-commands": List[List[str]],
    },
    total=False,
)


# Default value of the field path 'K8s configuration k3d'
K3D_CONFIGURATION_DEFAULT: Dict[str, Any] = {}


# Default value of the field path 'K3d configuration install-commands'
K3D_INSTALL_COMMANDS_DEFAULT = [["k3d", "cluster", "create", "test-cluster", "--no-lb", "--no-rollback"]]


# K8s configuration
#
# default:
#   {}
K8SConfiguration = TypedDict(
    "K8SConfiguration",
    {
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "k3d": "K3DConfiguration",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "db": "DbConfiguration",
    },
    total=False,
)


# Default value of the field path 'configuration k8s'
K8S_CONFIGURATION_DEFAULT: Dict[str, Any] = {}


# Default value of the field path 'DB configuration chart-options'
K8S_DB_CHART_OPTIONS_DEFAULT = {
    "persistence.enabled": "false",
    "tls.enabled": "true",
    "tls.autoGenerated": "true",
    "auth.postgresPassword": "mySuperTestingPassword",
    "volumePermissions.enabled": "true",
}


# Default value of the field path 'Audit pipfile lock config sections'
PIPFILE_FULL_STOP_LOCK_SECTIONS_DEFAULT = ["default"]


# Default value of the field path 'Audit pipfile config sections'
PIPFILE_SECTIONS_DEFAULT = ["default", "develop"]


# Default value of the field path 'Checks prospector configuration config properties'
PROSPECTOR_CONFIGURATION_PROPERTIES_DEFAULT = {
    "strictness": "veryhigh",
    "max-line-length": 110,
    "doc-warnings": True,
    "mypy": {"run": True},
    "bandit": {"run": True},
}


# Default value of the field path 'Publish Docker image group'
PUBLISH_DOCKER_IMAGE_GROUP_DEFAULT = "default"


# Default value of the field path 'Publish Docker image tags'
PUBLISH_DOCKER_IMAGE_TAGS_DEFAULT = ["{version}"]


# Default value of the field path 'Publish Docker config latest'
PUBLISH_DOCKER_LATEST_DEFAULT = True


# Default value of the field path 'Publish Docker repository versions'
PUBLISH_DOCKER_REPOSITORY_VERSIONS_DEFAULT = ["version_tag", "version_branch", "rebuild", "feature_branch"]


# Default value of the field path 'Publish google_calendar'
PUBLISH_GOOGLE_CALENDAR_DEFAULT: Dict[str, Any] = {}


# Default value of the field path 'Publish Google calendar config on'
PUBLISH_GOOGLE_CALENDAR_ON_DEFAULT = ["version_branch", "version_tag", "rebuild"]


# Default value of the field path 'publish pypi package group'
PUBLISH_PIP_PACKAGE_GROUP_DEFAULT = "default"


# Default value of the field path 'Publish pypi'
PUBLISH_PYPI_DEFAULT: Dict[str, Any] = {}


# Default value of the field path 'pull request checks commits messages configuration check_first_capital'
PULL_REQUEST_CHECKS_COMMITS_MESSAGES_FIRST_CAPITAL_DEFAULT = True


# Default value of the field path 'pull request checks commits messages configuration check_fixup'
PULL_REQUEST_CHECKS_COMMITS_MESSAGES_FIXUP_DEFAULT = True


# Default value of the field path 'pull request checks commits messages configuration min_head_length'
PULL_REQUEST_CHECKS_COMMITS_MESSAGES_MIN_HEAD_LENGTH_DEFAULT = 5


# Default value of the field path 'pull request checks commits messages configuration check_no_merge_commits'
PULL_REQUEST_CHECKS_COMMITS_MESSAGES_NO_MERGE_COMMITS_DEFAULT = True


# Default value of the field path 'pull request checks commits messages configuration check_no_own_revert'
PULL_REQUEST_CHECKS_COMMITS_MESSAGES_NO_OWN_REVERT_DEFAULT = True


# Default value of the field path 'pull request checks commits spelling configuration only_head'
PULL_REQUEST_CHECKS_COMMITS_MESSAGES_ONLY_HEAD_DEFAULT = False


# Default value of the field path 'pull request checks commits messages configuration check_squash'
PULL_REQUEST_CHECKS_COMMITS_MESSAGES_SQUASH_DEFAULT = True


# Default value of the field path 'pull request checks pull request spelling configuration only_head'
PULL_REQUEST_CHECKS_ONLY_HEAD_DEFAULT = False


# Print versions
#
# The print versions configuration
PrintVersions = TypedDict(
    "PrintVersions",
    {
        "versions": List["_PrintVersionsVersionsItem"],
    },
    total=False,
)


# Publish
#
# The publishing configurations
Publish = TypedDict(
    "Publish",
    {
        "docker": "PublishDocker",
        "pypi": "PublishPypi",
        "helm": "PublishHelm",
        "google_calendar": "PublishGoogleCalendar",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "print_versions": "PrintVersions",
    },
    total=False,
)


# Publish Docker
#
# The configuration used to publish on Docker
#
# oneOf
PublishDocker = Union["PublishDockerConfig", Literal[False]]


# Publish Docker config
#
# The configuration used to publish on Docker
PublishDockerConfig = TypedDict(
    "PublishDockerConfig",
    {
        # Publish Docker latest
        #
        # Publish the latest version on tag latest
        #
        # default: True
        "latest": bool,
        # List of images to be published
        "images": List["PublishDockerImage"],
        # Docker repository
        #
        # The repository where we should publish the images
        #
        # default:
        #   dockerhub: {}
        #   github:
        #     server: ghcr.io
        #     versions:
        #     - version_tag
        #     - version_branch
        #     - rebuild
        "repository": Dict[str, "PublishDockerRepository"],
        # Send a dispatch event to an other repository
        #
        # default:
        #   {}
        #
        # oneOf
        "dispatch": Union["DispatchConfig", Literal[False]],
    },
    total=False,
)


# Publish Docker image
PublishDockerImage = TypedDict(
    "PublishDockerImage",
    {
        # Publish Docker image group
        #
        # The image is in the group, should be used with the --group option of c2cciutils-publish script
        #
        # default: default
        "group": str,
        # The image name
        "name": str,
        # publish docker image tags
        #
        # The tag name, will be formatted with the version=<the version>, the image with version=latest should be present when we call the c2cciutils-publish script
        #
        # default:
        #   - '{version}'
        "tags": List[str],
    },
    total=False,
)


# Publish Docker repository
PublishDockerRepository = TypedDict(
    "PublishDockerRepository",
    {
        # The server URL
        "server": str,
        # Publish Docker repository versions
        #
        # The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script
        #
        # default:
        #   - version_tag
        #   - version_branch
        #   - rebuild
        #   - feature_branch
        "versions": List[str],
    },
    total=False,
)


# Publish Google calendar
#
# The configuration to publish on Google Calendar
#
# default:
#   {}
#
# oneOf
PublishGoogleCalendar = Union["PublishGoogleCalendarConfig", Literal[False]]


# Publish Google calendar config
#
# The configuration to publish on Google Calendar
PublishGoogleCalendarConfig = TypedDict(
    "PublishGoogleCalendarConfig",
    {
        # Publish Google calendar on
        #
        # default:
        #   - version_branch
        #   - version_tag
        #   - rebuild
        "on": List[str],
    },
    total=False,
)


# publish helm
#
# Configuration to publish Helm charts on GitHub release
#
# oneOf
PublishHelm = Union["PublishHelmConfig", Literal[False]]


# publish helm config
#
# Configuration to publish on Helm charts on GitHub release
PublishHelmConfig = TypedDict(
    "PublishHelmConfig",
    {
        # The folders that will be published
        "folders": List[str],
        # The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script
        "versions": List[str],
    },
    total=False,
)


# publish pypi
#
# Configuration to publish on pypi
#
# default:
#   {}
#
# oneOf
PublishPypi = Union["PublishPypiConfig", Literal[False]]


# publish pypi config
#
# Configuration to publish on pypi
PublishPypiConfig = TypedDict(
    "PublishPypiConfig",
    {
        # The configuration of packages that will be published
        "packages": List["PublishPypiPackage"],
        # The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script
        "versions": List[str],
    },
    total=False,
)


# publish pypi package
#
# The configuration of package that will be published
PublishPypiPackage = TypedDict(
    "PublishPypiPackage",
    {
        # Publish pip package group
        #
        # The image is in the group, should be used with the --group option of c2cciutils-publish script
        #
        # default: default
        "group": str,
        # The path of the pypi package
        "path": str,
        # The command used to do the build
        "build_command": List[str],
    },
    total=False,
)


# Pull request checks
#
# The PR check configuration
PullRequestChecks = TypedDict(
    "PullRequestChecks",
    {
        "print_event": "PullRequestChecksPrintEvent",
        "commits_messages": "PullRequestChecksCommitsMessages",
        "commits_spell": "PullRequestChecksCommitsSpelling",
        "pull_request_spell": "PullRequestChecksPullRequestSpelling",
        "pull_request_labels": "PullRequestChecksRequestLabels",
        "add_issue_link": "PullRequestChecksAddIssueLink",
    },
    total=False,
)


# pull request checks add issue link
PullRequestChecksAddIssueLink = bool


# pull request checks commits messages
#
# Check the pull request commits messages
#
# oneOf
PullRequestChecksCommitsMessages = Union["PullRequestChecksCommitsMessagesConfiguration", bool]


# pull request checks commits messages configuration
#
# The commit message check configuration
PullRequestChecksCommitsMessagesConfiguration = TypedDict(
    "PullRequestChecksCommitsMessagesConfiguration",
    {
        # pull request checks commits messages fixup
        #
        # Check that we don't have one fixup commit in the pull request
        #
        # default: True
        "check_fixup": bool,
        # pull request checks commits messages squash
        #
        # Check that we don't have one squash commit in the pull request
        #
        # default: True
        "check_squash": bool,
        # pull request checks commits messages first capital
        #
        # Check that the all the commits message starts with a capital letter
        #
        # default: True
        "check_first_capital": bool,
        # pull request checks commits messages min head length
        #
        # Check that the commits message head is at least this long, use 0 to disable
        #
        # default: 5
        "min_head_length": int,
        # pull request checks commits messages no merge commits
        #
        # Check that we don't have merge commits in the pull request
        #
        # default: True
        "check_no_merge_commits": bool,
        # pull request checks commits messages no own revert
        #
        # Check that we don't have reverted one of our commits in the pull request
        #
        # default: True
        "check_no_own_revert": bool,
    },
    total=False,
)


# pull request checks commits spelling
#
# oneOf
PullRequestChecksCommitsSpelling = Union["PullRequestChecksCommitsSpellingConfiguration", bool]


# pull request checks commits spelling configuration
#
# Configuration used to check the spelling of the commits
PullRequestChecksCommitsSpellingConfiguration = TypedDict(
    "PullRequestChecksCommitsSpellingConfiguration",
    {
        # pull request checks commits messages only head
        #
        # default: False
        "only_head": bool,
    },
    total=False,
)


# pull request checks print event
#
# Print the GitHub event object
PullRequestChecksPrintEvent = bool


# pull request checks pull request spelling
#
# oneOf
PullRequestChecksPullRequestSpelling = Union["PullRequestChecksPullRequestSpellingConfiguration", bool]


# pull request checks pull request spelling configuration
#
# Configuration used to check the spelling of the title and body of the pull request
PullRequestChecksPullRequestSpellingConfiguration = TypedDict(
    "PullRequestChecksPullRequestSpellingConfiguration",
    {
        # pull request checks only head
        #
        # default: False
        "only_head": bool,
    },
    total=False,
)


# pull request checks request labels
#
# According the create changelog configuration
PullRequestChecksRequestLabels = bool


# Version
#
# The version configurations
Version = TypedDict(
    "Version",
    {
        "branch_to_version_re": "VersionTransform",
        "tag_to_version_re": "VersionTransform",
    },
    total=False,
)


# Version transform
#
# A version transformer definition
VersionTransform = List["_VersionTransformItem"]


# Default value of the field path 'audit npm config cwe_ignore'
_AUDIT_NPM_CONFIG_CWE_IGNORE_DEFAULT: List[Any] = []


# Default value of the field path 'audit npm config package_ignore'
_AUDIT_NPM_CONFIG_PACKAGE_IGNORE_DEFAULT: List[Any] = []


# Default value of the field path 'Checks black config ignore_patterns_re'
_CHECKS_BLACK_CONFIG_IGNORE_PATTERNS_RE_DEFAULT: List[Any] = []


# Default value of the field path 'checks isort config ignore_patterns_re'
_CHECKS_ISORT_CONFIG_IGNORE_PATTERNS_RE_DEFAULT: List[Any] = []


# oneOf
_ChecksRequiredWorkflowsConfigAdditionalproperties = Union[
    "_ChecksRequiredWorkflowsConfigAdditionalpropertiesOneof0", bool
]


_ChecksRequiredWorkflowsConfigAdditionalpropertiesOneof0 = TypedDict(
    "_ChecksRequiredWorkflowsConfigAdditionalpropertiesOneof0",
    {
        # The required steps configuration
        "steps": List["_ChecksRequiredWorkflowsConfigAdditionalpropertiesOneof0StepsItem"],
        # Should we have a fail fast configuration
        "strategy-fail-fast": bool,
        # The if that we should have
        "if": str,
        # We shouldn't have any if
        "noif": bool,
        # The on configuration that we should have
        "on": Dict[str, Any],
    },
    total=False,
)


_ChecksRequiredWorkflowsConfigAdditionalpropertiesOneof0StepsItem = TypedDict(
    "_ChecksRequiredWorkflowsConfigAdditionalpropertiesOneof0StepsItem",
    {
        # The required environment variable
        "env": List[str],
        # The required regular expression of the run part
        "run_re": str,
    },
    total=False,
)


# Default value of the field path 'Publish Docker config dispatch'
_PUBLISH_DOCKER_CONFIG_DISPATCH_DEFAULT: Dict[str, Any] = {}


_PrintVersionsVersionsItem = TypedDict(
    "_PrintVersionsVersionsItem",
    {
        # The command that should be used
        "cmd": List[str],
        # The name
        "name": str,
        # Prefix added when we print the version
        "prefix": str,
    },
    total=False,
)


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
