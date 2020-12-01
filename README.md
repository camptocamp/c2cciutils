# c2c CI utils


Commands:
  - c2cciutils: some generic tools.
  - c2cciutils-checks: Run the checks on the code (those checks don't need any project dependencies).
  - c2cciutils-audit: Do the audit, the main difference with checks is that it can change between runs on the same code.
  - c2cciutils-publish: Publish the project.
  - c2cciutils-clean: Delete Docker images on Docker Hub after corresponding branch have been deleted.


# New project

The content of example-project can be a good base for a new project.

# Configuration

You can get the currunt configuration with `c2cciutils --get-config`, the default configuration depends on your project.

You can override the configuration with the file `ci/config.yaml`.

At the base of the configuration you have:

* `version`: Contains some regular expressions to find the versions branches and tags, and to convert them into application versions.
* `checks`: The checkers configuration, see `c2cciutils/checks.py` for more information.
* `audit`: The audit configuration, see `c2cciutils/audit.py` for more information.
* `publish`: The publish configuration, see `c2cciutils/publish.py` for more information.

Many actions can be disabled by setting the corresponding configuration part to `False`.

# Publishing

## To pypi

When publishing the computed version is set as the environment variable 'VERSION' than you can use it in
the `setup.py`.

The config is like this:

```yaml
    versions: # List of kind of version you vant to publish, that can be: custom (used by rebuild),
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
      "version": # List of kind of version you vant to publish, that can be: custom (used by rebuild),
          # version_tag, version_branch, feature_branch, feature_tag (for pull request)
      "tags": # List of tags we want to publish interpreter with `template(version=version)`
          # the image should be built with `version = 'latest'`
      "group": # If your images are published by different job you can separate them in different groups
          # and publish them with `c2cciutils-publisg --group=<group>`
```

With the `c2cciutils-clean` the images on Docker hub for `feature_branch` will be removed on branch removing.
