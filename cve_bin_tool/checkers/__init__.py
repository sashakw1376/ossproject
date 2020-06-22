""" CVE Checkers """
import collections
import re

from ..util import regex_find

__all__ = [
    "Checker",
    "VendorPackagePair",
    "bash",
    "binutils",
    "bluez",
    "busybox",
    "bzip2",
    "cups",
    "curl",
    "dovecot",
    "expat",
    "ffmpeg",
    "freeradius",
    "gimp",
    "gnutls",
    "gstreamer",
    "haproxy",
    "hostapd",
    "icu",
    "kerberos",
    "libdb",
    "libgcrypt",
    "libjpeg",
    "libnss",
    "libtiff",
    "libvirt",
    "lighttpd",
    "ncurses",
    "nessus",
    "nginx",
    "node",
    "openafs",
    "openssh_client",
    "openssh_server",
    "openssl",
    "openswan",
    "openvpn",
    "png",
    "polarssl_fedora",
    "postgresql",
    "python",
    "radare2",
    "rsyslog",
    "sqlite",
    "strongswan",
    "syslogng",
    "systemd",
    "varnish",
    "wireshark",
    "xerces",
    "xml2",
    "zlib",
]

VendorPackagePair = collections.namedtuple("VendorPackagePair", ["vendor", "package"])


class CheckerMetaClass(type):
    def __init__(cls, name, bases, namespace, **kwargs):
        """
        Needed for compatibility with Python 3.5
        """
        super().__init__(name, bases, namespace)

    def __new__(cls, name, bases, props, module=None):
        # Create the class
        cls = super(CheckerMetaClass, cls).__new__(cls, name, bases, props)
        # HACK Skip validation is this class is the base class
        if name == "Checker":
            return cls
        # Validate that the checker has a module name set
        if not cls.MODULE_NAME:
            raise AssertionError("%s missing module name" % (name,))
        # Validate that we have at least one vendor package pair
        if len(cls.VENDOR_PACKAGE) < 1:
            raise AssertionError("%s needs at least one vendor package pair" % (name,))
        # Validate that each vendor package pair is of length 2
        cls.VENDOR_PACKAGE = list(
            map(lambda vpkg: VendorPackagePair(*vpkg), cls.VENDOR_PACKAGE)
        )
        # Compile regex
        cls.CONTAINS_PATTERNS = list(map(re.compile, cls.CONTAINS_PATTERNS))
        cls.VERSION_PATTERNS = list(map(re.compile, cls.VERSION_PATTERNS))
        cls.FILENAME_PATTERNS = list(map(re.compile, cls.FILENAME_PATTERNS))
        # Return the new checker class
        return cls


class Checker(metaclass=CheckerMetaClass):
    CONTAINS_PATTERNS = []
    VERSION_PATTERNS = []
    FILENAME_PATTERNS = []
    VENDOR_PACKAGE = []
    MODULE_NAME = ""

    def guess_contains(self, lines):
        for line in lines:
            if any(pattern.search(line) for pattern in self.CONTAINS_PATTERNS):
                return True
        return False

    def get_version(self, lines, filename):
        version_info = dict()

        if any(pattern.search(filename) for pattern in self.FILENAME_PATTERNS):
            version_info["is_or_contains"] = "is"

        if "is_or_contains" not in version_info and self.guess_contains(lines):
            version_info["is_or_contains"] = "contains"

        if "is_or_contains" in version_info:
            version_info["modulename"] = self.MODULE_NAME
            version_info["version"] = regex_find(lines, self.VERSION_PATTERNS)

        return version_info
