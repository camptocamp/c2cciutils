# -*- coding: utf-8 -*-
import argparse
import datetime
import glob
import os
import pickle
import subprocess
import sys
import uuid

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleCalendar:
    # pylint: disable=too-many-instance-attributes
    def __init__(self):
        self.scopes = ["https://www.googleapis.com/auth/calendar"]  # in fact it is better to hard-code this
        self.credentials_pickle_file = os.environ.get("TMP_CREDS_FILE", "/tmp/{}.pickle".format(uuid.uuid4()))
        self.credentials_json_file = os.environ.get(
            "GOOGLE_CREDS_JSON_FILE", "~/google-credentials-c2cibot.json"
        )  # used to refresh the refresh_token or to initialize the credentials the first time
        self.calendar_id = os.environ.get(
            "GOOGLE_CALENDAR_ID", self.gopass_get("gs/ci/google_calendar/calendarId")
        )
        self.token = os.environ.get("GOOGLE_TOKEN", self.gopass_get("gs/ci/google_calendar/token"))
        self.token_uri = os.environ.get(
            "GOOGLE_TOKEN_URI", self.gopass_get("gs/ci/google_calendar/token_uri")
        )
        self.refresh_token = os.environ.get(
            "GOOGLE_REFRESH_TOKEN",
            self.gopass_get("gs/ci/google_calendar/refresh_token"),
        )
        self.client_id = os.environ.get(
            "GOOGLE_CLIENT_ID", self.gopass_get("gs/ci/google_calendar/client_id")
        )
        self.client_secret = os.environ.get(
            "GOOGLE_CLIENT_SECRET",
            self.gopass_get("gs/ci/google_calendar/client_secret"),
        )

        self.init_calendar_service()

    def init_calendar_service(self):
        self.creds = None
        # The file token pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.credentials_pickle_file):
            with open(self.credentials_pickle_file, "rb") as token:
                self.creds = pickle.load(token)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if self.token:
                    self.creds = Credentials(
                        self.token,
                        refresh_token=self.refresh_token,
                        token_uri=self.token_uri,
                        client_id=self.client_id,
                        client_secret=self.client_secret,
                        scopes=self.scopes,
                    )
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.credentials_json_file, self.scopes)
                    self.creds = flow.run_local_server(port=0)
                    self.refresh_token = self.creds

            # Save the credentials for the next run
            with open(self.credentials_pickle_file, "wb") as token:
                pickle.dump(self.creds, token)
        self._update_creds()
        self.service = build("calendar", "v3", credentials=self.creds)

    def _update_creds(self):
        self.client_id = self.creds.client_id
        self.client_secret = self.creds.client_secret
        self.token = self.creds.token
        self.token_uri = self.creds.token_uri
        self.refresh_token = self.creds.refresh_token

    def print_all_calendars(self):
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
            print("%s\t%s\t%s" % (summary, event_id, primary))

    def print_latest_events(self, time_min=None):
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
        summary="dummy/image:{}".format(datetime.datetime.now().isoformat()),
        description="description",
    ):
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
        print("created event with id: {}".format(event_result["id"]))

    def _print_credentials(self):
        # UNSAFE: DO NEVER PRINT CREDENTIALS IN CI ENVIRONMENT, DEBUG ONLY!!!!
        print(self.creds.to_json())

    @staticmethod
    def gopass_get(key):
        try:
            return subprocess.check_output(["gopass", "show", key]).strip().decode()
        except subprocess.CalledProcessError:
            return None

    @staticmethod
    def gopass_put(secret, key):
        subprocess.check_output(["gopass", "insert", "--force", key], input=secret.encode())

    def save_credentials_to_gopass(self):
        objs_to_save = {
            "gs/ci/google_calendar/calendarId": self.calendar_id,
            "gs/ci/google_calendar/token": self.token,
            "gs/ci/google_calendar/token_uri": self.token_uri,
            "gs/ci/google_calendar/refresh_token": self.refresh_token,
            "gs/ci/google_calendar/client_id": self.client_id,
            "gs/ci/google_calendar/client_secret": self.client_secret,
        }
        for key, secret in objs_to_save.items():
            self.gopass_put(secret, key)

    def __del__(self):
        if os.path.exists(self.credentials_pickle_file):
            os.remove(self.credentials_pickle_file)


def main_calendar() -> None:
    parser = argparse.ArgumentParser(
        description="Interact with google API for the docker publishing calendar"
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


def pip(package, version, version_type, publish):
    """
    Publish to pypi

    version_type: Describe the kind of release we do: rebuild (specified using --type), version_tag,
                  version_branch, feature_branch, feature_tag (for pull request)
    publish: If False only check the package
    package is like:
        path: . # the root folder of the package
    """

    print("::group::{} '{}' to pypi".format("Publishing" if publish else "Checking", package.get("path")))
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        env = dict(os.environ)
        env["VERSION"] = version

        cwd = os.path.abspath(package.get("path", "."))
        cmd = ["python3", "./setup.py", "egg_info", "--no-date"]
        cmd += (
            ["--tag-build=dev" + datetime.datetime.now().strftime("%Y%m%d%H%M%S")]
            if version_type == "version_branch"
            else []
        )
        cmd.append("bdist_wheel")
        subprocess.check_call(cmd, cwd=cwd, env=env)
        cmd = ["twine"]
        cmd += ["upload", "--verbose", "--disable-progress-bar"] if publish else ["check"]
        cmd += glob.glob(os.path.join(cwd, "dist/*.whl"))
        subprocess.check_call(cmd)
        print("::endgroup::")
    except subprocess.CalledProcessError as exception:
        print("Error: {}".format(exception))
        print("::endgroup::")
        print("With error")
        return False
    return True


def docker(config, name, image_config, tag_src, tag_dst):
    """
    Publish to a docker registry

    config is like:
        server: # The server fqdn

    image_config is like:
        name: # The image name
    """

    print("::group::Publishing {}:{} to {}".format(image_config["name"], tag_dst, name))
    sys.stdout.flush()
    sys.stderr.flush()

    try:
        if "server" in config:
            subprocess.check_call(
                [
                    "docker",
                    "tag",
                    "{}:{}".format(image_config["name"], tag_src),
                    "{}/{}:{}".format(config["server"], image_config["name"], tag_dst),
                ]
            )
            subprocess.check_call(
                [
                    "docker",
                    "push",
                    "{}/{}:{}".format(config["server"], image_config["name"], tag_dst),
                ]
            )
        else:
            if tag_src != tag_dst:
                subprocess.check_call(
                    [
                        "docker",
                        "tag",
                        "{}:{}".format(image_config["name"], tag_src),
                        "{}:{}".format(image_config["name"], tag_dst),
                    ]
                )
            subprocess.check_call(
                [
                    "docker",
                    "push",
                    "{}:{}".format(image_config["name"], tag_dst),
                ]
            )
        print("::endgroup::")
    except subprocess.CalledProcessError as exception:
        print("Error: {}".format(exception))
        print("::endgroup::")
        print("With error")
        return False
    return True
