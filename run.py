# -*- coding: utf-8 -*-
"""启动入口：

    python run.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from siheyuan_vision.ui import App  # noqa: E402


def main():
    App().run()


if __name__ == "__main__":
    main()
