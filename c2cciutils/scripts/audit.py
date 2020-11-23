#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

import c2cciutils.audit


def main() -> None:
    full_config = c2cciutils.get_config()
    config = full_config.get("audit", {})
    success = True
    for key, conf in config.items():
        if conf:
            audit = getattr(c2cciutils.audit, key)
            print("Run audit {}".format(key))
            success &= audit(conf, full_config)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
