#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2025/12/21 15:47
# @Author  : Kevin Chang
# @File    : main.py
# @Software: PyCharm
def launch(side):
    if side == 'server':
        from server import run
        run()
    elif side == 'client':
        from client import run
        run()
    else:
        print('Invalid side')


if __name__ == '__main__':
    launch(input('server or client? >>'))
