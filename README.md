CVE Binary Tool
===============

[![Build Status](https://travis-ci.org/intel/cve-bin-tool.svg?branch=master)](https://travis-ci.org/intel/cve-bin-tool)

This tool scans for a number of common, vulnerable open source components
(openssl, libpng, libxml2, expat and a few others) to let you know if your
system includes common libraries with known vulnerabilities.

Usage:
`python -m cve_bin_tool.cli <flags> <path to directory>`

    Possible output levels:
    -v (verbose): print scan results as they're found
       (regular): print only final summary
    -q (quiet):   suppress all output but exit with error
                  number indicating number of files with CVE

    Other options:
    -x (extract): Autoextract compressed files

When running this script, Python 3 is preferred over Python 2.7 because it has
been more tested, but both versions should work.

This readme is intended to be a quickstart guide for using the tool.  If you
require more information, there is also a [user manual](MANUAL.md) available.

How it works
------------

This scanner looks at the strings found in binary files to see if they
match certain vulnerable versions of the following libraries and tools:

* curl
* expat
* libnss
* node.js
* openssl
* libpng
* libtiff
* xerces
* xml2
* zlib

All the checkers can be found in the checkers directory, as can the
[instructions on how to add a new checker](cve_bin_tool/checkers/README.md).
Support for new checkers can be requested via
[GitHub issues](https://github.com/intel/cve-bin-tool/issues).

Limitations
-----------

This scanner does not attempt to exploit issues or examine the code in greater
detail; it only looks for library signatures and version numbers.  As such, it
cannot tell if someone has backported fixes to a vulnerable version, and it
will not work if library or version information was intentionally obfuscated.

This tool is meant to be used as a quick-to-run, easily-automatable check in a
non-malicious environment so that developers can be made aware of old libraries
with security issues that have been compiled into their binaries.

Requirements
------------

To run the cve-bin-tool you need the following utilities:

* `file`
* `strings`

These are installed by default on many Linux systems but may need to be sought
out on other platforms

To use the auto-extractor, you may need the following utilities depending on the
type of file you need to extract.  All of them will be required to run the full
test suite:

* `ar`
* `cabextract`
* `cpio`
* `rpm2cpio`
* `tar`
* `unzip`

Most of these are installed by default on many Linux systems, but `cabextract` and
`rpm2cpio` in particular might need to be installed.

Feedback & Contributions
------------------------

Bugs and feature requests can be made via [GitHub
issues](https://github.com/intel/cve-bin-tool).  Be aware that these issues are
not private, so take care when providing output to make sure you are not
disclosing security issues in other products.

Pull requests are also welcome via git.

Security Issues
---------------

Security issues with the tool itself can be reported to Intel's security
incident response team via
[https://intel.com/security](https://intel.com/security).

If in the course of using this tool you discover a security issue with someone
else's code, please disclose responsibly to the appropriate party.

