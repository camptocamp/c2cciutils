# Applications configuration

_All the applications configuration_

## Additional Properties

- **Additional Properties** _(object)_: An application configuration.
  - **`url-pattern`** _(string)_: URL pattern, to be used for files that didn't come from GitHub release, available arguments: {version}.
  - **`type`** _(string)_: The type of file. Must be one of: `["tar"]`.
  - **`get-file-name`** _(string)_: The name of the file to get in the GitHub release.
  - **`to-file-name`** _(string)_: The name of the final tile we will create.
  - **`tar-file-name`** _(string)_
  - **`finish-commands`** _(array)_
    - **Items** _(array)_
      - **Items** _(string)_

## Definitions
