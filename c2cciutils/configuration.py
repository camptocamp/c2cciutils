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
AuditNpm = Union["AuditNpmConfig", Literal[False]]


# audit npm config
#
# The npm audit configuration
AuditNpmConfig = TypedDict(
    "AuditNpmConfig",
    {
        # The list of CWE id to be ignored
        "cwe_ignore": List[str],
        # The list of package names to be ignored
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
AuditPipfile = Union["AuditPipfileConfig", Literal[False]]


# Audit pipfile config
#
# The audit Pipfile configuration
AuditPipfileConfig = TypedDict(
    "AuditPipfileConfig",
    {
        # The section to be audited
        "sections": List[str],
    },
    total=False,
)


# Audit pipfile lock
#
# The audit Pipfile.lock configuration
#
# oneOf
AuditPipfileLock = Union["AuditPipfileLockConfig", Literal[False]]


# Audit pipfile lock config
#
# The audit Pipfile.lock configuration
AuditPipfileLockConfig = TypedDict(
    "AuditPipfileLockConfig",
    {
        # The section to be audited
        "sections": List[str],
    },
    total=False,
)


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
ChecksBlack = Union["ChecksBlackConfig", Literal[False]]


# Checks black config
#
# The Black check configuration
ChecksBlackConfig = TypedDict(
    "ChecksBlackConfig",
    {
        "properties": Dict[str, Any],
        # List of regular expression that should be ignored
        "ignore_patterns_re": List[str],
    },
    total=False,
)


# Checks Black configuration
#
# The Black configuration check configuration
#
# oneOf
ChecksBlackConfiguration = Union["ChecksBlackConfigurationConfig", Literal[False]]


# Checks black configuration config
#
# The Black configuration check configuration
ChecksBlackConfigurationConfig = TypedDict(
    "ChecksBlackConfigurationConfig",
    {
        # The properties key = value that should be present
        "properties": Dict[str, Union[Union[int, float], str]],
    },
    total=False,
)


# Checks codespell
#
# The codespell check configuration
#
# oneOf
ChecksCodespell = Union["ChecksCodespellConfig", Literal[False]]


# Checks codespell config
#
# The codespell check configuration
ChecksCodespellConfig = TypedDict(
    "ChecksCodespellConfig",
    {
        # List of argument that will be added to the codespell command
        "arguments": List[str],
        # List of regular expression that should be ignored
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
ChecksIsort = Union["ChecksIsortConfig", Literal[False]]


# checks isort config
#
# The isort check configuration
ChecksIsortConfig = TypedDict(
    "ChecksIsortConfig",
    {
        # List of regular expression that should be ignored
        "ignore_patterns_re": List[str],
    },
    total=False,
)


# Checks Prettier
#
# The Prettier check configuration
#
# oneOf
ChecksPrettier = Union["ChecksPrettierConfig", Literal[False]]


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
ChecksProspectorConfiguration = Union["ChecksProspectorConfigurationConfig", Literal[False]]


# Checks prospector configuration config
#
# The Prospector configuration check configuration
ChecksProspectorConfigurationConfig = TypedDict(
    "ChecksProspectorConfigurationConfig",
    {
        # The properties key = value that should be present
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
        # Check the versions in the rebuild workflows
        #
        # oneOf
        "rebuild": Union["ChecksVersionsRebuild", Literal[False]],
    },
    total=False,
)


# checks versions rebuild
#
# Check the versions in the rebuild workflows
ChecksVersionsRebuild = TypedDict(
    "ChecksVersionsRebuild",
    {
        # The workflows files name
        "files": List[str],
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
        "publish": "Publish",
        # WARNING: The required are not correctly taken in account,
        # See: https://github.com/camptocamp/jsonschema-gentypes/issues/6
        "version": "Version",
    },
    total=False,
)


# dispatch config
#
# Send a dispatch event to an other repository
DispatchConfig = TypedDict(
    "DispatchConfig",
    {
        # The repository name to be triggered
        "repository": str,
        # The event type to be triggered
        "event-type": str,
    },
    total=False,
)


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
        # Publish the latest version on tag latest
        #
        # default: True
        "latest": bool,
        # List of images to be published
        "images": List["PublishDockerImage"],
        # The repository where we should publish the images
        "repository": Dict[str, "PublishDockerRepository"],
        # Send a dispatch event to an other repository
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
        # The image is in the group, should be used with the --group option of c2cciutils-publish script
        "group": str,
        # The image name
        "name": str,
        # The tag name, will be formatted with the version=<the version>, the image with version=latest should be present when we call the c2cciutils-publish script
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
        # The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script
        "versions": List[str],
    },
    total=False,
)


# Publish Google calendar
#
# The configuration to publish on Google Calendar
#
# oneOf
PublishGoogleCalendar = Union["PublishGoogleCalendarConfig", Literal[False]]


# Publish Google calendar config
#
# The configuration to publish on Google Calendar
PublishGoogleCalendarConfig = TypedDict(
    "PublishGoogleCalendarConfig",
    {
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
        # The image is in the group, should be used with the --group option of c2cciutils-publish script
        "group": str,
        # The path of the pypi package
        "path": str,
        # The command used to do the build
        "build_command": List[str],
    },
    total=False,
)


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
