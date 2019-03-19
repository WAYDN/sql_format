# encoding=utf-8

"""
20190309 wq 增加对 join/from等后面直接跟左括号的修复：1.分割sql时的无法识别 2.左括号前增加空格 (1.3)
20190312 wq 修复<>的处理。对 join/from等后面直接跟左括号的进一步修复 (1.4)
20190316 wq 1.增加对注释字段的处理 2.修改 case when...end改为同行显示 (1.5)
20190319 wq 1.修复字段名中含关键字错误 2.符号后空格问题及中括号被分割问题 3增加逗号前置功能（1.6）
"""

import re
from common import common_func
import random

def sql_split(sql):
    """
    用于分割sql，返回list
    :param sql:string/待处理sql
    :return: list
    """
    # 分割sql, 结尾加\s 防止将非关键字给分割了 例如pdw_fact_person_insure中的on
    # 20190318 wq 在关键字前增加\s，防止将非关键字给分割了，例如sql_from中的from
    split_sql = re.findall(r'((^\s*--\s*[^\s]*|(with.*?\(|[^,]*as\s*\(|select|from|((left|right|full|inner)\s)?join|on|where|group|order|limit|having|union|insert|create))\s.*?(?=\s*([^,]*as\s*\(|select|from|((left|right|full|inner)\s)?join\(?|on|where|group|order|limit|having|union|insert|create)\s|$))', sql)
    split_sql_list = [split_sql_value[0].lstrip() for split_sql_value in split_sql]
    # 20190319 wq 消除窗口函数中order等字段中含关键字的影响,将select到from或select整合在一起
    split_sql_list_pos = 0
    while split_sql_list_pos < len(split_sql_list)-1 and len(split_sql_list) > 1:
        if re.search('^select', split_sql_list[split_sql_list_pos]) and not re.search('^(from|select)', split_sql_list[split_sql_list_pos+1]):
            split_sql_list[split_sql_list_pos] = split_sql_list[split_sql_list_pos] + ' ' + split_sql_list[split_sql_list_pos+1]
            split_sql_list.pop(split_sql_list_pos+1)
        else:
            split_sql_list_pos += 1
    for split_sql_pos in range(len(split_sql_list)):
        split_sql_value = split_sql_list[split_sql_pos].strip()
        # 分割 ); 如果多出一个）则分割
        exec_sql = ['']
        if split_sql_value.count('(') < split_sql_value.count(')') and split_sql_value.count(')') > 0:
            tmp = split_sql_value
            while tmp.count('(') < tmp.count(')'):
                exec_sql[0] = list(re.findall(r'^(.*)(\).*?,?)$', tmp)[0])
                exec_sql = common_func.list_remake(exec_sql)
                tmp = exec_sql[0]
        else:
            exec_sql = [split_sql_value]
        # 分割 sql中的‘字段’和‘逻辑判断条件’；并根据关键字添加空格
        for exec_sql_pos in range(len(exec_sql)):
            exec_sql_value = exec_sql[exec_sql_pos].strip()
            first_value = re.match(r'^\s*((--)?\w+|\))\s?', exec_sql_value).group(1)
            if first_value in ('select', 'group', 'order'):
                # 分割字段，根据','分割出所有字段
                tmp_sql = [i[0].strip() for i in re.findall('(.*?(,(\s*--\s*[^\s]*)?|$))', exec_sql_value)]
                tmp = []
                # 20190319 wq 合并函数中的括号和中括号
                for tmp_sql_pos in range(len(tmp_sql)):
                    if tmp_sql_pos > 0 and (tmp_sql[tmp_sql_pos-1].count('(') != tmp_sql[tmp_sql_pos-1].count(')') or tmp_sql[tmp_sql_pos-1].count('[') != tmp_sql[tmp_sql_pos-1].count(']')):
                        tmp_sql[tmp_sql_pos] = tmp_sql[tmp_sql_pos-1] + ' ' + tmp_sql[tmp_sql_pos]
                        # 跳过上次括号不齐，留到下次合并处理
                        if tmp_sql[tmp_sql_pos].count('(') == tmp_sql[tmp_sql_pos].count(')') and tmp_sql[tmp_sql_pos].count('[') == tmp_sql[tmp_sql_pos].count(']'):
                            tmp.append(tmp_sql[tmp_sql_pos])
                    elif tmp_sql[tmp_sql_pos].count('(') == tmp_sql[tmp_sql_pos].count(')') and tmp_sql[tmp_sql_pos].count('[') == tmp_sql[tmp_sql_pos].count(']'):
                        tmp.append(tmp_sql[tmp_sql_pos])
                    else:
                        pass
                # 添加字段前空格
                for tmp_pos in range(len(tmp)):
                    if tmp_pos == 0:
                        tmp[tmp_pos] = re.sub(r'^\s*(\w*)\s*', first_value.rjust(6) + 2 * " ", tmp[tmp_pos])
                    else:
                        tmp[tmp_pos] = 8 * " " + tmp[tmp_pos]
                    # case when 特别处理
                    if re.search('case', tmp[tmp_pos]):
                        tmp_case = [i[0] for i in re.findall(r'((.*?(case )?when|else.{10,}(?=end)|(else.{0,10})?end).*?(?=(when|else.{10,}|(else.{0,10})?end|$)))', tmp[tmp_pos])]
                        if len(tmp_case) > 2:
                            case_pos = 0
                            for tmp_case_pos in range(len(tmp_case)):
                                if tmp_case_pos == 0:
                                    case_pos = tmp_case[tmp_case_pos].find('when')
                                elif re.match('^end', tmp_case[tmp_case_pos]):
                                    tmp_case[tmp_case_pos] = (case_pos + 1) * ' ' + tmp_case[tmp_case_pos]
                                else:
                                    tmp_case[tmp_case_pos] = case_pos * ' ' + tmp_case[tmp_case_pos]
                            tmp[tmp_pos] = tmp_case
                        else:
                            pass
                    else:
                        pass
                exec_sql[exec_sql_pos] = tmp
            elif first_value in ('on', 'where', 'having'):
                tmp = [i[0] for i in re.findall(r'(\s*(where|on|having|and|or)\s.*?(?=\s(and|or|on|where|having)\s|$))', exec_sql_value)]
                for tmp_pos in range(len(tmp)):
                    first_value_2 = re.match(r'^\s*(\w*)\s*', tmp[tmp_pos]).group(1)
                    tmp[tmp_pos] = re.sub(r'^\s*(\w*)\s*', first_value_2.rjust(6) + 2 * " ", tmp[tmp_pos])
                exec_sql[exec_sql_pos] = tmp
            else:
                if first_value != ')':
                    exec_sql[exec_sql_pos] = re.sub('^\s*(\w*)\s*', first_value.rjust(6) + 2 * " ", re.sub('\s*\(', ' (', exec_sql[exec_sql_pos]))
                else:
                    # exec_sql[exec_sql_pos] = 8 * " " + exec_sql[exec_sql_pos]
                    pass
        split_sql_list[split_sql_pos] = exec_sql
    return common_func.list_remake(split_sql_list)


def sql_format(sql):
    """
    将list整合成str，并处理空白字符
    :param sql:string/待处理sql
    :return: str
    """
    level = 0
    result_sql = ''
    sign_list = ['-', '\+', '\*', '/', '=', '<', '>', '\[', '\]', ',', '\(', '\)']
    # 20190316 wq 修复注释问题，先将注释内容取出,映射到一个随机数，等处理完后最后映射回来
    notes = re.findall('((?<=--).*?)\r?\n', sql)
    notes_encode = ['w' + str(random.randint(1000000, 10000000)) + 'q' for i in notes]
    for note_pos in range(len(notes)):
        sql = sql.replace('--' + notes[note_pos], '--' + notes_encode[note_pos])
    sql = ' ' + re.sub('\s+', ' ', sql).strip() + ' '
    # 格式化运算符，关键字转化小写（跳过单引号内的字符串）
    tmp_sql = [i[0] for i in re.findall('((\'.*?\')|([^\']*))', sql)]
    for tmp_result_sql_pos in range(len(tmp_sql)):
        if re.search('^\'', tmp_sql[tmp_result_sql_pos]):
            pass
        else:
            tmp_sql[tmp_result_sql_pos] = tmp_sql[tmp_result_sql_pos].lower()
            for pattern_atom in sign_list:
                pattern = '[ ]*{0}[ ]*'.format(pattern_atom)
                if pattern_atom in ['-', '\+', '\*', '/', '=', '<', '>']:
                    repl_str = ' ' + re.sub(r'\\', '', pattern_atom) + ' '
                elif pattern_atom in ['\]', ',', '\)']:
                    repl_str = re.sub(r'\\', '', pattern_atom) + ' '
                elif pattern_atom in ('\[', '\('):
                    repl_str = re.sub(r'\\', '', pattern_atom)
                else:
                    pass
                tmp_sql[tmp_result_sql_pos] = re.sub(pattern, repl_str, tmp_sql[tmp_result_sql_pos])
            # 20190319 wq 优化符号间空格代码去除
            tmp_sql[tmp_result_sql_pos] = re.sub('(?<=-|\+|\*|/|=|<|>|\[|\]|,|\(|\))\s*(?=-|\+|\*|/|=|<|>|\[|\]|,|\(|\))', '',tmp_sql[tmp_result_sql_pos])
            tmp_sql[tmp_result_sql_pos] = tmp_sql[tmp_result_sql_pos].replace('(--', '( --')
    tmp_sql = ''.join(tmp_sql)
    # 20190312 wq 关键字后直接接左括号
    tmp_sql = re.sub('((?<=\sselect)|(?<=\sfrom)|(?<=\sjoin)|(?<=\son)|(?<=\swhere)|(?<=\sby)|(?<=\shaving)|(?<=\sas))\(', ' (', tmp_sql)
    # 按括号添加前缀空格
    split_sql = sql_split(tmp_sql)
    for split_sql_value in split_sql:
        if re.match(r'^\s*$', split_sql_value):
            continue
        result_sql = result_sql + level * 8 * " " + split_sql_value + "\r\n"
        if re.search('\((\s*--\s*[^\s]*)?\s*$', split_sql_value):
            level += 1
        elif re.search('^\s*\)\s*.*?,?\s*$', split_sql_value):
            level -= 1
        else:
            pass
    for note_pos in range(len(notes_encode)):
        result_sql = result_sql.replace(notes_encode[note_pos], notes[note_pos])
    return result_sql

def comma_trans(sql):
    """
    逗号前置
    :param sql:string/待处理sql
    """
    sql = re.sub('\s{4}(?!(with|as|select|from|left|right|full|inner|join|on|where|group|order|limit|having|union|insert|create|when|else|end|and|or)\s)(?=\w)', '    ,', re.sub(',(?=(\s*--\s*[^\s]*)?\r\n)', '', sql))
    return sql




# exec_sql = [
#     """
# select 123
#
#     """
# ]
# for exec_sql_vaule in exec_sql:
#     print(exec_sql_vaule)
#     print("------------------------无情分割线-----------------------")
#     format_sql = sql_format(exec_sql_vaule)
#     print(format_sql)
#     print(comma_trans(format_sql))
