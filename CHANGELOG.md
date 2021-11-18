# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/) and this
project adheres to [Semantic Versioning](https://semver.org/).

# 1.0.0 - 2021-11-18

## Added

- Automated integration tests
- Statement summary and dxplanation of variables in `Syntax` documentation

## Fixed

## Changed

- Upgraded Python build/test system
- Switched to `argparse`

# 0.3.2 - 2021-01-30

## Added

## Fixed

- Variables were superglobal (global over all zones), instead of local

## Changed

# 0.3.1 - 2021-01-30

## Added

## Fixed

- `$DEFAULT` wrongly overwrote variables

## Changed

# 0.3.0 - 2021-01-22

## Added

- Automatically maintain a catalog file
- `./dnstemple.py` to simplify testing the current version
- Will output the domains which were changed, to simplify zone reloads
- Option to skip outputting empty and/or comment lines (_starting_ with `;`)
- Allow a constant number as the serial number in `config.serial`
- If catalog is changed, output its name first, so that it the name server will
  learn about potential new domains first

## Fixed

## Changed

- Default for serial number generation is now `unixtime`. Is much faster than
  `online`. Recommended for use with [Knot DNS](https://knot-dns.cz) option
  `zonefile-load: difference-no-serial`.
- No more variable expansion in comment lines (referring to a changing variable
  such as `_serial` in the comments no longer results in the file considered to
  have changed)
- Comment lines no longer reset the expectation for a label (to avoid wrong
  assumptions, after e.g. `$INCLUDE`, a warning is issued, if the first resource
  record does not have an explicit label)
- Warnings go to stderr so that only changed domain names go to stdout

# 0.2.0 - 2021-01-21

## Added

- Support for `$DEFAULT` directive for setting a default value for a variable.
  (The use of more shell-like substitutions like `{variable:-value}` was
  discarded, as it would have required a variable substitution parser.)

## Fixed

- Install `dnspython` as well when using `pip`.

## Changed

# 0.1.0 - 2020-12-20

## Added

- First version

## Fixed

## Changed
