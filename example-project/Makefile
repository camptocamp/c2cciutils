GITHUB_REPOSITORY ?= camptocamp/project
export DOCKER_BUILDKIT = 1

.PHONY: build
build: checks
		docker build --tag=$(GITHUB_REPOSITORY) .

.PHONY: build-checker
build-checker:
	docker build --target=checker --tag=$(GITHUB_REPOSITORY)-checker .

.PHONY: checks
checks: prospector

.PHONY: prospector
prospector: build-checker
	docker run --volume=${PWD}:/app $(GITHUB_REPOSITORY)-checker prospector
