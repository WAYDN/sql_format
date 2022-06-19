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
- set_info.ini<!--设置信息-->
- sql_format.ico
- version_info.txt
- \_\_init\_\_.py

#### 迭代计划
- [ ] 增加搜索替换功能（包含右键调起），增加sql文件保存功能，临时代码自动保存临时文件
- [ ] 增加建表自动格式化sql

#### 版本迭代信息
- 2.2
<br>20220619 wq 1.重置版本号 2.修复无注释内容的注释带来的注释错误 3.无页卡情况下新建报错 (2.2.2)
<br>20220301 wq 1.修复/*+...*/ 这种特殊写法的格式及注释的位置 (2.2.1)
- 2.1
<br>20220224 wq 1.修复create...select句型的格式问题 2.select *句型的格式问题 3.union all 前增加换行 (2.1.3)
<br>20220215 wq 1.修复运算符的格式化 (2.1.2)
<br>20220106 wq 1.case when 后面跟括号的异常 2.增加结尾显示分号 (2.1.1)
- 2.0
<br>20210408 wq 增加建表功能 (2.0.4)
<br>20210303 wq 修复字段中含有create导致格式化处理失败 (2.0.3)
<br>20210112 wq 增加对建表语句的格式化 (2.0.2)
<br>20210106 wq 1.解决行数超过1000行时行数显示不全 2.增加搜索跳转功能，将搜索的内容显示在当前视图 3.搜索对话框顶层显示 (2.0.1)
- 1.3
<br>20201230 wq 1.增加文件操作功能：打开 2.修复快捷键功能 3.增加光标及选择的位置信息统计 (1.3.3)
<br>20201229 wq 增加文件操作功能：新建/保存/关闭 (1.3.2)
<br>20201224 wq 增加搜索替换功能初版 (1.3.1)
- 1.2
<br>20200714 wq 消引用符前无空格的情况 (1.2.3)
<br>20200712 wq gui代码结构重构 (1.2.2)
<br>20200430 wq 修复with...as中注释导致的格式错误 (1.2.1)
- 1.1
<br>20200318 wq 优化四则运算符的格式 (1.1.3)
<br>20200316 wq 修复with...as中的分号添加 (1.1.2)
<br>20200302 wq 修改between...and为不换行 (1.1.1)
- 1.0
<br>20200122 wq 1.修复注释中含双引号导致的错误 2.文本上 注释/运算符/引号/数字 做出颜色区分 (1.0.3)
<br>20200113 wq 兼容多段sql格式化处理 (1.0.2)
<br>20200108 wq case when 格式完善 (1.0.1)
- 0.4
<br>20191226 wq 没有配置文件则创建配置文件 (0.4.5.2)
<br>20191226 wq 新增菜单栏配置文件，记忆用户上次设置信息 (0.4.5)
<br>20191225 wq 新增关键词后保留单个空格的功能 (0.4.4)
<br>20191210 wq 回滚2.2.1中case when的改动 (0.4.3)
<br>20191210 wq 修复连续注释导致的逗号错误写入 (0.4.2)
<br>20191204 wq 1.修复重复点导致注释多次换行问题 2.调整括号内逻辑连接符的对齐位置 (0.4.1)
- 0.3
<br>20191123 wq 更改所在行的背景色/选择高亮 (0.3.4)
<br>20191123 wq 关键词提示功能升级:取消快捷键控制,改为自动提示,并在菜单栏增加提示开关选项 (0.3.3)
<br>20191118 wq 1.新增 关键词提示【快捷键：ctrl】 2.新增 括号高亮 (0.3.2)
<br>20191104 wq 1.修复菜单栏中显示控件未绑定函数 (0.3.1)
- 0.2
<br>20191029 wq 1.修复where/on/and 后置单空格 2.上次修复导致的逗号后多空一格等问题 (0.2.5)
<br>20191025 wq 增加with...as中第二个as之后的前置空格 (0.2.4)
<br>20191023 wq 1.增加返回表名的功能 2.优化多结构逻辑判断下逻辑连接符的格式 (0.2.3)
<br>20190924 wq 1.case when...end：如果只有一个when的话就不对else换行 2.引用内容保持原样 (0.2.2)
<br>20190827 wq 1.函数内注释修复导致的格式错误 2.修复union的换行 3.修复子查询中以函数结尾的分割问题 (0.2.1)
- 0.1
<br>20190423 wq 1.函数内注释修复：强制插入换行 2.兼容hive关键字：lateral view (0.1.5)
<br>20190410 wq 1.符号处理中增加'!'的处理 2.修复case when中end的空格处理 3.去掉原sql中前置逗号带来的注释结尾所带的逗号 (0.1.4)
<br>20190409 wq 1.重构逗号前置功能2.修复case中else后超10位的格式处理 (0.1.3)
<br>20190404 wq 去掉重复表名 (0.1.2)
<br>20190402 wq 获取表名：增加join的判断 (0.1.1)
- 0.0
<br>20190328 wq 1.调整格式 2.优化表名获取(剔除自定义表名) (0.0.10)
<br>20190327 wq 1.修复两类注释问题 --，/* */ (0.0.9)
<br>20190326 wq 1.修复关键字遗留问题 2.增加返回表名 3.join中含outer 4.子查询中左括号直接跟select (0.0.8)
<br>20190322 wq 1.when/else换行 2.else后跟低于10个字符 end不换行 (0.0.7)
<br>20190321 wq 1.修复逗号前置和字段中含注释所导致的错误，即逗号被注释掉 2.优化符号的处理 (0.0.6)
<br>20190320 wq 1.补充关键字 cross 2.修复注释中的多余空格 (0.0.5)
<br>20190319 wq 1.修复字段名中含关键字错误 2.符号后空格问题及中括号被分割问题 3增加逗号前置功能 4增加首行注释处理 (0.0.4)
<br>20190316 wq 1.增加对注释字段的处理 2.修改 case when...end改为同行显示 (0.0.3)
<br>20190312 wq 修复<>的处理。对 join/from等后面直接跟左括号的进一步修复 (0.0.2)
<br>20190309 wq 增加对 join/from等后面直接跟左括号的修复：1.分割sql时的无法识别 2.左括号前增加空格 (0.0.1)
