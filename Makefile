GITHUB_REPOSITORY ?= camptocamp/c2cciutils
export DOCKER_BUILDKIT = 1

.PHONY: build
build: checks
	DOCKER_BUILDKIT=1 docker build --tag=$(GITHUB_REPOSITORY) .

.PHONY: build-checker
build-checker:
	DOCKER_BUILDKIT=1 docker build --target=checker --tag=$(GITHUB_REPOSITORY)-checker .

.PHONY: checks
checks: prospector

.PHONY: prospector
prospector: build-checker
	docker run --volume=${PWD}:/app $(GITHUB_REPOSITORY)-checker prospector --ignore-paths=example-project/ --output=pylint

.PHONY: jsonschema
jsonschema:
	jsonschema-gentypes
