#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2019/12/20 9:49
# @Author  : ysy
# @Site    : 
# @File    : judge_classes.py
# @Software: PyCharm
from data.config import get_config_from_ini


# 保留关键字
reserve_key = ("name", "value", "visible")


class JudgeClassConfig:
    # 'capnormal': {'name': '管帽正常', 'cap_normal_other': '管帽_正常_其他', 'cap_normal_normal': '管帽_正常_正常'}
    _config = get_config_from_ini("judge_classes.ini")

    @staticmethod
    def get_judge_label_list(label):
        for k, v in JudgeClassConfig._config.items():
            if isinstance(v, dict) and v.get("name") == label:
                #  name 去除掉
                return [item[1] for item in v.items() if item[0] not in reserve_key]

        return []

    @staticmethod
    def get_label_list():
        label_list = []

        for k, v in JudgeClassConfig._config.items():
            if str(v.get("visible", "")).lower() == "false":
                continue

            if not isinstance(v, dict):
                continue

            name = v.get("name") or k

            # 存在value配置时，自动填补":"
            if v.get("value") is not None:
                name += ":"

            label_list.append(name)

        return label_list

    @staticmethod
    def get_name(key):
        """
        返回的可能是缺陷或者判断结果的name，如果存在value配置
        :param key:
        :return:
        """
        # 直接返回
        if key in JudgeClassConfig._config.keys():
            return JudgeClassConfig._config[key].get("name", key)

        # todo 待完善 遍历judge
        for k, v in JudgeClassConfig._config.items():
            if not isinstance(v, dict):
                continue

            if key in v.keys():
                return v[key] or key

        # 没有 key相关的配置项
        return ""

    @staticmethod
    def get_name_value(key):
        """
        返回的可能是缺陷或者判断结果的name，如果存在value配置
        :param key:
        :return:
        """
        # 直接返回
        if key in JudgeClassConfig._config.keys():
            name = JudgeClassConfig._config[key].get("name", key)
            value = JudgeClassConfig._config[key].get("value")
            return name, value

        # todo 待完善 遍历judge
        for k, v in JudgeClassConfig._config.items():
            if not isinstance(v, dict):
                continue

            if key in v.keys():
                return v[key] or key, None

        # 没有 key相关的配置项
        return "", None

    @staticmethod
    def get_key_value(label):
        for k, v in JudgeClassConfig._config.items():
            # label是英文和k相同
            if v.get("name", "") == label:
                return k, v.get("value")

        return None, None

    @staticmethod
    def get_key(label):
        """
        根据label获取key
        :param label:
        :return:
        """
        for k, v in JudgeClassConfig._config.items():
            # label是英文和k相同
            if k == label:
                return k

            if not isinstance(v, dict):
                continue

            # label是中文
            if v.get("name") == label:
                return k

            # todo 后续待优化
            # label是子属性
            for judge_key, judge_value in v.items():
                # 关键字
                if judge_key in reserve_key:
                    continue
                if judge_value == label:
                    return judge_key

        return ""


if __name__ == '__main__':
    print(JudgeClassConfig.get_label_list())
    print(JudgeClassConfig.get_judge_label_list('管帽正常'))
    print(JudgeClassConfig.get_key('管帽_正常_正常'))
    print(JudgeClassConfig.get_name('cap_missing_normal'))
    print(JudgeClassConfig.get_key_value('杆号'))


