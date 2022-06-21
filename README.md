# C2C CI utils

Commands:

- `c2cciutils`: some generic tools.
- `c2cciutils-checks`: Run the checks on the code (those checks don't need any project dependencies).
- `c2cciutils-audit`: Do the audit, the main difference with checks is that it can change between runs on the same code.
- `c2cciutils-publish`: Publish the project.
- `c2cciutils-clean`: Delete Docker images on Docker Hub after corresponding branch have been deleted.
- `c2cciutils-google-calendar`: Tool to test the google credentials for calendar API and refresh them if needed. See `c2cciutils-google-calendar -h` for more information.

# New project

The content of `example-project` can be a good base for a new project.

# Secrets

In the CI we needs to have the following secrets::

- `HAS_SECRETS` to be set to 'HAS_SECRETS', to avoid error errors from external
  pull requests, already set globally on camtocamp organisation.
- `GOPASS_CI_GITHUB_TOKEN` and `CI_GPG_PRIVATE_KEY` required to initialise the gopass password store,
  the secrets axists in the camptocamp organisation but not shared on all project, then you should add
  your project to the shared list.

# Use locally, in the projects that use c2cciutils

Install it: `python3 -m pip install --user --requirement ci/requirements.txt`
Run the checkers: `c2cciutils-checks [--fix] [--stop] [--check CHECK]`
Dry run publish: `GITHUB_REF=... c2cciutils-publish --dry-run ...`

# Configuration

You can get the current configuration with `c2cciutils --get-config`, the default configuration depends on your project.

You can override the configuration with the file `ci/config.yaml`.

At the base of the configuration you have:

- `version`: Contains some regular expressions to find the versions branches and tags, and to convert them into application versions.
- `checks`: The checkers configuration, see `c2cciutils/checks.py` for more information.
- `audit`: The audit configuration, see `c2cciutils/audit.py` for more information.
- `publish`: The publish configuration, see `c2cciutils/publish.py` for more information.

Many actions can be disabled by setting the corresponding configuration part to `False`.

# Checks

The configuration profile considers we use a project with:

- The following workflows:
  - `Continuous integration`,
  - `Rebuild` on all supported branch,
  - `Audit` for security issues on all supported branches,
  - `Backport` between all supported branches,
  - `Clean Docker hub tags`,
  - `Auto review`.
- A `SECURITY.md` file.

It will check that:

- All the workflows are conform on what we expect,
- All the workflows are completely configured for all the versions present in `SECURITY.md` file.
- The code is conform with the `black` and `isort` rules.
- The `gitattributes` are valid.
- All text files end with an empty line.

# SECURITY.md

The `SECURITY.md` file should contains the security policy of the repository, espessially the end of
support dates.

For compatibility with `c2cciutils` it should contain an array with at least the columns
`Version` and `Supported Until`. The `Version` column will contain the concerned version.
The `Supported Until` will contains the date of end of support `dd/mm/yyyy`.
It can also contain the following sentences:

- `Unsupported`: no longer supported => no audit, no rebuild.
- `Best effort`: the support is ended, it is still rebuilt and audited but this can be can stopped without any notice.
- `To be defined`: not yet released or the date will be set related of an other project release date (like for GeoMapFish).

See also [GitHub Documentation](https://docs.github.com/en/github/managing-security-vulnerabilities/adding-a-security-policy-to-your-repository)

# IDE

The IDE should be configured as:

- using `black` and `isort` without any arguments,
- using the `editorconfig` configuration.

## VScode

- Recommend extensions to work well with c2cciutils:
  - [Prettier](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) And use EditorConfig
  - [shell-format](https://marketplace.visualstudio.com/items?itemName=foxundermoon.shell-format) With the configuration
    `"shellformat.flag": "-bn"`.
- Other recommend extensions:
  - [hadolint](https://marketplace.visualstudio.com/items?itemName=exiasr.hadolint)
  - [Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker)

Select a formatter:

- `CTRL+MAJ+P`
- Format document With...
- Configure Default Formatter...
- Select the formatter

# Publishing

## To pypi

When publishing, the version computed from arguments or `GITHUB_REF` is put in environment variable `VERSION`, thus you should use it in `setup.py`, example:

```python
VERSION = os.environ.get("VERSION", "1.0.0")
```

The config is like this:

```yaml
versions:
  # List of kinds of versions you want to publish, that can be:
  # rebuild (specified with --type),
  # version_tag, version_branch, feature_branch, feature_tag (for pull request)
```

## To Docker registry

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

By default the last line of the `SECURITY.md` file will be published (`docker`) with the tag
`latest`. Set `latest` to `False` to disable it.

With the `c2cciutils-clean` the images on Docker hub for `feature_branch` will be removed on branch removing.
