#!/usr/bin/env python

import os
import sys

try:
    import pinax
except ImportError:
    sys.stderr.write("Error: Can't import Pinax. Make sure you are in a virtual environment that has\nPinax installed or create one with pinax-boot.py.\n")
    sys.exit(1)

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
    from settings import PROJECT_ROOT
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
