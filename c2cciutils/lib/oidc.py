"""
Manage OpenID Connect (OIDC) token exchange for external services.

Inspired by
https://github.com/pypa/gh-action-pypi-publish/blob/unstable/v1/oidc-exchange.py
"""

import base64
import json
import os
import sys
from typing import NoReturn

import id as oidc_id
import requests


class _OidcError(Exception):
    pass


def _fatal(message: str) -> NoReturn:
    # HACK: GitHub Actions' annotations don't work across multiple lines naively;
    # translating `\n` into `%0A` (i.e., HTML percent-encoding) is known to work.
    # See: https://github.com/actions/toolkit/issues/193
    message = message.replace("\n", "%0A")
    print(f"::error::Trusted publishing exchange failure: {message}", file=sys.stderr)
    raise _OidcError(message)


def _debug(message: str) -> None:
    print(f"::debug::{message.title()}", file=sys.stderr)


def _render_claims(token: str) -> str:
    _, payload, _ = token.split(".", 2)

    # urlsafe_b64decode needs padding; JWT payloads don't contain any.
    payload += "=" * (4 - (len(payload) % 4))
    claims = json.loads(base64.urlsafe_b64decode(payload))

    return f"""
The claims rendered below are **for debugging purposes only**. You should **not**
use them to configure a trusted publisher unless they already match your expectations.

If a claim is not present in the claim set, then it is rendered as `MISSING`.

* `sub`: `{claims.get('sub', 'MISSING')}`
* `repository`: `{claims.get('repository', 'MISSING')}`
* `repository_owner`: `{claims.get('repository_owner', 'MISSING')}`
* `repository_owner_id`: `{claims.get('repository_owner_id', 'MISSING')}`
* `job_workflow_ref`: `{claims.get('job_workflow_ref', 'MISSING')}`
* `ref`: `{claims.get('ref')}`

See https://docs.pypi.org/trusted-publishers/troubleshooting/ for more help.
"""


def _get_token(hostname: str) -> str:
    # Indices are expected to support `https://{hostname}/_/oidc/audience`,
    # which tells OIDC exchange clients which audience to use.
    audience_resp = requests.get(f"https://{hostname}/_/oidc/audience", timeout=5)
    audience_resp.raise_for_status()

    _debug(f"selected trusted publishing exchange endpoint: https://{hostname}/_/oidc/mint-token")

    try:
        oidc_token = oidc_id.detect_credential(audience=audience_resp.json()["audience"])
    except oidc_id.IdentityError as identity_error:
        _fatal(
            f"""
OpenID Connect token retrieval failed: {identity_error}

This generally indicates a workflow configuration error, such as insufficient
permissions. Make sure that your workflow has `id-token: write` configured
at the job level, e.g.:

```yaml
permissions:
  id-token: write
```

Learn more at https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect#adding-permissions-settings.
"""
        )

    # Now we can do the actual token exchange.
    mint_token_resp = requests.post(
        f"https://{hostname}/_/oidc/mint-token",
        json={"token": oidc_token},
        timeout=5,
    )

    try:
        mint_token_payload = mint_token_resp.json()
    except requests.JSONDecodeError:
        # Token exchange failure normally produces a JSON error response, but
        # we might have hit a server error instead.
        _fatal(
            f"""
Token request failed: the index produced an unexpected
{mint_token_resp.status_code} response.

This strongly suggests a server configuration or downtime issue; wait
a few minutes and try again.

You can monitor PyPI's status here: https://status.python.org/
"""  # noqa: E702
        )

    # On failure, the JSON response includes the list of errors that
    # occurred during minting.
    if not mint_token_resp.ok:
        reasons = "\n".join(
            f'* `{error["code"]}`: {error["description"]}'
            for error in mint_token_payload["errors"]  # noqa: W604
        )

        rendered_claims = _render_claims(oidc_token)

        _fatal(
            f"""
Token request failed: the server refused the request for the following reasons:

{reasons}

This generally indicates a trusted publisher configuration error, but could
also indicate an internal error on GitHub or PyPI's part.

{rendered_claims}
"""
        )

    pypi_token = mint_token_payload.get("token")
    if not isinstance(pypi_token, str):
        _fatal(
            """
Token response error: the index gave us an invalid response.

This strongly suggests a server configuration or downtime issue; wait
a few minutes and try again.
"""
        )

    # Mask the newly minted PyPI token, so that we don't accidentally leak it in logs.
    print(f"::add-mask::{pypi_token}")

    # This final print will be captured by the subshell in `twine-upload.sh`.
    return pypi_token


def pypi_login() -> None:
    """
    Connect to PyPI using OpenID Connect and mint a token for the user.

    See Also
    - https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect
    - https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-pypi
    """
    pypirc_filename = os.path.expanduser("~/.pypirc")

    if os.path.exists(pypirc_filename):
        print(f"::info::{pypirc_filename} already exists; consider as already logged in.")  # noqa: E702
        return

    if "ACTIONS_ID_TOKEN_REQUEST_TOKEN" not in os.environ:
        print(
            """::error::Not available, you probably miss the permission `id-token: write`.
              ```
              permissions:
                id-token: write
              ```
              See also: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/about-security-hardening-with-openid-connect"""
        )
        return

    try:
        token = _get_token("pypi.org")
        with open(pypirc_filename, "w", encoding="utf-8") as pypirc_file:
            pypirc_file.write("[pypi]\n")
            pypirc_file.write("repository: https://upload.pypi.org/legacy/\n")
            pypirc_file.write("username: __token__\n")
            pypirc_file.write(f"password: {token}\n")
    except _OidcError:
        # Already visible in logs; no need to re-raise.
        return
