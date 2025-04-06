import os
import datetime

VERSION_FILE = os.path.join(os.path.dirname(__file__), "version.txt")


def get_version():
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE) as f:
            return f.read().strip()
    return "0.0.0"


def bump_version(level="patch"):
    major, minor, patch = map(int, get_version().split('.'))
    if level == "major":
        major += 1
        minor = 0
        patch = 0
    elif level == "minor":
        minor += 1
        patch = 0
    else:  # patch
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    with open(VERSION_FILE, "w") as f:
        f.write(new_version)
    return new_version
