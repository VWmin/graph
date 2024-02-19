#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from ryu.cmd import manager


def main():
    sys.argv.append('/home/fwy/Desktop/graph/experimental/multipath.py')
    # sys.argv.append('/usr/local/lib/python3.10/dist-packages/ryu/app/simple_switch_igmp_13.py')
    # sys.argv.append('--verbose')
    sys.argv.append('--enable-debugger')
    sys.argv.append('--observe-links')
    manager.main()


if __name__ == '__main__':
    main()
