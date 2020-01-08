# encoding=utf-8

import re
import random


def list_remake(l):
    """
    将多维数据转化为一维数组
    :param l: list
    :return: list/返回一维数组
    """
    if type(l) == list:
        result = []
        for i in l:
            result += list_remake(i)
        return result
    else:
        return [l]


def sql_split(sql, is_comma_trans=False, space_num=2):
    """
    用于分割sql，返回list
    :param sql: string/待处理sql
    :param is_comma_trans: int/逗号是否前置
    :param space_num: int/关键字后空格个数
    :return: list
    """
    # 分割sql, 结尾加\s 防止将非关键字给分割了 例如pdw_fact_person_insure中的on
    # 20190326 wq 在关键字前后增加\s，防止将非关键字给分割了，例如sql_from中的from

    split_sql = re.findall(r'(((^(\s*--\s*[^\s]*)+|with.*?\(|\w+\sas\s*\()|'
                           r'(select|from|((left|right|full|inner|cross)\s(outer\s)?)?join|'
                           r'on|where|group|order|limit|having|union(\sall)?|insert|create|lateral\sview))'
                           r'.*?'
                           r'\s(?=(with.*?\(|\w+\sas\s*\()|'
                           r'(select|from|((left|right|full|inner|cross)\s(outer\s)?)?join\(?|'
                           r'on|where|group|order|limit|having|union(\sall)?|insert|create|lateral\sview)\s|$))', sql)
    split_sql_list = [split_sql_value[0].lstrip() for split_sql_value in split_sql]
    # 20190319 wq 消除窗口函数中order等字段中含关键字的影响,将select到from或select到union或select整合在一起
    split_sql_list_pos = 0
    while split_sql_list_pos < len(split_sql_list)-1 and len(split_sql_list) > 1:
        if not re.search('^(from|select|union) ', split_sql_list[split_sql_list_pos+1])\
                and split_sql_list[split_sql_list_pos].count('(') > split_sql_list[split_sql_list_pos].count(')'):
            split_sql_list[split_sql_list_pos] = split_sql_list[split_sql_list_pos].strip() + ' ' + \
                                                 split_sql_list[split_sql_list_pos+1]
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
                exec_sql = list_remake(exec_sql)
                tmp = exec_sql[0]
        else:
            exec_sql = [split_sql_value]
        # 分割 sql中的‘字段’和‘逻辑判断条件’；并根据关键字添加空格
        for exec_sql_pos in range(len(exec_sql)):
            exec_sql_value = exec_sql[exec_sql_pos].strip()
            first_value = re.match(r'\s*(--|\w+|\))\s?', exec_sql_value).group(1)
            if first_value in ('select', 'group', 'order'):
                # 分割字段，根据','分割出所有字段
                tmp_sql = [i[0].strip() for i in re.findall(r'(.*?(,(\s*--\s*[^\s]*)?|$))', exec_sql_value)]
                tmp = []
                # 20190319 wq 合并函数中的括号和中括号
                for tmp_sql_pos in range(len(tmp_sql)):
                    if tmp_sql_pos > 0 and (tmp_sql[tmp_sql_pos-1].count('(') != tmp_sql[tmp_sql_pos-1].count(')')
                                            or tmp_sql[tmp_sql_pos-1].count('[') != tmp_sql[tmp_sql_pos-1].count(']')):
                        tmp_sql[tmp_sql_pos] = tmp_sql[tmp_sql_pos-1] + ' ' + tmp_sql[tmp_sql_pos]
                        # 跳过上次括号不齐，留到下次合并处理
                        if tmp_sql[tmp_sql_pos].count('(') == tmp_sql[tmp_sql_pos].count(')') \
                                and tmp_sql[tmp_sql_pos].count('[') == tmp_sql[tmp_sql_pos].count(']'):
                            tmp.append(tmp_sql[tmp_sql_pos])
                    elif tmp_sql[tmp_sql_pos].count('(') == tmp_sql[tmp_sql_pos].count(')') \
                            and tmp_sql[tmp_sql_pos].count('[') == tmp_sql[tmp_sql_pos].count(']'):
                        tmp.append(tmp_sql[tmp_sql_pos])
                    else:
                        pass
                # 添加字段前空格
                for tmp_pos in range(len(tmp)):
                    # 20190321 wq 修复逗号前置和字段中含注释所导致的错误（逗号被注释掉）
                    if re.search(r'[^,]+--z\d+s,$', tmp[tmp_pos]) is not None:
                        tmp[tmp_pos] = re.sub(',$', '', re.sub(r'(?<=[^,])\s*--', ', --', tmp[tmp_pos], 1))
                    if tmp_pos == 0:
                        if is_comma_trans is True:
                            tmp[tmp_pos] = re.sub(r',(?=\s*(--z\d+s)?$)', '', tmp[tmp_pos])
                        tmp[tmp_pos] = re.sub(r'^\s*(\w*)\s*', first_value.rjust(6) + space_num * " ", tmp[tmp_pos])
                    else:
                        if is_comma_trans is True and tmp[tmp_pos] != '':
                            tmp[tmp_pos] = ',' + re.sub(r',(?=\s*(--z\d+s)?$)', '', tmp[tmp_pos])
                        tmp[tmp_pos] = (6 + space_num) * " " + tmp[tmp_pos]
                    # case when 特别处理
                    """
                    20200108 when/else/end 不换行规则
                    1.else与end之间只相隔10个字符，end不换行
                    2.只有when与end，end不换行
                    3.end后面没有空格即直接接逗号，end不换行
                    4.只有一个when，且else与end之间只相隔10个字符，else和end不换行
                    """
                    if re.search(',?case', tmp[tmp_pos]):
                        tmp_case = [i[0] for i in re.findall(r'((.*?(,?case\s)?when|else\s.{10,}(?=\send)|'
                                                             r' else\s.{0,10} end|end).*?(?=\s(when|else|end)\s|$))',
                                                             tmp[tmp_pos])]
                        if len(tmp_case) < 2:
                            pass
                        elif len(tmp_case) == 2 and re.search(r'^\s*else.*end\W', tmp_case[1]):
                            tmp[tmp_pos] = tmp_case[0] + ' ' + tmp_case[1].strip()
                        else:
                            case_pos = 0
                            for tmp_case_pos in range(len(tmp_case)):
                                if tmp_case_pos == 0:
                                    case_pos = tmp_case[tmp_case_pos].find('when')
                                elif re.match('^end', tmp_case[tmp_case_pos]):
                                    tmp_case[tmp_case_pos] = (case_pos + 1) * ' ' + tmp_case[tmp_case_pos].strip()
                                else:
                                    tmp_case[tmp_case_pos] = case_pos * ' ' + tmp_case[tmp_case_pos].strip()
                            tmp[tmp_pos] = tmp_case
                    else:
                        pass
                exec_sql[exec_sql_pos] = tmp
            elif first_value in ('on', 'where', 'having'):
                tmp = [i[0] for i in re.findall(r'(\s*(where|on|having|and|or)\s.*?(?=\s(and|or|on|where|having)\s|$))',
                                                exec_sql_value)]
                bracket_num = 0
                for tmp_pos in range(len(tmp)):
                    first_value_2 = re.match(r'^\s*(\w*)\s*', tmp[tmp_pos]).group(1)
                    if bracket_num > 0 or space_num == 1:
                        bool_num = 1
                    else:
                        bool_num = 2
                    tmp[tmp_pos] = re.sub(r'^\s*(\w*)\s*', first_value_2.rjust(6 + space_num - bool_num)
                                          + bool_num * " ", tmp[tmp_pos])
                    tmp[tmp_pos] = bracket_num * '    ' + tmp[tmp_pos]
                    bracket_num = bracket_num + tmp[tmp_pos].count('(') - tmp[tmp_pos].count(')')
                exec_sql[exec_sql_pos] = tmp
            # 20190423 wq 兼容hive关键字：lateral view
            elif first_value == 'lateral':
                exec_sql[exec_sql_pos] = re.sub(r'^\s*(\w*)\s*', 'lateral ', exec_sql[exec_sql_pos])
            else:
                if first_value != ')':
                    if re.search(r'^\w+ as \($', exec_sql[exec_sql_pos]):
                        exec_sql[exec_sql_pos] = (6 + space_num) * " " + exec_sql[exec_sql_pos]
                    else:
                        exec_sql[exec_sql_pos] = re.sub(r'^\s*(--|\w*)\s*', first_value.rjust(6) + space_num * " ",
                                                        re.sub(r'\s*\(', ' (', exec_sql[exec_sql_pos]))
                else:
                    # exec_sql[exec_sql_pos] = (6 + space_num) * " " + exec_sql[exec_sql_pos]
                    pass
        split_sql_list[split_sql_pos] = exec_sql
    return list_remake(split_sql_list)


def sql_format(sql, is_comma_trans=False, space_num=2):
    """
    将list整合成str，并处理空白字符
    :param sql:string/待处理sql
    :param is_comma_trans: bool/逗号是否前置
    :param space_num: int/关键字后空格个数
    :return: list/处理后的sql及当中所涉及到的表
    """
    level = 0
    result_sql = ''
    # 20190316 wq 修复注释问题，先将注释内容取出,映射到一个随机数，等处理完后最后映射回来
    sql = sql + '\n'
    notes = list(set([i[0] for i in re.findall(r'(\s*(--.*?(?=\r?\n)|/\*(.|\n)*?\*/))', sql)]))
    notes_encode = ['z' + str(random.randint(1000000, 10000000)) + 's' for i in notes]
    for note_pos in range(len(notes)):
        sql = sql.replace(notes[note_pos], '--' + notes_encode[note_pos])
    # 20190924 wq 引用符中的内容 处理【引用涉及字段引用，因此与注释分开去处理】
    quotes = list(set([i[0] for i in re.findall(r'((\'|`|\")(.|\n)*?(\'|`|\"))', sql)]))
    quotes_encode = ['y' + str(random.randint(1000000, 10000000)) + 'y' for i in quotes]
    for quote_pos in range(len(quotes)):
        sql = sql.replace(quotes[quote_pos], quotes_encode[quote_pos])
    # 统一空白符
    sql = ' ' + re.sub(r'\s+', ' ', sql).strip() + ' '
    tmp_sql = sql.lower()
    for pattern_atom in [r'\[', r'\(', r'\]', ',', r'\)', r'\+', '-', r'\*', '/', '=', '<', '>', '!']:
        pattern = '[ ]*{0}[ ]*'.format(pattern_atom)
        if pattern_atom in (r'\[', r'\('):
            repl_str = re.sub(r'\\', '', pattern_atom)
            pattern = r'(?<=(\w|\(|\[|\)|\]))' + pattern
        elif pattern_atom in [r'\]', r'\)', r',']:
            repl_str = re.sub(r'\\', '', pattern_atom) + ' '
            pattern = r'(?<=(\w|\(|\[|\)|\]))' + pattern
        elif pattern_atom in [r'\+', r'\*', '/', '=', '<', '>', '!']:
            repl_str = ' ' + re.sub(r'\\', '', pattern_atom) + ' '
        elif pattern_atom == '-':
            pattern = '[ ]*(?<!-)-(?!-)[ ]*'
            repl_str = ' - '
        else:
            pass
        tmp_sql = re.sub(pattern, repl_str, tmp_sql)
    # 20190321 wq 优化符号的处理，例如"100 * -1"
    tmp_sql = re.sub(r'(?<=\[|\]|,|\(|\))\s*(?=\[|\]|,|\(|\))', '', tmp_sql)
    tmp_sql = re.sub(r'(?<=!|=|<|>)\s*(?=!|=|<|>)', '', tmp_sql)
    # 字段中符号开头
    tmp_sql = re.sub(r'(?<=,\s(\+|-))\s*(?!-)', '', tmp_sql)
    tmp_sql = re.sub(r'(?<=(\+|-|\*|/|=|<|>)\s(\+|-))\s*', '', tmp_sql)
    # 20190326 wq 修复子查询的问题
    tmp_sql = tmp_sql.replace('(--', '( --').replace('(select ', '( select ')
    # 20190312 wq 关键字后直接接左括号
    tmp_sql = re.sub(r'((?<=\Wselect)|(?<=\Wfrom)|(?<=\Wjoin)|(?<=\Won)|(?<=\Wover)|(?<=\Wand)|(?<=\Wor)|'
                     r'(?<=\Wwhere)|(?<=\Wby)|(?<=\Whaving)|(?<=\Was)|(?<=\Win))\(', ' (', tmp_sql)
    # 按括号添加前缀空格
    split_sql = sql_split(tmp_sql, is_comma_trans, space_num)
    table_list = []
    custom_table_list = []
    # 20190328 wq 获取from后的表，再与with/as的自定义表名对比，剔除
    # 20190402 wq 1.获取表名：增加join的判断
    for split_sql_value in split_sql:
        if re.match(r'^\s*(from|((left|right|full|inner|cross)\s+(outer\s+)?)?join)\s+[^\(]+$', split_sql_value):
            table_list.append(re.search(r'(from|join)\s+(.+?)(?=--|\s|$)', split_sql_value).group(2))
        elif re.match(r'^\s*\swith.*?\(|[^,]*as\s*\(', split_sql_value):
            custom_table_list.append(re.search(r'((?<=with)\s+[^\s]+|[^\s]+(?=\s+as))', split_sql_value).group(1).strip())
        else:
            pass
        if re.match(r'^\s*$', split_sql_value):
            continue
        result_sql = result_sql + level * 8 * " " + split_sql_value + "\r\n"
        if re.search(r'\((\s*--\s*[^\s]*)?\s*$', split_sql_value):
            level += 1
        elif re.search(r'^\s*\)\s*.*?,?\s*$', split_sql_value):
            level -= 1
        else:
            pass
    # 20190423 wq 函数内注释修复：强制插入换行
    for note_pos in range(len(notes_encode)):
        if re.search(notes_encode[note_pos] + "\r?\n", result_sql) is not None:
            pass
        else:
            # 20190827 wq 修复字段内的注释
            if re.search(r'( {6,}.*?)\(.*?--' + notes_encode[note_pos], result_sql) is not None:
                space = ' ' * len(re.search(r'( {6,}.*?)\(.*?--' + notes_encode[note_pos], result_sql).group(1))
            else:
                space = ''
            notes[note_pos] = notes[note_pos] + "\r\n" + space
    for note_pos in range(len(notes_encode)):
        result_sql = re.sub(r'\s*--\s*' + notes_encode[note_pos], notes[note_pos], result_sql)
    for quotes_pos in range(len(quotes_encode)):
        result_sql = result_sql.replace(quotes_encode[quotes_pos], quotes[quotes_pos])

    # 20190404 wq 去掉重复表名
    custom_table_list = list(set(custom_table_list))
    table_list = list(set(table_list))
    for custom_table in custom_table_list:
        if custom_table in table_list:
            table_list.remove(custom_table)
    return [result_sql, table_list]


if __name__ == '__main__':
    exec_sql = [
        """
select case when coalesce(from_object, '') not in ('icon', '') then from_object else from_resourceid end as from_content, count(1) from pdw.fact_stock_em_web_log 
where hp_stat_date >= '2019-11-01' and hp_stat_date <= '2019-11-28' and objects rlike '^(ssbb|neican)_\\d+$' and user_id <> 0 group by 1
        """
    ]
    for exec_sql_vaule in exec_sql:
        # print(exec_sql_vaule)
        # print("------------------------无情分割线-----------------------")
        format_sql = sql_format(exec_sql_vaule, False, 1)
        print(format_sql[0])
        print(format_sql[1])
