#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from ryu.cmd import manager


def main():
    sys.argv.append('/home/fwy/anaconda3/envs/ryu-multicast/lib/python3.7/site-packages/ryu/app/simple_switch_13.py')
    sys.argv.append('--verbose')
    sys.argv.append('--enable-debugger')
    sys.argv.append('--observe-links')
    manager.main()


if __name__ == '__main__':
    main()
