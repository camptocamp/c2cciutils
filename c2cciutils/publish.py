"""
The publishing functions.
"""

import argparse
import datetime
import glob
import os
import pickle  # nosec
import subprocess  # nosec
import sys
import tempfile
import uuid
from typing import List, Optional

import ruamel.yaml
import tomlkit
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import c2cciutils.configuration


class GoogleCalendar:
    """
    Interact with the Google Calendar API.
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self) -> None:
        """
        Initialize.
        """
        self.scopes = ["https://www.googleapis.com/auth/calendar"]  # in fact it is better to hard-code this
        self.credentials_pickle_file = os.environ.get("TMP_CREDS_FILE", f"/tmp/{uuid.uuid4()}.pickle")
        self.credentials_json_file = os.environ.get(
            "GOOGLE_CREDS_JSON_FILE", "~/google-credentials-c2cibot.json"
        )  # used to refresh the refresh_token or to initialize the credentials the first time
        self.calendar_id = os.environ.get(
            "GOOGLE_CALENDAR_ID", c2cciutils.gopass("gs/ci/google_calendar/calendarId")
        )
        self.token = os.environ.get("GOOGLE_TOKEN", c2cciutils.gopass("gs/ci/google_calendar/token"))
        self.token_uri = os.environ.get(
            "GOOGLE_TOKEN_URI", c2cciutils.gopass("gs/ci/google_calendar/token_uri")
        )
        self.refresh_token = os.environ.get(
            "GOOGLE_REFRESH_TOKEN",
            c2cciutils.gopass("gs/ci/google_calendar/refresh_token"),
        )
        self.client_id = os.environ.get(
            "GOOGLE_CLIENT_ID", c2cciutils.gopass("gs/ci/google_calendar/client_id")
        )
        self.client_secret = os.environ.get(
            "GOOGLE_CLIENT_SECRET",
            c2cciutils.gopass("gs/ci/google_calendar/client_secret"),
        )

        self.creds: Credentials = self.init_calendar_service()
        self._update_creds()
        self.service = build("calendar", "v3", credentials=self.creds)

    def init_calendar_service(self) -> Credentials:
        """
        Initialize the calendar service.
        """
        # The file token pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.credentials_pickle_file):
            with open(self.credentials_pickle_file, "rb") as token:
                creds = pickle.load(token)  # nosec
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if self.token:
                    creds = Credentials(
                        self.token,
                        refresh_token=self.refresh_token,
                        token_uri=self.token_uri,
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        scopes=self.scopes,
                    )
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_json_file, self.scopes)
                    creds = flow.run_local_server(port=0)
                    self.refresh_token = creds

            # Save the credentials for the next run
            with open(self.credentials_pickle_file, "wb") as token:
                pickle.dump(creds, token)

    def _update_creds(self) -> None:
        """
        Update the credentials.
        """
        self.client_id = self.creds.client_id
        self.client_secret = self.creds.client_secret
        self.token = self.creds.token
        self.token_uri = self.creds.token_uri
        self.refresh_token = self.creds.refresh_token

    def print_all_calendars(self) -> None:
        """
        Print all calendar events.
        """
        # list all the calendars that the user has access to.
        # used to debug credentials
        print("Getting list of calendars")
        calendars_result = self.service.calendarList().list().execute()

        calendars = calendars_result.get("items", [])

        if not calendars:
            print("No calendars found.")
        for calendar in calendars:
            summary = calendar["summary"]
            event_id = calendar["id"]
            primary = "Primary" if calendar.get("primary") else ""
            print(f"{summary}\t{event_id}\t{primary}")

    def print_latest_events(self, time_min: Optional[datetime.datetime] = None) -> None:
        """
        Print latest events.

        Arguments:
            time_min: The time to be considered.
        """
        now = datetime.datetime.utcnow()
        if not time_min:
            time_min = datetime.datetime.utcnow() - datetime.timedelta(days=30)
        events_result = (
            self.service.events()
            .list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat() + "Z",
                timeMax=now.isoformat() + "Z",
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start, event["summary"])

    def create_event(
        self,
        summary: str = f"dummy/image:{datetime.datetime.now().isoformat()}",
        description: str = "description",
    ) -> None:
        """
        Create a calendar event.

        Arguments:
            summary: The event summary
            description: The event description
        """
        now = datetime.datetime.now()
        start = now.isoformat()
        end = (now + datetime.timedelta(minutes=15)).isoformat()
        body = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start, "timeZone": "Europe/Zurich"},
            "end": {"dateTime": end, "timeZone": "Europe/Zurich"},
        }

        event_result = self.service.events().insert(calendarId=self.calendar_id, body=body).execute()
        print(f"Created event with id: {event_result['id']}")

    def _print_credentials(self) -> None:
        """
        Print the credentials.
        """
        # UNSAFE: DO NEVER PRINT CREDENTIALS IN CI ENVIRONMENT, DEBUG ONLY!!!!
        print(self.creds.to_json())

    def save_credentials_to_gopass(self) -> None:
        """
        Save the calendar credentials to gopass.
        """
        objects_to_save = {
            "gs/ci/google_calendar/calendarId": self.calendar_id,
            "gs/ci/google_calendar/token": self.token,
            "gs/ci/google_calendar/token_uri": self.token_uri,
            "gs/ci/google_calendar/refresh_token": self.refresh_token,
            "gs/ci/google_calendar/client_id": self.client_id,
            "gs/ci/google_calendar/client_secret": self.client_secret,
        }
        for key, secret in objects_to_save.items():
            assert secret is not None
            c2cciutils.gopass_put(secret, key)

    def __del__(self) -> None:
        if os.path.exists(self.credentials_pickle_file):
            os.remove(self.credentials_pickle_file)


def main_calendar() -> None:
    """
    Run the calendar main function.
    """
    parser = argparse.ArgumentParser(
        description="Interact with google API for the Docker publishing calendar"
    )
    parser.add_argument(
        "--refresh-gopass-credentials",
        action="store_true",
        help="Refresh the credentials in gopass using google API",
    )
    parser.add_argument(
        "--show-events-since",
        help="show the calendar events since a date in 'YYYY-mm-dd' format",
        type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d"),
    )
    parser.add_argument(
        "--create-test-event",
        action="store_true",
        help="Create a dummy event to check that the calendar settings are correct",
    )
    args = parser.parse_args()

    if args.show_events_since or args.refresh_gopass_credentials or args.create_test_event:
        google_calendar = GoogleCalendar()
    else:
        parser.print_help()

    if args.show_events_since:
        google_calendar.print_latest_events(args.show_events_since)

    if args.refresh_gopass_credentials:
        google_calendar.save_credentials_to_gopass()

    if args.create_test_event:
        google_calendar.create_event()


def pip(
    package: c2cciutils.configuration.PublishPypiPackage, version: str, version_type: str, publish: bool
) -> bool:
    """
    Publish to pypi.

    Arguments:
        version: The version that will be published
        version_type: Describe the kind of release we do: rebuild (specified using --type), version_tag,
                    version_branch, feature_branch, feature_tag (for pull request)
        publish: If False only check the package
        package: The package configuration
    """

    print(f"::group::{'Publishing' if publish else 'Checking'} '{package.get('path')}' to pypi")
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        env = dict(os.environ)
        env["VERSION"] = version

        cwd = os.path.abspath(package.get("path", "."))

        dist = os.path.join(cwd, "dist")
        if not os.path.exists(dist):
            os.mkdir(dist)
        if os.path.exists(os.path.join(cwd, "setup.py")):
            cmd = ["python3", "./setup.py", "egg_info", "--no-date"]
            cmd += (
                ["--tag-build=dev" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")]
                if version_type in ("version_branch", "rebuild")
                else []
            )
            cmd.append("bdist_wheel")
        else:
            if not os.path.exists(dist):
                os.mkdir(dist)
            cmd = ["pip", "wheel", "--no-deps", "--wheel-dir=dist", "."]
            if os.path.exists(os.path.join(cwd, "pyproject.toml")):
                if "build_command" not in package:
                    with open(os.path.join(cwd, "pyproject.toml"), encoding="utf-8") as project_file:
                        pyproject = tomlkit.load(project_file)
                    for requirement in pyproject.get("build-system", {}).get("requires", []):
                        requirement_split = requirement.split(">=")
                        if requirement_split[0] == "poetry-core":
                            use_poetry = True
                if use_poetry:
                    if version_type == "version_tag":
                        pyproject.get("tool", {})["poetry"]["version"] = version
                        pyproject.get("tool", {})["poetry-dynamic-versioning"]["enable"] = False
                    with open(os.path.join(cwd, "pyproject.toml"), "w", encoding="utf-8") as project_file:
                        project_file.write(tomlkit.dumps(pyproject))
                    with tempfile.TemporaryDirectory(prefix="c2cciutils-publish-venv") as venv:
                        subprocess.run(["python3", "-m", "venv", venv], check=True)
                        subprocess.run([f"{venv}/bin/pip", "install", "poetry"], check=True)
                        for requirement in pyproject.get("build-system", {}).get("requires", []):
                            print(f"Install requirement {requirement}")
                            subprocess.run([f"{venv}/bin/pip", "install", requirement], check=True)
                        subprocess.run(["poetry", "--version"], check=True)
                        subprocess.run([f"{venv}/bin/poetry", "build"], cwd=cwd, env=env, check=True)
                        cmd = []
        if cmd:
            cmd = package.get("build_command", cmd)
            subprocess.check_call(cmd, cwd=cwd, env=env)
        cmd = ["twine"]
        cmd += ["upload", "--verbose", "--disable-progress-bar"] if publish else ["check"]
        cmd += glob.glob(os.path.join(cwd, "dist/*.whl"))
        subprocess.check_call(cmd)
        print("::endgroup::")
    except subprocess.CalledProcessError as exception:
        print(f"Error: {exception}")
        print("::endgroup::")
        print("With error")
        return False
    return True


def docker(
    config: c2cciutils.configuration.PublishDockerRepository,
    name: str,
    image_config: c2cciutils.configuration.PublishDockerImage,
    tag_src: str,
    tag_dst: str,
    latest: bool,
    images_full: List[str],
) -> bool:
    """
    Publish to a Docker registry.

    config is like:
        server: # The server fqdn

    image_config is like:
        name: # The image name

    Arguments:
        config: The publishing config
        name: The repository name, just used to print messages
        image_config: The image config
        tag_src: The source tag (usually latest)
        tag_dst: The tag used for publication
        latest: Publish also the tag latest
        images_full: The list of published images (with tag), used to build the dispatch event
    """

    print(f"::group::Publishing {image_config['name']}:{tag_dst} to {name}")
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        new_images_full = []
        if "server" in config:
            subprocess.run(
                [
                    "docker",
                    "tag",
                    f"{image_config['name']}:{tag_src}",
                    f"{config['server']}/{image_config['name']}:{tag_dst}",
                ],
                check=True,
            )
            new_images_full.append(f"{config['server']}/{image_config['name']}:{tag_dst}")
            if latest:
                subprocess.run(
                    [
                        "docker",
                        "tag",
                        f"{image_config['name']}:{tag_src}",
                        f"{config['server']}/{image_config['name']}:{tag_src}",
                    ],
                    check=True,
                )
                new_images_full.append(f"{config['server']}/{image_config['name']}:{tag_src}")
        else:
            if tag_src != tag_dst:
                subprocess.run(
                    [
                        "docker",
                        "tag",
                        f"{image_config['name']}:{tag_src}",
                        f"{image_config['name']}:{tag_dst}",
                    ],
                    check=True,
                )
            new_images_full.append(f"{image_config['name']}:{tag_dst}")
            if latest and tag_src != tag_dst:
                new_images_full.append(f"{image_config['name']}:{tag_src}")

        for image in new_images_full:
            subprocess.run(["docker", "push", image], check=True)
        images_full += new_images_full

        print("::endgroup::")
    except subprocess.CalledProcessError as exception:
        print(f"Error: {exception}")
        print("::endgroup::")
        print("With error")
        return False
    return True


def helm(folder: str, version: str, owner: str, repo: str, commit_sha: str, token: str) -> bool:
    """
    Publish to pypi.

    Arguments:
        folder: The folder to be published
        version: The version that will be published
        owner: The GitHub repository owner
        repo: The GitHub repository name
        commit_sha: The sha of the current commit
        token: The GitHub token
    """

    print(f"::group::Publishing Helm chart from '{folder}' to GitHub release")
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        yaml_ = ruamel.yaml.YAML()
        with open(os.path.join(folder, "Chart.yaml"), encoding="utf-8") as open_file:
            chart = yaml_.load(open_file)
        chart["version"] = version
        with open(os.path.join(folder, "Chart.yaml"), "w", encoding="utf-8") as open_file:
            yaml_.dump(chart, open_file)
        for index, dependency in enumerate(chart.get("dependencies", [])):
            if dependency["repository"].startswith("https://"):
                subprocess.run(["helm", "repo", "add", str(index), dependency["repository"]], check=True)

        subprocess.run(["cr", "package", folder], check=True)
        subprocess.run(
            [
                "cr",
                "upload",
                f"--owner={owner}",
                f"--git-repo={repo}",
                f"--commit={commit_sha}",
                "--release-name-template={{ .Version }}",
                f"--token={token}",
            ],
            check=True,
        )
        if not os.path.exists(".cr-index"):
            os.mkdir(".cr-index")
        subprocess.run(
            [
                "cr",
                "index",
                f"--owner={owner}",
                f"--git-repo={repo}",
                f"--charts-repo=https://{owner}.github.io/{repo}",
                "--push",
                "--release-name-template={{ .Version }}",
                f"--token={token}",
            ],
            check=True,
        )
        print("::endgroup::")
    except subprocess.CalledProcessError as exception:
        print(f"Error: {exception}")
        print("::endgroup::")
        print("With error")
        return False
    return True
