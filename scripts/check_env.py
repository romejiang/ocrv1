#!/usr/bin/env python3
"""验证开发环境配置"""

import sys


def check_package(name, import_name=None, version_check=None):
    try:
        mod = __import__(import_name or name)
        version = getattr(mod, "__version__", "unknown")
        if version_check and version_check not in version:
            return False, f"{name} version {version} (expected {version_check})"
        return True, f"{name} {version}"
    except ImportError as e:
        return False, f"{name} NOT FOUND: {e}"


checks = [
    check_package("paddlepaddle", "paddle", "3.2"),
    check_package("paddleocr", "paddleocr"),
    check_package("opencv", "cv2", "4."),
    check_package("pillow", "PIL"),
    check_package("numpy", "numpy"),
]

all_pass = True
for passed, msg in checks:
    status = "✓" if passed else "✗"
    print(f"{status} {msg}")
    if not passed:
        all_pass = False

sys.exit(0 if all_pass else 1)
