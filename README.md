# sql_format
The main thrust of this project is to standardize the SQL format.

#### 应用介绍
SQL格式化工具，为了更优美的sql代码
```
select  a.user_id,
        a.name
  from  (
        select  user_id,
                trim(name) as name,--中文名字
                row_number() over(partition on by user_id order by time desc) as rn,
                case when 1 = 1 then end_date
                     else start_date end,
                col1
          from  db_test.test
         where  regexp_like(trim(name), '^[\u4E00-\u9FA5]+$')
        ) a
 where  rn = 1
```

#### 图标
![sql_format](https://github.com/WAYDN/sql_format/blob/master/sql_format.ico)

#### 开发环境
python3.6

#### 目录结构
- .gitignore
- sql_format_gui.py <!--GUI界面-->
- sql_format_exec.py<!--实际执行文件-->
- sql_format.ico
- version_info.txt
- \_\_init\_\_.py

#### 迭代计划
- [ ] 2.4 增加关键字/注释/函数等颜色区分
- [ ] 2.5 增加搜索替换功能（包含右键调起），增加sql文件保存功能

#### 版本迭代信息
- 2.4
<br>20191118 wq 1.新增 关键词提示【快捷键：ctrl】 2.新增 括号高亮（2.4.1）
<br>20191123 wq 关键词提示功能升级:取消快捷键控制,改为自动提示,并在菜单栏增加提示开关选项（2.4.2）
<br>20191123 wq 更改所在行的背景色/选择高亮(2.4.3)
<br>20191204 wq 1.修复重复点导致注释多次换行问题 2.调整括号内逻辑连接符的对齐位置(2.4.4)
<br>20191210 wq 修复连续注释导致的逗号错误写入 (2.4.5)
- 2.3
<br>20191023 wq 1.增加返回表名的功能 2.优化多结构逻辑判断下逻辑连接符的格式(2.3)
<br>20191025 wq 增加with...as中第二个as之后的前置空格(2.3.1)
<br>20191029 wq 1.修复where/on/and 后置单空格 2.上次修复导致的逗号后多空一格等问题（2.3.2）
<br>20191104 wq 1.修复菜单栏中显示控件未绑定函数（2.3.3）
- 2.2
<br>20190827 wq 1.函数内注释修复导致的格式错误 2.修复union的换行 3.修复子查询中以函数结尾的分割问题（2.2）
<br>20190924 wq 1.case when...end：如果只有一个when的话就不对else换行 2.引用内容保持原样(2.2.1)
- 2.1
<br>20190409 wq 1.重构逗号前置功能2.修复case中else后超10位的格式处理
<br>20190410 wq 1.符号处理中增加'!'的处理 2.修复case when中end的空格处理 3.去掉原sql中前置逗号带来的注释结尾所带的逗号（2.1.1）
<br>20190423 wq 1.函数内注释修复：强制插入换行 2.兼容hive关键字：lateral view（2.1.2）
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
