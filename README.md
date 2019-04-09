# sql_format
The main thrust of this project is to standardize the SQL format.

#### 图标
![sql_format](https://github.com/WAYDN/sql_format/blob/master/sql_format.ico)

#### 开发环境
python3.6

#### 目录结构
- .gitignore
- sql_format_gui.py
- sql_format_exec.py
- sql_format.ico
- version_info.txt
- \_\_init\_\_.py


#### 版本迭代信息
- 2.1
<br>20190409 wq 1.重构逗号前置功能2.修复case中else后超10位的格式处理
- 1.13
<br>20190404 wq 去掉重复表名
<br>20190402 wq 获取表名：增加join的判断
- 1.12
<br>20190328 wq 1.调整格式 2.优化表名获取(剔除自定义表名)
- 1.11
<br>20190327 wq 1.修复两类注释问题 --，/* */
- 1.10
<br>20190326 wq 1.修复关键字遗留问题 2.增加返回表名 3.join中含outer 4.子查询中左括号直接跟select
- 1.9
<br>20190322 wq 1.when/else换行 2.else后跟低于10个字符 end不换行
- 1.8
<br>20190321 wq 1.修复逗号前置和字段中含注释所导致的错误，即逗号被注释掉 2.优化符号的处理
- 1.7
<br>20190320 wq 1.补充关键字 cross 2.修复注释中的多余空格
- 1.6
<br>20190319 wq 1.修复字段名中含关键字错误 2.符号后空格问题及中括号被分割问题 3增加逗号前置功能 4增加首行注释处理
- 1.5
<br>20190316 wq 1.增加对注释字段的处理 2.修改 case when...end改为同行显示
- 1.4
<br>20190312 wq 修复<>的处理。对 join/from等后面直接跟左括号的进一步修复
- 1.3
<br>20190309 wq 增加对 join/from等后面直接跟左括号的修复：1.分割sql时的无法识别 2.左括号前增加空格