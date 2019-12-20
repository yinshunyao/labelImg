#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/19 20:34
# @Author  : ysy
# @Site    : 
# @File    : config.py
# @Software: PyCharm
import os
from configparser import ConfigParser


def get_config_from_ini(config_file_name):
    config_file = os.path.join(os.path.split(os.path.abspath(__file__))[0], config_file_name)

    config = ConfigParser()
    config.read(config_file, encoding="utf-8")

    classes = {}
    for section in config.sections():
        classes[section] = dict(config.items(section))

    return classes