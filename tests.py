#!/usr/bin/env python3
import logging
import os
import sys
import unittest

# Resolve local module
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), os.path.pardir)
)  # noqa


if __name__ == "__main__":
    logging.disable(logging.CRITICAL)  # Tests shouldn't spew logs
    unittest.main()
