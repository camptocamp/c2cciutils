"""
Automatically generated file from a JSON schema.
"""

from typing import Any, TypedDict


class Configuration(TypedDict, total=False):
    """
    configuration.

    C2C CI utils configuration file
    """

    print_versions: "PrintVersions"
    """
    Print versions.

    The print versions configuration
    """

    k8s: "K8SConfiguration"
    """
    K8s configuration.

    default:
      {}
    """


DB_CONFIGURATION_DEFAULT: dict[str, Any] = {}
""" Default value of the field path 'K8s configuration db' """


# | DB configuration.
# |
# | Database configuration
# |
# | default:
# |   {}
DbConfiguration = TypedDict(
    "DbConfiguration",
    {
        # | K8S DB chart options.
        # |
        # | default:
        # |   auth.postgresPassword: mySuperTestingPassword
        # |   persistence.enabled: 'false'
        # |   tls.autoGenerated: 'true'
        # |   tls.enabled: 'true'
        # |   volumePermissions.enabled: 'true'
        "chart-options": dict[str, str],
    },
    total=False,
)


# | K3d configuration.
# |
# | default:
# |   {}
K3DConfiguration = TypedDict(
    "K3DConfiguration",
    {
        # | K3D install commands.
        # |
        # | default:
        # |   - - k3d
        # |     - cluster
        # |     - create
        # |     - test-cluster
        # |     - --no-lb
        # |     - --no-rollback
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
    """
    K3d configuration.

    default:
      {}
    """

    db: "DbConfiguration"
    """
    DB configuration.

    Database configuration

    default:
      {}
    """


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
    {"name": "python", "cmd": ["python3", "--version"]},
    {"name": "pip", "cmd": ["python3", "-m", "pip", "--version"]},
    {"name": "node", "prefix": "node ", "cmd": ["node", "--version"]},
    {"name": "npm", "prefix": "npm ", "cmd": ["npm", "--version"]},
    {"name": "make", "cmd": ["make", "--version"]},
    {"name": "docker", "cmd": ["docker", "--version"]},
    {"name": "docker compose", "cmd": ["docker", "compose", "version"]},
    {"name": "java", "cmd": ["java", "-version"]},
    {"name": "helm", "cmd": ["helm", "version"], "prefix": "HELM: "},
]
""" Default value of the field path 'Print versions versions' """


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
        prefix: 'HELM: '
    """


class _PrintVersionsVersionsItem(TypedDict, total=False):
    cmd: list[str]
    """ The command that should be used """

    name: str
    """ The name """

    prefix: str
    """ Prefix added when we print the version """
