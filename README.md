# C2C CI utils


Commands:
  - `c2cciutils`: some generic tools.
  - `c2cciutils-checks`: Run the checks on the code (those checks don't need any project dependencies).
  - `c2cciutils-audit`: Do the audit, the main difference with checks is that it can change between runs on the same code.
  - `c2cciutils-publish`: Publish the project.
  - `c2cciutils-clean`: Delete Docker images on Docker Hub after corresponding branch have been deleted.


# New project

The content of `example-project` can be a good base for a new project.


# Configuration

You can get the current configuration with `c2cciutils --get-config`, the default configuration depends on your project.

You can override the configuration with the file `ci/config.yaml`.

At the base of the configuration you have:

* `version`: Contains some regular expressions to find the versions branches and tags, and to convert them into application versions.
* `checks`: The checkers configuration, see `c2cciutils/checks.py` for more information.
* `audit`: The audit configuration, see `c2cciutils/audit.py` for more information.
* `publish`: The publish configuration, see `c2cciutils/publish.py` for more information.

Many actions can be disabled by setting the corresponding configuration part to `False`.

# Checks

The configuration profile consider we use a project with:

-   Dependabot.
-   The following workflows:
    -   `Continuous integration`,
    -   `Rebuild` on all supported branch,
    -   `Audit` for security issues on all supported branches,
    -   `Backport` between all supported branches,
    -   `Clean Docker hub tags`,
    -   `Auto merge Dependabot updates`.
-   A `SECURITY.md` file.

It will check that:

-   All the workflows are conform on what we expect,
-   All the workflows are completely configured for all the versions present in `SECURITY.md` file.
-   The code is conform with the `black` and `isort` rules.
-   The `gitattributes` are valid.
-   All text files end with an empty line.

# IDE

The IDE should be configured as:

-   using `black` and `isort` without any arguments,
-   using the `editorconfig` configuration.

# Publishing

## To pypi

When publishing, the version computed from arguments or `GITHUB_REF` is put in environment variable `VERSION`, thus you should use it in `setup.py`, example:

```python
VERSION = os.environ.get("VERSION", "1.0.0")
```

The config is like this:

```yaml
    versions: # List of kinds of versions you want to publish, that can be: rebuild (specified with --type),
        # version_tag, version_branch, feature_branch, feature_tag (for pull request)
```

## To Docker registry

The config is like this:

```yaml
images:
  - name: # The base name of the image we want to publish
repository:
  <internal_name>:
      "server": # The fqdn name of the server if not Docker hub
      "version": # List of kinds of versions you want to publish, that can be: rebuild (specified using --type),
          # version_tag, version_branch, feature_branch, feature_tag (for pull request)
      "tags": # List of tags we want to publish interpreted with `template(version=version)`
          # e.-g. if you use `{version}-lite` when you publish the version `1.2.3` the source tag
          # (that should be built by the application build) is `latest-lite`, and it will be published
          # with the tag `1.2.3-lite`.
      "group": # If your images are published by different jobs you can separate them in different groups
          # and publish them with `c2cciutils-publish --group=<group>`
```

With the `c2cciutils-clean` the images on Docker hub for `feature_branch` will be removed on branch removing.
