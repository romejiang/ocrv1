#!/usr/bin/env python3
"""Ubuntu 服务器兼容性检查"""

import sys
import platform


def check_ubuntu_compat():
    """检查 Ubuntu 兼容性"""
    issues = []

    if platform.system() != "Linux":
        print(f"注意: 当前系统 {platform.system()}，Ubuntu 验证需在服务器上进行")
        print("代码兼容性检查：")
    else:
        print(f"当前系统: {platform.system()} {platform.release()}")

    if sys.version_info < (3, 8):
        issues.append("Python 版本需要 >= 3.8")
    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")

    cross_platform_deps = [
        ("paddle", "paddlepaddle"),
        ("paddleocr", "paddleocr"),
        ("cv2", "opencv-python-headless"),
        ("PIL", "pillow"),
        ("numpy", "numpy"),
    ]

    for mod_name, pkg_name in cross_platform_deps:
        try:
            __import__(mod_name)
            print(f"✓ {pkg_name} 已安装 (跨平台)")
        except ImportError:
            issues.append(f"{pkg_name} 未安装")

    if platform.system() == "Linux":
        import subprocess

        try:
            result = subprocess.run(
                ["ldd", "--version"], capture_output=True, text=True
            )
            ldd_version = result.stdout.split("\n")[0]
            print(f"✓ {ldd_version}")
        except Exception as e:
            issues.append(f"无法检查 glibc 版本: {e}")

    if issues:
        print("\n问题:")
        for issue in issues:
            print(f"  ✗ {issue}")
        return False
    else:
        print("\n✓ 代码兼容性检查通过")
        print("  实际 Ubuntu 部署验证请在服务器上运行:")
        print("  1. pip install -r requirements.txt")
        print("  2. python scripts/check_env.py")
        print("  3. paddleocr install_hpi_deps cpu  # 安装 MKL-DNN")
        return True


if __name__ == "__main__":
    success = check_ubuntu_compat()
    sys.exit(0 if success else 1)
