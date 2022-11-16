# C2C CI utils

The goals of C2C CI utils are:

- Have some global checks that's didn't request any dependency related to the application:
  this commands return 3 types of results:
  - Print some useful information:
    - The version of some packages
    - The used configuration (with default and autodetect)
    - The environment variables
    - The GitHub event file
  - Check that some configuration where correct:
    - Git attributes
    - That the timeout is present in the GitHub workflow files
    - That the stabilization version (get from the Security.md) are used everywhere it's needed
  - Check the code style:
    - End of files
    - Black
    - Isort
    - Code spell
    - Prettier
  - Snyk tests
    - Test (never failed)
    - Code test (never failed, disabled by default)
    - Iac Test (never failed, disabled by default)
    - Fix (For information only, disabled by default)

Every check can be disabled with the following config (the configuration is `ci/config.yaml`):

```yaml
checks:
  <check name>: false
```

It make easier to place the following workflows:

- `audit.yaml`: Audit the stabilization branches of the application against vulnerabilities in the python and node dependency
- `auto-review.yaml`: Auto review the Renovate pull requests
- `backport.yaml`: Trigger the backports (work with labels)
- `clean.yaml`: Clean the Docker images related on a deleted feature branch
- `codeql.yaml`: Run a GitHub CodeQL check
- `main.yaml`: Main workflow especially with the c2cciutils-checks command
- `rebuild.yaml`: Daily rebuild of the Docker images on the stabilization branches.

All the provided commands:

- `c2cciutils`: some generic tools.
- `c2cciutils-checks`: Run the checks on the code (those checks don't need any project dependencies).
- `c2cciutils-audit`: Do the audit, the main difference with checks is that it can change between runs on the same code.
- `c2cciutils-publish`: Publish the project.
- `c2cciutils-clean`: Delete Docker images on Docker Hub after corresponding branch have been deleted.
- `c2cciutils-google-calendar`: Tool to test the Google credentials for calendar API and refresh them if needed. See `c2cciutils-google-calendar -h` for more information.
- `c2cciutils-k8s-install`: Install a k3d / k3s cluster, see below.
- `c2cciutils-k8s-db`: Create a database in the k8s cluster, see below.
- `c2cciutils-k8s-wait`: Wait that the application started correctly in the cluster, see below.
- `c2cciutils-k8s-logs`: Display the logs of the application in the k8s cluster, see below.
- `c2cciutils-pin-pipenv`: Display all the dependencies that's in the `Pipenv.lock` but not in the `Pipenv` to be able to pin them.
- `c2cciutils-docker-logs`: Display the logs of the application in Docker (compose).
- `c2cciutils-trigger-image-update`: Trigger the ArgoCD repository about image update on the CI (automatically done in the publishing).
- `c2cciutils-download-applications`: Download the applications with version managed by Renovate, see below.
- `c2cciutils-docker-versions-gen`: Generate the Docker package versions file (`ci/dpkg-versions.yaml`), see below.

## New project

The content of `example-project` can be a good base for a new project.

## Secrets

In the CI we need to have the following secrets::

- `HAS_SECRETS` to be set to 'HAS_SECRETS', to avoid error errors from external
  pull requests, already set globally on Camptocamp organization.
- `GOPASS_CI_GITHUB_TOKEN` and `CI_GPG_PRIVATE_KEY` required to initialize the gopass password store,
  the secrets exists in the Camptocamp organization but not shared on all project, then you should add
  your project to the shared list.

## Use locally, in the projects that use c2cciutils

Install it: `python3 -m pip install --user --requirement ci/requirements.txt`
Run the checkers: `c2cciutils-checks [--fix] [--stop] [--check CHECK]`
Dry run publish: `GITHUB_REF=... c2cciutils-publish --dry-run ...`

## Configuration

You can get the current configuration with `c2cciutils --get-config`, the default configuration depends on your project.
Note that it didn't contain the default defined the schema and visible in the [generated documentation](./config.md).

You can override the configuration with the file `ci/config.yaml`.

At the base of the configuration you have:

- `version`: Contains some regular expressions to find the versions branches and tags, and to convert them into application versions.
- `checks`: The checker's configuration, see `c2cciutils/checks.py` for more information.
- `audit`: The audit configuration, see `c2cciutils/audit.py` for more information.
- `publish`: The publishing configuration, see `c2cciutils/publish.py` for more information.

Many actions can be disabled by setting the corresponding configuration part to `False`.

## SECURITY.md

The `SECURITY.md` file should contain the security policy of the repository, especially the end of
support dates.

For compatibility with `c2cciutils` it should contain an array with at least the columns
`Version` and `Supported Until`. The `Version` column will contain the concerned version.
The `Supported Until` will contain the date of end of support `dd/mm/yyyy`.
It can also contain the following sentences:

- `Unsupported`: no longer supported => no audit, no rebuild.
- `Best effort`: the support is ended, it is still rebuilt and audited, but this can be stopped without any notice.
- `To be defined`: not yet released or the date will be set related of another project release date (like for GeoMapFish).

See also [GitHub Documentation](https://docs.github.com/en/github/managing-security-vulnerabilities/adding-a-security-policy-to-your-repository)

## IDE

The IDE should be configured as:

- using `black` and `isort` without any arguments,
- using the `editorconfig` configuration.

### VScode

- Recommend extensions to work well with c2cciutils:
  - [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) And use EditorConfig
  - [shell-format](https://marketplace.visualstudio.com/items?itemName=foxundermoon.shell-format) With the configuration
    `"shellformat.flag": "-bn"`.
  - [Better TOML](https://marketplace.visualstudio.com/items?itemName=bodil.prettier-toml)
- Other recommend extensions:
  - [hadolint](https://marketplace.visualstudio.com/items?itemName=exiasr.hadolint)
  - [Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)

Select a formatter:

- `CTRL+MAJ+P`
- Format document With...
- Configure Default Formatter...
- Select the formatter

## Publishing

### To pypi

The config is like this:

```yaml
versions:
  # List of kinds of versions you want to publish, that can be:
  # rebuild (specified with --type),
  # version_tag, version_branch, feature_branch, feature_tag (for pull request)
```

It we have a `setup.py` file, we will be in legacy mode:
When publishing, the version computed from arguments or `GITHUB_REF` is put in environment variable `VERSION`, thus you should use it in `setup.py`, example:

```python
VERSION = os.environ.get("VERSION", "1.0.0")
```

Also we consider that we use `poetry` with [poetry-dynamic-versioning](https://pypi.org/project/poetry-dynamic-versioning/) to manage the version, and [poetry-plugin-tweak-dependencies-version](https://pypi.org/project/poetry-plugin-tweak-dependencies-version/) to manage the dependencies versions.

Example of configuration:

```toml
[tool.poetry-dynamic-versioning]
enable = true
vcs = "git"
pattern = "^(?P<base>\\d+(\\.\\d+)*)"
format-jinja = """
{%- if env.get("VERSION_TYPE") == "version_branch" -%}
{{serialize_pep440(bump_version(base, 1 if env.get("IS_MASTER") == "TRUE" else 2), dev=distance)}}
{%- elif distance == 0 -%}
{{serialize_pep440(base)}}
{%- else -%}
{{serialize_pep440(bump_version(base), dev=distance)}}
{%- endif -%}
"""

```

Note that we can access to the environment variables `VERSION`,`VERSION_TYPE` and `IS_MASTER`.

Then by default:

- Tag with `1.2.3` => release `1.2.3`
- Commit on feature branch just do a validation
- Commit on `master` branch after the tag 1.3.0 => release `1.4.0.dev1`
- Commit on `1.3` branch after the tag 1.3.0 => release `1.3.1.dev1`

To make it working in the `Dockerfile` you should have in the `poetry` stage:

```Dockerfile
ENV POETRY_DYNAMIC_VERSIONING_BYPASS=dev
RUN poetry export --extras=checks --extras=publish --extras=audit --output=requirements.txt \
    && poetry export --with=dev --output=requirements-dev.txt
```

And in the `run` stage

```Dockerfile
ARG VERSION=dev
RUN --mount=type=cache,target=/root/.cache \
    POETRY_DYNAMIC_VERSIONING_BYPASS=${VERSION} python3 -m pip install --disable-pip-version-check --no-deps --editable=.
```

And in the `Makefile`:

```Makefile
VERSION = $(strip $(shell poetry version --short))

.PHONY: build
build: ## Build the Docker images
    docker build --build-arg=VERSION=$(VERSION) --tag=$(GITHUB_REPOSITORY) .
```

### To Docker registry

The config is like this:

```yaml
latest: True
images:
  - name: # The base name of the image we want to publish
repository:
  <internal_name>:
    'server': # The fqdn name of the server if not Docker hub
    'version':# List of kinds of versions you want to publish, that can be: rebuild (specified using --type),
      # version_tag, version_branch, feature_branch, feature_tag (for pull request)
    'tags':# List of tags we want to publish interpreted with `template(version=version)`
      # e.g. if you use `{version}-lite` when you publish the version `1.2.3` the source tag
      # (that should be built by the application build) is `latest-lite`, and it will be published
      # with the tag `1.2.3-lite`.
    'group':# If your images are published by different jobs you can separate them in different groups
      # and publish them with `c2cciutils-publish --group=<group>`
```

By default, the last line of the `SECURITY.md` file will be published (`docker`) with the tag
`latest`. Set `latest` to `False` to disable it.

With the `c2cciutils-clean` the images on Docker hub for `feature_branch` will be removed on branch removing.

## Download applications

In case some executables or applications from GitHub releases or any other URLs are required on the CI host
and are not handled by any dependency manager, we provide a set of tools to install them and manage upgrades
through Renovate.

Create an application file (e.-g. `applications.yaml`) with:

```yaml
# yaml-language-server: $schema=https://raw.githubusercontent.com/camptocamp/c2cciutils/master/c2cciutils/schema-applications.json

# Application from GitHub release
<organization>/<project>:
  get-file-name: <file name present in the release>
  to-file-name: <The file name you want to create in ~/.local/bin>
  finish-command: # The command you want to run after the file is downloaded
    - - chmod # To be executable (usually required)
      - +x
      - <to-file-name>
    - - <to-file-name> # Print the version of the application
      - --version
# Application from GitHub release in a tar file (or tar.gz)
<organization>/<project>:
  get-file-name: <file name present in the release>
  type: tar
  tar-file-name: <The file name available in the tar file>
  to-file-name: <The file name you want to create in ~/.local/bin>
  finish-command: [...] # The command you want to run after the file is downloaded
# Application from an URL
<application reference name>:
  url-pattern: <The URL used to download the application>
  to-file-name: <The file name you want to create in ~/.local/bin>
  finish-command: [...] # The command you want to run after the file is downloaded
```

In the attributes `url-pattern`, `get-file-name` you can use the following variables:

- `{version}`: The version of the application present in the version file.
- `{version_quote}`: The URL encoded version.
- `{short_version}`: The version without the `v` prefix.

The `applications-versions.yaml` file is a map of applications and their versions.

Add in your Renovate configuration:

```json5

  regexManagers: [
    {
      fileMatch: ['^applications-versions.yaml$'],
      matchStrings: [
        '(?<depName>[^\\s]+): (?<currentValue>[^\\s]+) # (?<datasource>[^\\s]+)',
      ],
    },
  ],
```

Now you need to call `c2cciutils-download-applications --applications-file=applications.yaml --versions-file=applications-version.yaml`
to install required applications on CI host before using them (an already installed application is installed only if needed).

## Use Renovate to trigger a new build instead of the legacy rebuild

Run the command `c2cciutils-docker-versions-gen camptocamp/image[:tag]` to generate a file that is a kind of package lock of the Debian packages in the file `ci/dpkg-versions.yaml`.

Add in your renovate configuration:

```javascript
  regexManagers: [
    {
      fileMatch: ['^ci/dpkg-versions.yaml$'],
      matchStrings: [" *(?<depName>[^'\\s]+): '?(?<currentValue>[^'\\s/]*[0-9][^'\\s/]*)'?"],
      datasourceTemplate: 'repology',
      versioningTemplate: 'loose',
    },
  ],
```

When a new version of a Debian package will be available:

- Renovate will automatically open a pull request to update the file `ci/dpkg-versions.yaml`.
- And the continuous integration will build a new fresh Docker image with latest versions of all Debian packages.

## Kubernetes

C2cciutils provide some commands for Kubernetes.

You can define a workflow like that:

```yaml
- name: Install k3s/k3d (Kubernetes cluster)
  run: c2cciutils-k8s-install

- name: Create a database to do the tests
  run: c2cciutils-k8s-db --script=<my_script>.sql

- name: Install the application in the Kubernetes cluster
  run: kubectl apply -f <my_application>.yaml

- name: Wait that the application is ready
  run: c2cciutils-k8s-wait
- name: Print the application status and logs
  run: c2cciutils-k8s-logs
  if: always()

- name: Uninstall the application
  run: kubectl delete -f <my_application>.yaml || true

- name: Cleanup the database
  run: c2cciutils-k8s-db --cleanup
```

`c2cciutils-k8s-install` can be configured in the `ci/config.yaml` file, in section `k8s/k3d/install-commands`, default is:

```yaml
- - k3d
    cluster
    create
    test-cluster
    --no-lb
    --no-rollback
```

See also: [K3d cluster create documentation](https://k3d.io/v4.4.8/usage/commands/k3d_cluster_create/).

`c2cciutils-k8s-db` can be configured in the `ci/config.yaml` file, in section `k8s/db/chart-options`, default is:

```yaml
persistence.enabled: 'false'
tls.enabled: 'true'
tls.autoGenerated: 'true'
postgresqlPassword: mySuperTestingPassword
volumePermissions.enabled: 'true'
```

See also: [Parameters documentations](https://github.com/bitnami/charts/tree/master/bitnami/postgresql#parameters).
