# coding=utf-8


def list_remake(l):
    """
    将多维数据转化为一维数组
    :param l:
    :return: list/返回一维数组
    """
    if type(l) == list:
        result = []
        for i in l:
            result += list_remake(i)
        return result
    else:
        return [l]
# 示例
# a = [[1,2], 3, [22, 3,[54]]]
# print(list_remark(a))
