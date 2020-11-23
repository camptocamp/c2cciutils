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
