#!/usr/bin/env python3

import argparse
import json
import subprocess  # nosec
import sys
import time
from typing import Any


def _check_deployment_status(deployments: Any) -> bool:
    for deployment in deployments["items"]:
        if not deployment["status"]:
            print(f'Waiting status for {deployment["metadata"]["name"]}')
            return False

        for condition in deployment["status"].get("conditions", []):
            if not condition["status"]:
                print(
                    f'::group::Deployment {deployment["metadata"]["name"]} not ready: {condition["message"]}'
                )
                print(json.dumps(condition, indent=4))
                print("::endgroup::")
                return False

        if deployment["status"].get("unavailableReplicas", 0) != 0:
            print(
                f'::group::Deployment {deployment["metadata"]["name"]} not ready there is {deployment["status"].get("unavailableReplicas", 0)} '
                "unavailable replicas"
            )
            print(json.dumps(deployment["status"], indent=4))
            print("::endgroup::")
            return False

    return True


def _check_container_status(pod: Any, status: Any, is_init: bool = False) -> bool:
    del is_init
    good = status["ready"]

    if not good:
        waiting = status["state"].get("waiting")
        terminated = status["state"].get("terminated")
        state = waiting if waiting else terminated
        status_message = state.get("message", state.get("reason", "")) if state else ""
        if not status_message:
            state = status.get("lastState", {}).get("terminated", {})
            status_message = state.get("message", state.get("reason", "")) if state else ""
        status_message_long = status_message.strip()
        if "message" in status.get("lastState", {}).get("terminated", {}):
            status_message_long = status["lastState"]["terminated"]["message"]
        status_message = status_message.split("\n")[0]
        status_message = status_message.strip()
        if status_message == "Completed":
            return True
        print(f'::group::Container not ready in {pod["metadata"]["name"]}: {status_message}')
        if status_message_long != status_message:
            print(status_message_long)
        print(json.dumps(status, indent=4))
        print("::endgroup::")
        return False
    return True


def _check_pod_status(pods: Any) -> bool:
    for pod in pods["items"]:
        for condition in pod["status"].get("conditions", []):
            if not condition["status"]:
                print(
                    f'::group::Pod not ready in {pod["metadata"]["name"]}: {condition.get("message", condition["type"])}'
                )
                print(json.dumps(condition, indent=4))
                print("::endgroup::")
                return False

        for status in pod["status"].get("initContainerStatuses", []):
            if not _check_container_status(pod, status, True):
                return False
        for status in pod["status"].get("containerStatuses", []):
            if not _check_container_status(pod, status):
                return False

    return True


def main() -> None:
    """Wait that the k8s application is ready."""
    parser = argparse.ArgumentParser(description="Get some logs to from k8s.")
    parser.add_argument("--namespace", help="Namespace to be used")
    parser.add_argument(
        "-l",
        "--selector",
        default="",
        help="Selector (label query) to filter on, supports '=', '==', and '!='.(e.g. -l key1=value1,key2=value2)",
    )
    parser.add_argument("--no-deployments", dest="deployments", action="store_false")

    args = parser.parse_args()

    if args.namespace:
        subprocess.run(["kubectl", "config", "set-context", "--current", "--namespace=default"], check=True)

    for _ in range(20):
        time.sleep(10)
        success = True
        deployements_names = []
        if args.deployments:
            deployments = subprocess.run(
                ["kubectl", "get", "deployments", "--output=json"],
                stdout=subprocess.PIPE,
                check=True,
            )
            deployements_json = json.loads(deployments.stdout)
            success &= _check_deployment_status(deployements_json)
            deployements_names = [
                deployment["metadata"]["name"] for deployment in json.loads(deployments.stdout)["items"]
            ]

        pods = subprocess.run(
            ["kubectl", "get", "pods", "--output=json", f"--selector={args.selector}"],
            stdout=subprocess.PIPE,
            check=True,
        )
        pods_json = json.loads(pods.stdout)
        success &= _check_pod_status(pods_json)
        pods_name = [p["metadata"]["name"] for p in json.loads(pods.stdout)["items"]]
        if success:
            if deployements_names:
                print()
                print("Deployments ready:")
                print("\n".join(deployements_names))
            print()
            print("Pods ready:")
            print("\n".join(pods_name))
            sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
