# configuration

_C2C CI utils configuration file_

## Properties

- **`audit`** _(object)_: The audit configuration. Default: `{"print_versions": {"versions": [{"name": "c2cciutils", "cmd": ["c2cciutils", "--version"]}, {"name": "python", "cmd": ["python3", "--version"]}, {"name": "safety", "cmd": ["safety", "--version"]}, {"name": "node", "prefix": "node ", "cmd": ["node", "--version"]}, {"name": "npm", "prefix": "npm ", "cmd": ["npm", "--version"]}]}, "npm": true, "snyk": true, "outdated_versions": true}`.
  - **`npm`**: Refer to _[#/definitions/audit_npm](#definitions/audit_npm)_.
  - **`outdated_versions`**: Refer to _[#/definitions/audit_outdated_versions](#definitions/audit_outdated_versions)_.
  - **`snyk`**: Refer to _[#/definitions/audit_snyk](#definitions/audit_snyk)_.
  - **`print_versions`**: Refer to _[#/definitions/print_versions](#definitions/print_versions)_.
- **`checks`** _(object)_: The checkers configurations. Default: `{"print_versions": {"versions": [{"name": "c2cciutils", "cmd": ["c2cciutils", "--version"]}, {"name": "codespell", "cmd": ["codespell", "--version"], "prefix": "codespell "}, {"name": "java", "cmd": ["java", "-version"]}, {"name": "python", "cmd": ["python3", "--version"]}, {"name": "pip", "cmd": ["python3", "-m", "pip", "--version"]}, {"name": "node", "prefix": "node ", "cmd": ["node", "--version"]}, {"name": "npm", "prefix": "npm ", "cmd": ["npm", "--version"]}, {"name": "docker", "cmd": ["docker", "--version"]}, {"name": "docker-compose", "cmd": ["docker-compose", "--version"]}, {"name": "kubectl", "cmd": ["kubectl", "version"]}, {"name": "make", "cmd": ["make", "--version"], "prefix": "make "}, {"name": "pip_packages", "cmd": ["pip", "freeze", "--all"], "prefix": "pip packages: "}, {"name": "npm_packages", "cmd": ["npm", "list", "--all", "--global"]}]}, "print_config": true, "print_environment_variables": true, "print_github_event": true, "gitattribute": true, "eof": true, "workflows": true, "black": true, "isort": true, "codespell": true, "prettier": true, "snyk": true, "snyk_code": false, "snyk_iac": false, "snyk_fix": false}`.
  - **`black`**: Refer to _[#/definitions/checks_black](#definitions/checks_black)_.
  - **`codespell`**: Refer to _[#/definitions/checks_codespell](#definitions/checks_codespell)_.
  - **`eof`**: Refer to _[#/definitions/checks_eof](#definitions/checks_eof)_.
  - **`gitattribute`**: Refer to _[#/definitions/checks_gitattribute](#definitions/checks_gitattribute)_.
  - **`isort`**: Refer to _[#/definitions/checks_isort](#definitions/checks_isort)_.
  - **`print_config`**: Refer to _[#/definitions/checks_print_config](#definitions/checks_print_config)_.
  - **`workflows`**: Refer to _[#/definitions/checks_workflows](#definitions/checks_workflows)_.
  - **`snyk`**: Refer to _[#/definitions/checks_snyk](#definitions/checks_snyk)_.
  - **`snyk_code`**: Refer to _[#/definitions/checks_snyk_code](#definitions/checks_snyk_code)_.
  - **`snyk_iac`**: Refer to _[#/definitions/checks_snyk_iac](#definitions/checks_snyk_iac)_.
  - **`snyk_fix`**: Refer to _[#/definitions/checks_snyk_fix](#definitions/checks_snyk_fix)_.
  - **`prettier`**: Refer to _[#/definitions/checks_prettier](#definitions/checks_prettier)_.
  - **`print_versions`**: Refer to _[#/definitions/print_versions](#definitions/print_versions)_.
- **`pr-checks`** _(object)_: The PR check configuration. Default: `{"commits_messages": true, "commits_spell": true, "pull_request_spell": true, "pull_request_labels": true, "add_issue_link": true}`.
  - **`print_event`**: Refer to _[#/definitions/pr_checks_print_event](#definitions/pr_checks_print_event)_.
  - **`commits_messages`**: Refer to _[#/definitions/pr_checks_commits_messages](#definitions/pr_checks_commits_messages)_.
  - **`commits_spell`**: Refer to _[#/definitions/pr_checks_commits_spell](#definitions/pr_checks_commits_spell)_.
  - **`pull_request_spell`**: Refer to _[#/definitions/pr_checks_pull_request_spell](#definitions/pr_checks_pull_request_spell)_.
  - **`pull_request_labels`**: Refer to _[#/definitions/pr_checks_pull_request_labels](#definitions/pr_checks_pull_request_labels)_.
  - **`add_issue_link`**: Refer to _[#/definitions/pr_checks_add_issue_link](#definitions/pr_checks_add_issue_link)_.
- **`publish`** _(object)_: The publishing configurations. Default: `{"print_versions": {"versions": [{"name": "c2cciutils", "cmd": ["c2cciutils", "--version"]}, {"name": "python", "cmd": ["python3", "--version"]}, {"name": "twine", "cmd": ["twine", "--version"]}, {"name": "docker", "cmd": ["docker", "--version"]}]}, "pypi": {"versions": ["version_tag"], "packages": "<auto-detected>"}, "docker": {"images": "<auto-detected>"}, "helm": {"versions": ["version_tag"], "folders": "<auto-detected>"}}`.
  - **`docker`**: Refer to _[#/definitions/publish_docker](#definitions/publish_docker)_.
  - **`pypi`**: Refer to _[#/definitions/publish_pypi](#definitions/publish_pypi)_.
  - **`helm`**: Refer to _[#/definitions/publish_helm](#definitions/publish_helm)_.
  - **`google_calendar`**: Refer to _[#/definitions/publish_google_calendar](#definitions/publish_google_calendar)_.
  - **`print_versions`**: Refer to _[#/definitions/print_versions](#definitions/print_versions)_.
- **`version`** _(object)_: The version configurations.
  - **`branch_to_version_re`**: Refer to _[#/definitions/version_transform](#definitions/version_transform)_.
  - **`tag_to_version_re`**: Refer to _[#/definitions/version_transform](#definitions/version_transform)_.
- **`k8s`** _(object)_: Default: `{}`.
  - **`k3d`** _(object)_: Default: `{}`.
    - **`install-commands`** _(array)_: Default: `[["k3d", "cluster", "create", "test-cluster", "--no-lb", "--no-rollback"]]`.
      - **Items** _(array)_
        - **Items** _(string)_
  - **`db`** _(object)_: Database configuration. Default: `{}`.
    - **`chart-options`** _(object)_: Can contain additional properties. Default: `{"persistence.enabled": "false", "tls.enabled": "true", "tls.autoGenerated": "true", "auth.postgresPassword": "mySuperTestingPassword", "volumePermissions.enabled": "true"}`.
      - **Additional Properties** _(string)_

## Definitions

- <a id="definitions/audit_npm"></a>**`audit_npm`**: The npm audit configuration.
  - **One of**
    - _object_: The npm audit configuration.
      - **`cwe_ignore`** _(array)_: The list of CWE id to be ignored. Default: `[]`.
        - **Items** _(string)_
      - **`package_ignore`** _(array)_: The list of package names to be ignored. Default: `[]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/audit_outdated_versions"></a>**`audit_outdated_versions`** _(boolean)_: Audit of outdated version.
- <a id="definitions/audit_snyk"></a>**`audit_snyk`**: The audit snyk configuration.
  - **One of**
    - _object_: The audit Pipfile configuration.
      - **`test_arguments`** _(array)_: The snyk test arguments. Default: `["--all-projects", "--fail-on=all", "--severity-threshold=medium"]`.
        - **Items** _(string)_
      - **`monitor_arguments`** _(array)_: The snyk monitor arguments. Default: `["--all-projects"]`.
        - **Items** _(string)_
      - **`fix_arguments`** _(array)_: The snyk fix arguments. Default: `["--all-projects"]`.
        - **Items** _(string)_
      - **`fix_github_create_pull_request_arguments`** _(array)_: The snyk fix pull request extra arguments. Default: `["--fill", "--label=dependencies"]`.
        - **Items** _(string)_
      - **`pip_install_arguments`** _(array)_: The snyk pip install arguments. Default: `["--user"]`.
        - **Items** _(string)_
      - **`pipenv_sync_arguments`** _(array)_: The snyk pipenv sync arguments. Default: `[]`.
        - **Items** _(string)_
      - **`files_no_install`** _(array)_: The list of files to not install. Default: `[]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/checks_black"></a>**`checks_black`**: The Black check configuration.
  - **One of**
    - _object_: The Black check configuration.
      - **`properties`** _(object)_
      - **`ignore_patterns_re`** _(array)_: List of regular expression that should be ignored. Default: `[]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/checks_prettier"></a>**`checks_prettier`**: The Prettier check configuration.
  - **One of**
    - _object_: The Prettier check configuration.
      - **`properties`** _(object)_
    - _boolean_
- <a id="definitions/checks_codespell"></a>**`checks_codespell`**: The codespell check configuration.
  - **One of**
    - _object_: The codespell check configuration.
      - **`internal_dictionaries`** _(array)_: List of argument that will be added to the codespell command. Default: `["clear", "rare", "informal", "code", "names", "en-GB_to_en-US"]`.
        - **Items** _(string)_
      - **`arguments`** _(array)_: List of argument that will be added to the codespell command. Default: `["--quiet-level=2", "--check-filenames", "--ignore-words-list=ro"]`.
        - **Items** _(string)_
      - **`ignore_re`** _(array)_: List of regular expression that should be ignored. Default: `["(.*/)?poetry\\.lock", "(.*/)?package-lock\\.json"]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/checks_eof"></a>**`checks_eof`** _(boolean)_: Check the end-of-file.
- <a id="definitions/checks_gitattribute"></a>**`checks_gitattribute`** _(boolean)_: Run the Git attributes check.
- <a id="definitions/checks_isort"></a>**`checks_isort`**: The isort check configuration.
  - **One of**
    - _object_: The isort check configuration.
      - **`ignore_patterns_re`** _(array)_: List of regular expression that should be ignored. Default: `[]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/checks_print_config"></a>**`checks_print_config`** _(boolean)_: The print the configuration including the auto-generated parts.
- <a id="definitions/checks_workflows"></a>**`checks_workflows`** _(boolean)_: The workflows checks configuration.
- <a id="definitions/checks_snyk"></a>**`checks_snyk`**: The check snyk configuration.
  - **One of**
    - _object_
      - **`arguments`** _(array)_: The snyk code test arguments. Default: `["--severity-threshold=medium"]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/checks_snyk_code"></a>**`checks_snyk_code`**: The check snyk code configuration.
  - **One of**
    - _object_
      - **`arguments`** _(array)_: The snyk code test arguments. Default: `["--all-projects", "--severity-threshold=medium"]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/checks_snyk_iac"></a>**`checks_snyk_iac`**: The check snyk iac configuration.
  - **One of**
    - _object_
      - **`arguments`** _(array)_: The snyk code test arguments. Default: `["--severity-threshold=medium"]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/checks_snyk_fix"></a>**`checks_snyk_fix`**: The check snyk fix configuration.
  - **One of**
    - _object_
      - **`arguments`** _(array)_: The snyk code test arguments. Default: `[]`.
        - **Items** _(string)_
    - _boolean_
- <a id="definitions/pr_checks_print_event"></a>**`pr_checks_print_event`** _(boolean)_: Print the GitHub event object.
- <a id="definitions/pr_checks_commits_messages"></a>**`pr_checks_commits_messages`**: Check the pull request commits messages.
  - **One of**
    - _object_: The commit message check configuration.
      - **`check_fixup`** _(boolean)_: Check that we don't have one fixup commit in the pull request. Default: `true`.
      - **`check_squash`** _(boolean)_: Check that we don't have one squash commit in the pull request. Default: `true`.
      - **`check_first_capital`** _(boolean)_: Check that the all the commits message starts with a capital letter. Default: `true`.
      - **`min_head_length`** _(integer)_: Check that the commits message head is at least this long, use 0 to disable. Default: `5`.
      - **`check_no_merge_commits`** _(boolean)_: Check that we don't have merge commits in the pull request. Default: `true`.
      - **`check_no_own_revert`** _(boolean)_: Check that we don't have reverted one of our commits in the pull request. Default: `true`.
    - _boolean_
- <a id="definitions/pr_checks_commits_spell"></a>**`pr_checks_commits_spell`**
  - **One of**
    - _object_: Configuration used to check the spelling of the commits.
      - **`only_head`** _(boolean)_: Default: `true`.
    - _boolean_
- <a id="definitions/pr_checks_pull_request_spell"></a>**`pr_checks_pull_request_spell`**
  - **One of**
    - _object_: Configuration used to check the spelling of the title and body of the pull request.
      - **`only_head`** _(boolean)_: Default: `true`.
    - _boolean_
- <a id="definitions/pr_checks_pull_request_labels"></a>**`pr_checks_pull_request_labels`** _(boolean)_: According the create changelog configuration.
- <a id="definitions/pr_checks_add_issue_link"></a>**`pr_checks_add_issue_link`** _(boolean)_
- <a id="definitions/publish_docker"></a>**`publish_docker`**: The configuration used to publish on Docker.
  - **One of**
    - _object_: The configuration used to publish on Docker.
      - **`latest`** _(boolean)_: Publish the latest version on tag latest. Default: `true`.
      - **`images`** _(array)_: List of images to be published.
        - **Items** _(object)_
          - **`group`** _(string)_: The image is in the group, should be used with the --group option of c2cciutils-publish script. Default: `"default"`.
          - **`name`** _(string)_: The image name.
          - **`tags`** _(array)_: The tag name, will be formatted with the version=<the version>, the image with version=latest should be present when we call the c2cciutils-publish script. Default: `["{version}"]`.
            - **Items** _(string)_
      - **`repository`** _(object)_: The repository where we should publish the images. Can contain additional properties. Default: `{"github": {"server": "ghcr.io", "versions": ["version_tag", "version_branch", "rebuild"]}, "dockerhub": {}}`.
        - **Additional Properties** _(object)_
          - **`server`** _(string)_: The server URL.
          - **`versions`** _(array)_: The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script. Default: `["version_tag", "version_branch", "rebuild", "feature_branch"]`.
            - **Items** _(string)_
      - **`dispatch`**: Send a dispatch event to an other repository. Default: `{}`.
        - **One of**
          - _object_: Send a dispatch event to an other repository.
            - **`repository`** _(string)_: The repository name to be triggered. Default: `"camptocamp/argocd-gs-platform-ch-development-apps"`.
            - **`event-type`** _(string)_: The event type to be triggered. Default: `"image-update"`.
          -
    -
- <a id="definitions/publish_google_calendar"></a>**`publish_google_calendar`**: The configuration to publish on Google Calendar. Default: `{}`.
  - **One of**
    - _object_: The configuration to publish on Google Calendar.
      - **`on`** _(array)_: Default: `["version_branch", "version_tag", "rebuild"]`.
        - **Items** _(string)_
    -
- <a id="definitions/publish_pypi"></a>**`publish_pypi`**: Configuration to publish on pypi. Default: `{}`.
  - **One of**
    - _object_: Configuration to publish on pypi.
      - **`packages`** _(array)_: The configuration of packages that will be published.
        - **Items** _(object)_: The configuration of package that will be published.
          - **`group`** _(string)_: The image is in the group, should be used with the --group option of c2cciutils-publish script. Default: `"default"`.
          - **`path`** _(string)_: The path of the pypi package.
          - **`build_command`** _(array)_: The command used to do the build.
            - **Items** _(string)_
      - **`versions`** _(array)_: The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script.
        - **Items** _(string)_
    -
- <a id="definitions/publish_helm"></a>**`publish_helm`**: Configuration to publish Helm charts on GitHub release.
  - **One of**
    - _object_: Configuration to publish on Helm charts on GitHub release.
      - **`folders`** _(array)_: The folders that will be published.
        - **Items** _(string)_
      - **`versions`** _(array)_: The kind or version that should be published, tag, branch or value of the --version argument of the c2cciutils-publish script.
        - **Items** _(string)_
    -
- <a id="definitions/print_versions"></a>**`print_versions`** _(object)_: The print versions configuration.
  - **`versions`** _(array)_
    - **Items** _(object)_
      - **`cmd`** _(array)_: The command that should be used.
        - **Items** _(string)_
      - **`name`** _(string)_: The name.
      - **`prefix`** _(string)_: Prefix added when we print the version.
- <a id="definitions/version_transform"></a>**`version_transform`** _(array)_: A version transformer definition.
  - **Items** _(object)_
    - **`from`** _(string)_: The from regular expression.
    - **`to`** _(string)_: The expand regular expression: https://docs.python.org/3/library/re.html#re.Match.expand.