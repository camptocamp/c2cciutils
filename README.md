# C2C CI utils

## Publishing

The main goals of C2C CI utils is to offer the commands to publish the project,
see the [documentation](https://github.com/camptocamp/c2cciutils/wiki/Publishing).

## Changelog

When we create a tag by default with the `changelog` workflow a release is created on GitHub, a changelog is
generated and added to the release.

## Checks

C2C CI utils will no more provide a tool to do a check of the project, this is replaced by `pre-commit`,
a base configuration is provided in the example project.

## Pull request checks

A workflow is provided to run the checks on the pull requests, it will run the `c2cciutils-pr-checks` command.

- Check that the commit message and the pull request title start with a capital letter.
- Check that there aren't any spelling issue in the commit message and in the pull request title.
- Add a message to the pull request with a link to the JIRA issue if the pull request branch name starts with
  `[a-zA-Z]+-[0-9]+-` or end with `-[a-zA-Z]+-[0-9]+`.

## Dependencies

In the example project there is a basic Renovate configuration, it will update the dependencies of the project.
There is also a workflow to add a review on the Renovate pull requests to make the auto merge working on
repository that required a review.

## Backports

A workflow is provided to backport the pull requests on the stabilization branches, it will be triggered by
adding a label named `backport <destination_branch>` on the pull request.

## Old workflows

GitHub will retain all the old workflows, so we need to delete them, the `delete-old-workflows-run`
workflow will delete the workflows older than 500 days.

## Workflows

C2cciutils make easier to have those workflows in a project:

- `auto-review.yaml`: Auto review the Renovate pull requests
- `backport.yaml`: Trigger the backports (work with labels)
- `main.yaml`: Main workflow especially with the c2cciutils-checks command

All the provided commands used in the workflow:

- `c2cciutils`: some generic tools.
- `c2cciutils-version`: Create a new version of the project.
- `c2cciutils-env`: Print some environment information.

## Utilities

The following utilities are provided:

- `c2cciutils`: some generic tools.
- `c2cciutils-download-applications`: Download the applications with version managed by Renovate, see below.
- `c2cciutils-docker-logs`: Display the logs of the application in Docker (compose).
- `c2cciutils-k8s-install`: Install a k3d / k3s cluster, see below.
- `c2cciutils-k8s-logs`: Display the logs of the application in the k8s cluster, see below.
- `c2cciutils-k8s-db`: Create a database in the k8s cluster, see below.
- `c2cciutils-k8s-wait`: Wait that the application started correctly in the cluster, see below.
- `c2cciutils-docker-versions-gen`: Generate the Docker package versions file (`ci/dpkg-versions.yaml`), see below.
- `c2cciutils-pin-pipenv`: Display all the dependencies that's in the `Pipenv.lock` but not in the `Pipenv` to be able to pin them.
- `c2cciutils-trigger-image-update`: Trigger the ArgoCD repository about image update on the CI (automatically done in the publishing).
- `c2cciutils-google-calendar`: Tool to test the Google credentials for calendar API and refresh them if needed. See `c2cciutils-google-calendar -h` for more information.

## New project

The content of `example-project` can be a good base for a new project.

## New version

Requirements: the right version (>= 1.6) of `c2cciutils` should be installed with the `version` extra.

To create a new minor version you just should run `c2cciutils-version --version=<version>`.

You are welcome to run `c2cciutils-version --help` to see what's it's done.

Note that it didn't create a tag, you should do it manually.

To create a patch version you should just create tag.

## Secrets

In the CI we need to have the following secrets::

- `HAS_SECRETS` to be set to 'HAS_SECRETS', to avoid error errors from external
  pull requests, already set globally on Camptocamp organization.
- `GOPASS_CI_GITHUB_TOKEN` and `CI_GPG_PRIVATE_KEY` required to initialize the gopass password store,
  the secrets exists in the Camptocamp organization but not shared on all project, then you should add
  your project to the shared list.

## Use locally, in the projects that use c2cciutils

Install it: `python3 -m pip install --user --requirement ci/requirements.txt`

## Configuration

You can get the current configuration with `c2cciutils --get-config`, the default configuration depends on your project.
Note that it didn't contain the default defined the schema and visible in the [generated documentation](./config.md).

You can override the configuration with the file `ci/config.yaml`.

At the base of the configuration you have:

- `version`: Contains some regular expressions to find the versions branches and tags, and to convert them into application versions.
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

## Contributing

Install the pre-commit hooks:

```bash
pip install pre-commit
pre-commit install --allow-missing-config
```
