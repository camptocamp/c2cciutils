#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import c2cciutils.audit


def main() -> None:
    full_config = c2cciutils.get_config()
    config = full_config.get("audit", {})
    error = False
    for key, conf in config.items():
        if conf:
            audit = getattr(c2cciutils.audit, key)
            print("Run audit {}".format(key))
            if audit(conf, full_config) is True:
                error = True
    if error:
        sys.exit(1)


if __name__ == "__main__":
    main()
