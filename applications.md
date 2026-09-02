# Applications configuration

*All the applications configuration*

## Additional Properties

- **Additional Properties** *(object)*: An application configuration.
  - **`url-pattern`** *(string)*: URL pattern, to be used for files that didn't come from GitHub release, available arguments: {version}.
  - **`type`** *(string)*: The type of file. Must be one of: `["tar"]`.
  - **`get-file-name`** *(string)*: The filename to get in the GitHub release.
  - **`to-file-name`** *(string)*: The name of the final tile name we will create.
  - **`tar-file-name`** *(string)*
  - **`finish-commands`** *(array)*
    - **Items** *(array)*
      - **Items** *(string)*
## Definitions

