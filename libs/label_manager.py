#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/2 11:23
# @Author  : ysy
# @Site    : 标签管理
# @File    : label_manager.py
# @Software: PyCharm
import os
import codecs
import re
from collections import OrderedDict
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *


# 本地保存xml的name关键字
_KEY = "key"
# 本地保存值得关键之
VALUE_FLAG = "value"
# name和特殊值之间的间隔符
INTER_FLAG = ":"


def _parse_line(line: str):
    """
    行解析，逗号隔开，目前支持3个字段，第一个是展示的名称，第二个是xml中保存的名称，第三个是附带值value的正则标的形式
    :param line:
    :return:
    """
    line = line.strip()
    config = line.split(",")
    if len(config) == 2:
        return config[0], config[1], ""
    elif len(config) == 3:
        return config[0] + INTER_FLAG, config[1], config[2]
    elif len(config) == 1:
        return config[0], config[0], ""
    else:
        raise Exception("配置{}错误".format(line))


def _load_file(file_name):
    """
    从文件中加载标签列表映射
    :return:
    """
    flag = OrderedDict()
    # 属性设置文件
    with codecs.open(file_name, 'r', 'utf8') as f:
        for line in f:
            k, v, value = _parse_line(line)
            if not k:
                raise Exception("文件中{}配置{}非法".format(file_name, line))

            if k in flag.keys():
                raise Exception("文件中{}中存在重复的关键配置项：{}".format(file_name, k))
            flag[k] = {
                _KEY: v,
                VALUE_FLAG: value
            }

    return flag


class LabelManager:
    def __init__(self, predefClassesFile):
        """
        初始化，加载标签文件，主要传递predefined_classes.txt文件路径
        :param predefClassesFile:
        """
        if not os.path.exists(predefClassesFile):
            raise Exception("标签分类文件{}不存在".format(predefClassesFile))

        self.predefine_class_file = predefClassesFile
        # 属性文件
        self.attr_file = os.path.join(os.path.split(predefClassesFile)[0], "predefined_attr.txt")
        if not os.path.exists(self.attr_file):
            raise Exception("属性文件{}不存在".format(self.attr_file))

        # 属性标记字典
        self._attr_dict = _load_file(self.attr_file)
        # 标注框标记字典
        self._bbox_dict = _load_file(self.predefine_class_file)

        # 属性记录
        self.attr_flag = {}
        # 标注框记录
        self.bbox_flag = []

    def clear(self):
        self.attr_flag = {}
        self.bbox_flag = []

    @property
    def attr_key_list(self):
        """
        属性key的列表
        :return:
        """
        return [values.get(_KEY) for values in self._attr_dict.values() if values and isinstance(values, dict)]

    @property
    def label_view_list(self):
        """
        可视化标签列表，例如管帽正常、管帽丢失、[成像污染]等等，包括属性设置以及标注框框设置等等
        :return:
        """
        return list(self._attr_dict.keys()) + list(self._bbox_dict.keys())

    def _get_bbox_key_and_value(self, label: str):
        """
        根据标签获取name和value
        :param label:
        :return:
        """
        # 包含了标签和标记值
        if INTER_FLAG in label:
            labels = label.split(INTER_FLAG)
            name = labels[0] + INTER_FLAG
            value_regex = self._bbox_dict.get(name, {}).get(VALUE_FLAG)
            # 正则条件判断
            if value_regex and not re.search(value_regex, labels[1]):
                raise Exception("标签{}不满足正则配置约束{}".format(label, value_regex))

            value = labels[1]
            if not value:
                raise Exception("标签{}需要赋值，不能为空".format(label))
        else:
            name = label
            value = ""
        name = self._bbox_dict.get(name, {}).get(_KEY)
        if not name:
            raise Exception("标签{}没有配置到配置文件中".format(label))
        return name, value

    def get_attr_name(self, key):
        """
        通过xml的name映射到界面上展示的key
        :param key:
        :return:
        """
        for name, values in self._attr_dict.items():
            if isinstance(values, dict) and values.get(_KEY) == key:
                return name

        raise Exception("没有配置关键字{}".format(key))

    def get_bbox_name(self, key):
        """
        通过xml的name映射到界面上展示的key
        :param key:
        :return:
        """
        for name, values in self._bbox_dict.items():
            if isinstance(values, dict) and values.get(_KEY) == key:
                return name

        raise Exception("没有配置关键字{}".format(key))

    def set_attr(self, xmin, ymin, xmax, ymax, label):
        """
        设置属性
        :param xmin:
        :param ymin:
        :param xmax:
        :param ymax:
        :param label:
        :return:
        """
        name, value = self._get_bbox_key_and_value(label)
        self.attr_flag[name] = dict(xmin=xmin, ymin=ymin, xmax=xmax, ymax=ymax)

    def add_bbox(self, xmin, ymin, xmax, ymax, label, difficult):
        bndbox = {'xmin': xmin, 'ymin': ymin, 'xmax': xmax, 'ymax': ymax}
        label, value = self._get_bbox_key_and_value(label)
        bndbox['name'] = label or label
        bndbox['difficult'] = difficult
        if value:
            bndbox["value"] = value

        self.bbox_flag.append(bndbox)
