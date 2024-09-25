# coding=utf-8

import wx
import wx.stc as stc
import re
import os
import configparser
import math
import wx.grid as wg
import wx.aui as wa
import sql_format_exec


class SqlFormatPanel(wx.Panel):
    """页卡内功能"""
    def __init__(self, parent, comma_menu, table_menu, space_menu, row_menu, show_space_menu, wrap_menu, kw_tip_menu,
                 show_end_semicolon_menu):
        super(SqlFormatPanel, self).__init__(parent)
        self.last_pos = 0
        self.SetBackgroundColour('#F5F5F5')
        self.comma_menu = comma_menu
        self.table_menu = table_menu
        self.space_menu = space_menu
        self.row_menu = row_menu
        self.show_space_menu = show_space_menu
        self.wrap_menu = wrap_menu
        self.kw_tip_menu = kw_tip_menu
        self.show_end_semicolon_menu = show_end_semicolon_menu

        # 文本设置
        self.sql_text = stc.StyledTextCtrl(self, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_RICH)
        self.sql_text.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.sql_text.SetMarginWidth(1, 25)
        self.sql_text.StyleSetFontAttr(0, 10, "Consolas", False, False, False)
        self.sql_text.SetUseTabs(False)
        self.sql_text.SetViewWhiteSpace(self.show_space_menu.IsChecked())
        self.sql_text.SetWhitespaceForeground(True, 'Red')
        self.sql_text.SetWhitespaceSize(2)
        self.sql_text.SetWrapMode(self.wrap_menu.IsChecked())
        # 设置默认配色
        self.sql_text.SetLexer(stc.STC_LEX_SQL)
        # # 清空历史样式
        # sql_text.StyleClearAll()
        # 注释
        self.sql_text.StyleSetSpec(stc.STC_SQL_COMMENTLINE, "fore:#228B22")
        # 数字
        self.sql_text.StyleSetSpec(stc.STC_SQL_NUMBER, "fore:#FF8C00")
        # 双引号
        self.sql_text.StyleSetSpec(stc.STC_SQL_STRING, "fore:#CFCFCF")
        # 单引号
        self.sql_text.StyleSetSpec(stc.STC_SQL_CHARACTER, "fore:#9B30FF")
        # 运算符+标点符号
        self.sql_text.StyleSetSpec(stc.STC_SQL_OPERATOR, "fore:#1C86EE")
        # 标识符[所有其他字符]
        self.sql_text.StyleSetSpec(stc.STC_SQL_IDENTIFIER, "fore:#000000,face:Consolas")
        self.sql_text.SetCaretLineVisible(True)
        self.sql_text.SetCaretLineBackground("#F0F8FF")
        # self.sql_text.SetValue(u"""-- Ctrl+O：打开文件\n-- Ctrl+S：保存文件\n-- Ctrl+F：查询&替换\n-- Ctrl+Q：行注释""")
        self.sql_text.SetValue(u"""--Ctrl+Q：行注释
        with tmp1 (select 123 as col1),
            tmp2 (
                select 321 as col1) 
        select  a.user_id as "wq",
                a.name as `qw`
          from  (
                -- 测试数据
                select  user_id,
                        trim(name) as name,--中文名字
                        row_number() over (partition by user_id  order by apply_time desc) as rn,
                        case when 1=1 then endddd else appendas end,
                        ';' as test
                  from  test.wq_sql_format_ds
                 where  regexp_like(trim(name), '^[\u4E00-\u9FA5]+$')
                   and  (1 = 1 or 2<> 2)
                ) a
         where  rn = 1
         union all select col1, col1 from tmp1; select 123;select 12333
         """)
        # 文本动作
        self.sql_text.Bind(stc.EVT_STC_UPDATEUI, self.highlight)
        self.sql_text.Bind(wx.EVT_KEY_UP, self.keyword_tip)
        self.sql_text.Bind(wx.EVT_SET_CURSOR, self.get_pos)

        # 按钮控件
        self.button = wx.Button(self, label="格式化")
        self.button.SetWindowStyleFlag(wx.NO_BORDER)
        self.button.SetDefault()
        self.button_bc = self.button.GetBackgroundColour()
        self.button_fc = self.button.GetForegroundColour()
        # 按钮动作
        self.button.Bind(wx.EVT_ENTER_WINDOW, self.button_enter)
        self.button.Bind(wx.EVT_LEAVE_WINDOW, self.button_leave)
        self.button.Bind(wx.EVT_BUTTON, self.exec_format)

        # 位置信息
        self.pos_label = wx.StaticText(self, style=wx.ALIGN_RIGHT)

        # 布局
        self.v_box = wx.BoxSizer(wx.VERTICAL)
        self.v_box.Add(self.sql_text, proportion=1, flag=wx.EXPAND)
        self.v_box.Add(self.button, proportion=0, flag=wx.ALIGN_CENTER)
        self.SetSizer(self.v_box)

    # 光标位置/调整行数宽度
    def get_pos(self, event):
        max_line = self.sql_text.GetLineCount()
        if max_line > 999:
            self.sql_text.SetMarginWidth(1, int(math.log10(max_line)) * 10 + 5)
        else:
            self.sql_text.SetMarginWidth(1, 25)
        line_num = self.sql_text.GetCurrentLine()
        select_text = self.sql_text.GetSelectedText()
        if len(select_text) > 0:
            select_info = '{0}chars  '.format(len(select_text))
            if select_text.count('\n') > 0:
                select_info = '{0}lines '.format(select_text.count('\n') + 1) + select_info
        else:
            select_info = ''
        self.pos_label.SetLabel('{0}{1}:{2}'.format(
            select_info,
            self.sql_text.GetCurrentLine() + 1,
            self.sql_text.GetCurrentPos() - self.sql_text.GetLineEndPosition(line_num - 1)))
        self.pos_label.Position = (
            self.sql_text.GetPosition()[0] + self.sql_text.GetSize()[0] - self.pos_label.GetSize()[0],
            self.button.GetPosition()[1] + self.button.GetSize()[1] - self.pos_label.GetSize()[1])

    # 文本高亮
    def highlight(self, event):
        brace_pos = -1
        current_pos = self.sql_text.GetCurrentPos()
        # 括号高亮
        if current_pos >= 0:
            current_pos -= 1
            # BraceMatch 获取当前括号位置所对应的另一个括号位置
            brace_pos = self.sql_text.BraceMatch(current_pos)
            if chr(self.sql_text.GetCharAt(current_pos)) in list('{}[]()'):
                self.sql_text.BraceHighlight(current_pos, brace_pos)
            else:
                # 重置标色位置
                # sql_text.BraceBadLight(current_pos)
                self.sql_text.BraceHighlight(-1, -1)
        self.sql_text.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, "fore:#000000,back:#87CEFF")

        # 选择高亮
        select_context = self.sql_text.GetSelectedText()
        if re.search(r'^\w+$', select_context):
            self.sql_text.SetSelBackground(True, "#B4EEB4")
        else:
            self.sql_text.SetSelBackground(True, "#BDBDBD")

    # 关键词提示
    def keyword_tip(self, event):
        if self.kw_tip_menu.IsChecked():
            current_pos = self.sql_text.GetCurrentPos()
            sql_content = self.sql_text.GetValue().encode('utf-8')
            word_start_pos = self.sql_text.WordStartPosition(current_pos, True)
            current_str = sql_content[word_start_pos:current_pos]
            base_kw = ['select', 'from', 'left', 'right', 'full', 'inner', 'join', 'on', 'where', 'group', 'by',
                       'order', 'limit', 'having', 'union', 'all', 'insert', 'create', 'lateral', 'view', 'with', 'as']
            function_kw = ['avg', 'collect_set', 'collect_list', 'corr', 'count', 'covar_pop', 'covar_samp',
                           'histogram_numeric', 'max', 'min', 'ntile', 'percentile', 'percentile_approx', 'regr_avgx',
                           'regr_avgy', 'regr_count', 'regr_intercept', 'regr_r2', 'regr_slope', 'regr_sxx', 'regr_sxy',
                           'regr_syy', 'stddev_pop', 'stddev_samp', 'sum', 'variance', 'var_pop', 'var_samp',
                           'cume_dist', 'dense_rank', 'first_value', 'lag', 'last_value', 'lead', 'ntile',
                           'percent_rank', 'rank', 'row_number', 'array_contains', 'size', 'sort_array', 'array',
                           'create_union', 'map', 'named_struct', 'struct', 'assert_true', 'coalesce', 'if',
                           'isnotnull', 'isnull', 'nullif', 'nvl', 'add_months', 'current_timestamp', 'datediff',
                           'date_add', 'date_format', 'date_sub', 'day', 'dayofmonth', 'extract', 'from_unixtime',
                           'from_utc_timestamp', 'hour', 'last_day', 'minute', 'month', 'months_between', 'next_day',
                           'quarter', 'second', 'to_date', 'to_utc_timestamp', 'trunc', 'unix_timestamp', 'weekofyear',
                           'year', 'abs', 'acos', 'asin', 'atan', 'bin', 'bround', 'cbft', 'ceil', 'ceiling', 'conv',
                           'cos', 'degrees', 'e', 'exp', 'factorial', 'floor', 'greatest', 'hex', 'least', 'ln', 'log',
                           'log10', 'log2', 'negative', 'pi', 'pmod', 'positive', 'pow', 'power', 'radians', 'rand',
                           'round', 'shiftleft', 'shiftright', 'shiftrightunsigned', 'sign', 'sin', 'sqrt', 'tan',
                           'unhex', 'width_bucket', 'crc32', 'current_database', 'current_user', 'get_json_object',
                           'hash', 'java_method', 'logged_in_user', 'md5', 'reflect', 'sha', 'sha1', 'sha2', 'version',
                           'xpath_boolean', 'xpath_double', 'xpath_float', 'xpath_int', 'xpath_long', 'xpath_number',
                           'xpath_short', 'xpath_string', 'ascii', 'base64', 'chr', 'char_length', 'character_length',
                           'concat', 'concat_ws', 'decode', 'elt', 'encode', 'field', 'find_in_set', 'format_number',
                           'get_json_object', 'initcap', 'instr', 'in_file', 'length', 'levenshtein', 'lcase', 'locate',
                           'lower', 'lpad', 'ltrim', 'octet_length', 'parse_url', 'printf', 'regexp_extract',
                           'regexp_replace', 'repeat', 'replace', 'reverse', 'rpad', 'rtrim', 'soundex', 'space',
                           'substr', 'substring', 'substring_index', 'translate', 'trim', 'ucase', 'unbase64', 'upper',
                           'mask', 'mask_first_n', 'mask_last_n', 'mask_show_first_n', 'mask_show_last_n', 'mask_hash',
                           'explode', 'inline', 'json_tuple', 'parse_url_tuple', 'posexplode', 'stack', 'binary', 'cast'
                           ]
            tmp_kw = []
            kw = []
            tmp_kw += base_kw
            tmp_kw += function_kw
            sql_kw = re.findall(r'\w{2,}', self.sql_text.GetValue())
            tmp_kw += sql_kw
            tmp_kw = list(set(tmp_kw))
            key_code = event.GetKeyCode()
            if key_code in (wx.WXK_RETURN, wx.WXK_LEFT, wx.WXK_RIGHT, wx.WXK_UP, wx.WXK_DOWN):
                # 自动填补时清除历史字符并重新定位光标
                if key_code == 13 and word_start_pos < self.last_pos and current_str != '':
                    self.sql_text.SetValue(sql_content[:word_start_pos] + sql_content[self.last_pos:])
                    self.sql_text.GotoPos(current_pos - self.last_pos + word_start_pos)
                event.Skip()
            elif current_str != '':
                try:
                    current_str = current_str.decode('utf-8')
                except:
                    pass
                for i in tmp_kw:
                    if re.search(current_str, i) and current_str != i:
                        kw.append(i)
                kw.sort()
                if len(kw) > 0:
                    self.sql_text.AutoCompShow(0, " ".join(kw))
                    # 默认优先选择
                    self.sql_text.AutoCompSelect(current_str)
                    self.sql_text.AutoCompSetAutoHide(True)
                    # 完成匹配后 是否删除后续字符
                    self.sql_text.AutoCompSetDropRestOfWord(True)
            else:
                event.Skip()
                # 当组合键时关闭提示
                self.sql_text.AutoCompCancel()
            self.last_pos = current_pos

    # 执行格式化
    def exec_format(self, event):
        source_sql = self.sql_text.GetValue()
        try:
            if self.space_menu.IsChecked() == 1:
                space_num = 1
            else:
                space_num = 2
            if self.show_end_semicolon_menu.IsChecked() == 1:
                is_end_semicolon = 1
            else:
                is_end_semicolon = 0
            result = sql_format_exec.sql_format(source_sql, self.comma_menu.IsChecked(), space_num,
                                                self.row_menu.IsChecked(), is_end_semicolon)
            result_sql = result[0]
            if self.table_menu.IsChecked() == 1 and result[1] != []:
                result_sql = result_sql + '\r\n\r\n-- ' + ','.join(result[1])
            self.sql_text.SetValue(result_sql)
        except Exception as a:
            self.sql_text.SetValue("调用出现问题:{0}".format(a))

    # 按钮样式
    def button_enter(self, event):
        self.button.SetBackgroundColour("#338BB8")
        self.button.SetForegroundColour("#FFFFFF")

    def button_leave(self, event):
        self.button.SetBackgroundColour(self.button_bc)
        self.button.SetForegroundColour(self.button_fc)


class SqlFormat(wx.Frame):
    """主体(菜单栏+页卡+执行按钮)"""

    def __init__(self):
        super(SqlFormat, self).__init__(None, title='SQL格式助手', size=(640, 480), style=wx.DEFAULT_FRAME_STYLE)
        self.SetIcon(wx.Icon('sql_format.ico'))
        self.SetBackgroundColour("#FFFFFF")
        self.Center()

        self.menu_bar = wx.MenuBar()
        # 菜单栏-文件
        self.file_menu = wx.Menu()
        self.new_menu = wx.MenuItem(self.file_menu, 11, u"新建", kind=wx.ITEM_NORMAL)
        self.open_menu = wx.MenuItem(self.file_menu, 12, u"打开(O)", kind=wx.ITEM_NORMAL)
        self.save_menu = wx.MenuItem(self.file_menu, 13, u"保存(S)", kind=wx.ITEM_NORMAL)
        self.close_menu = wx.MenuItem(self.file_menu, 14, u"关闭", kind=wx.ITEM_NORMAL)
        self.search_menu = wx.MenuItem(self.file_menu, 19, u"查找&替换(F)", kind=wx.ITEM_NORMAL)
        self.file_menu.Append(self.new_menu)
        self.file_menu.Append(self.open_menu)
        self.file_menu.Append(self.save_menu)
        self.file_menu.Append(self.close_menu)
        self.file_menu.AppendSeparator()
        self.file_menu.Append(self.search_menu)

        # 菜单栏-设置
        self.set_menu = wx.Menu()
        self.font_menu = wx.MenuItem(self.set_menu, 21, "字体", kind=wx.ITEM_NORMAL)
        self.comma_menu = wx.MenuItem(self.set_menu, 22, "逗号前置", kind=wx.ITEM_CHECK)
        self.table_menu = wx.MenuItem(self.set_menu, 23, "输出表名", kind=wx.ITEM_CHECK)
        # 后续考虑改成输入框，用户自定义关键词后续的空格个数
        self.space_menu = wx.MenuItem(self.set_menu, 24, "单空格", kind=wx.ITEM_CHECK)
        self.row_menu = wx.MenuItem(self.set_menu, 25, "段前空行", kind=wx.ITEM_CHECK)
        self.set_menu.Append(self.font_menu)
        self.set_menu.AppendSeparator()
        self.set_menu.Append(self.comma_menu)
        self.set_menu.Append(self.table_menu)
        self.set_menu.Append(self.space_menu)
        self.set_menu.Append(self.row_menu)

        # 菜单栏-显示
        self.show_menu = wx.Menu()
        self.show_space_menu = wx.MenuItem(self.show_menu, 31, "显示空格", kind=wx.ITEM_CHECK)
        self.wrap_menu = wx.MenuItem(self.show_menu, 32, "自动换行", kind=wx.ITEM_CHECK)
        self.kw_tip_menu = wx.MenuItem(self.show_menu, 33, "关键词提示", kind=wx.ITEM_CHECK)
        self.show_end_semicolon_menu = wx.MenuItem(self.set_menu, 34, "末尾分号", kind=wx.ITEM_CHECK)
        self.show_menu.Append(self.show_space_menu)
        self.show_menu.Append(self.show_end_semicolon_menu)
        self.show_menu.Append(self.wrap_menu)
        self.show_menu.AppendSeparator()
        self.show_menu.Append(self.kw_tip_menu)

        # 菜单栏-建表
        self.create_table_menu = wx.Menu()
        self.hive_menu = wx.MenuItem(self.create_table_menu, 41, "Hive", kind=wx.ITEM_NORMAL)
        self.create_table_menu.Append(self.hive_menu)

        # 菜单栏-自定义
        self.custom_menu = wx.Menu()
        self.comment_menu = wx.MenuItem(self.custom_menu, 91, '注释')

        # 菜单栏
        self.menu_bar.Append(self.file_menu, title="文件")
        self.menu_bar.Append(self.set_menu, title="设置")
        self.menu_bar.Append(self.show_menu, title="显示")
        self.menu_bar.Append(self.create_table_menu, title="建表")
        self.SetMenuBar(self.menu_bar)

        # 菜单动作
        self.file_menu.Bind(wx.EVT_MENU, self.menu_event)
        self.set_menu.Bind(wx.EVT_MENU, self.menu_event)
        self.show_menu.Bind(wx.EVT_MENU, self.menu_event)
        self.create_table_menu.Bind(wx.EVT_MENU, self.menu_event)

        # 查找&替换对话框 --查找/替换，向上/向下，区分大小写
        self.search_dialog = wx.Dialog(self, title='查找&替换', size=(400, 180),
                                       style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        self.search_dialog.Position = (self.Position[0] + self.Size[0] / 2 - self.search_dialog.Size[0] / 2,
                                       self.Position[1] + self.Size[1] / 2 - self.search_dialog.Size[1] / 2)
        self.search_dialog_panel = wx.Panel(self.search_dialog)
        self.find_lable = wx.StaticText(parent=self.search_dialog_panel, label='查找内容:')
        self.find_text = wx.TextCtrl(parent=self.search_dialog_panel)
        self.find_button = wx.Button(parent=self.search_dialog_panel, label='查找')
        self.replace_lable = wx.StaticText(parent=self.search_dialog_panel, label='替换内容:')
        self.replace_text = wx.TextCtrl(parent=self.search_dialog_panel)
        self.replace_button = wx.Button(parent=self.search_dialog_panel, label='替换')
        self.direction_box = wx.RadioBox(parent=self.search_dialog_panel, label='方向', choices=['向上', '向下'],
                                         style=wx.RA_SPECIFY_COLS)
        self.direction_box.SetSelection(1)
        self.case_sensitive_box = wx.CheckBox(parent=self.search_dialog_panel, label='区分大小写')
        # 查找&替换对话框布局
        self.search_dialog_vbox1 = wx.BoxSizer()
        self.search_dialog_vbox1.Add(self.find_lable, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        self.search_dialog_vbox1.Add(self.find_text, proportion=1, flag=wx.ALIGN_CENTER | wx.RIGHT, border=5)
        self.search_dialog_vbox1.Add(self.find_button, proportion=0, flag=wx.ALIGN_CENTER | wx.LEFT, border=5)
        self.search_dialog_vbox2 = wx.BoxSizer()
        self.search_dialog_vbox2.Add(self.replace_lable, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        self.search_dialog_vbox2.Add(self.replace_text, proportion=1, flag=wx.ALIGN_CENTER | wx.RIGHT, border=5)
        self.search_dialog_vbox2.Add(self.replace_button, proportion=0, flag=wx.ALIGN_CENTER | wx.LEFT, border=5)
        self.direction_vbox = wx.BoxSizer()
        self.direction_vbox.Add(self.direction_box)
        self.case_sensitive_vbox = wx.BoxSizer()
        self.case_sensitive_vbox.Add(self.case_sensitive_box)
        self.search_dialog_vbox3 = wx.BoxSizer()
        self.search_dialog_vbox3.Add(self.direction_vbox, proportion=1, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        self.search_dialog_vbox3.Add(self.case_sensitive_vbox, proportion=0, flag=wx.ALL | wx.ALIGN_CENTER, border=5)
        self.search_dialog_hbox = wx.BoxSizer(wx.VERTICAL)
        self.search_dialog_hbox.Add(self.search_dialog_vbox1, flag=wx.TOP | wx.EXPAND, border=5)
        self.search_dialog_hbox.Add(self.search_dialog_vbox2, flag=wx.TOP | wx.EXPAND, border=5)
        self.search_dialog_hbox.Add(self.search_dialog_vbox3, flag=wx.TOP | wx.EXPAND, border=5)
        self.search_dialog_panel.SetSizer(self.search_dialog_hbox)
        # 查找&替换对话框动作
        self.find_button.Bind(wx.EVT_BUTTON, self.find)
        self.replace_button.Bind(wx.EVT_BUTTON, self.replace)

        # 建表对话框  可变大小-wx.RESIZE_BORDER
        self.create_table_dialog = wx.Dialog(self, size=(370, 450), style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        self.create_table_dialog.Center()
        self.create_table_dialog_panel = wx.Panel(self.create_table_dialog)
        # 字段属性
        self.column_grid = wg.Grid(self.create_table_dialog_panel)
        # 滚动条显示：wx.SHOW_SB_DEFAULT
        self.column_grid.ShowScrollbars(wx.SHOW_SB_NEVER, wx.SHOW_SB_NEVER)
        self.column_grid.SetRowLabelSize(20)
        self.column_grid.SetDefaultColSize((self.create_table_dialog.Size[0] - 50) / 4, False)
        self.column_grid.DisableDragColSize()
        self.column_grid.DisableDragRowSize()
        self.column_grid.SetDefaultCellOverflow(False)
        self.column_grid.ClearGrid()
        self.column_grid.CreateGrid(9, 4)
        self.column_grid.SetColLabelValue(0, '字段名')
        self.column_grid.SetColLabelValue(1, '字段类型')
        self.column_grid.SetColLabelValue(2, '注释')
        self.column_grid.SetColLabelValue(3, '是否分区')
        self.column_grid.SetColFormatBool(3)
        # 表属性
        self.table_name_lable = wx.StaticText(parent=self.create_table_dialog_panel, label='表名:', size=(65, 20))
        self.table_comment_lable = wx.StaticText(parent=self.create_table_dialog_panel, label='注释:', size=(65, 20))
        self.table_divide_lable = wx.StaticText(parent=self.create_table_dialog_panel, label='列分割依据:', size=(65, 20))
        self.table_store_lable = wx.StaticText(parent=self.create_table_dialog_panel, label='数据格式:', size=(65, 20))
        self.table_path_lable = wx.StaticText(parent=self.create_table_dialog_panel, label='hdfs路径:', size=(65, 20))
        self.table_type_lable = wx.StaticText(parent=self.create_table_dialog_panel, label='表类型:', size=(65, 20))
        self.table_name_text = wx.TextCtrl(parent=self.create_table_dialog_panel)
        self.table_comment_text = wx.TextCtrl(parent=self.create_table_dialog_panel)
        self.table_divide_text = wx.TextCtrl(parent=self.create_table_dialog_panel, value='\\t')
        self.table_store_text = wx.ComboBox(parent=self.create_table_dialog_panel, value='TEXTFILE',
                                            choices=['TEXTFILE', 'PARQUET', 'SEQUENCEFILE', 'RCFILE', 'ORC'])
        self.table_path_text = wx.TextCtrl(parent=self.create_table_dialog_panel)
        self.table_type_text = wx.ComboBox(parent=self.create_table_dialog_panel, value='内部表', choices=['内部表', '外部表'])
        self.create_table_button = wx.Button(parent=self.create_table_dialog_panel, label='生成')
        # 布局
        self.table_name_box = wx.BoxSizer()
        self.table_name_box.Add(self.table_name_lable, proportion=0, flag=wx.ALL, border=5)
        self.table_name_box.Add(self.table_name_text, proportion=1)
        self.table_comment_box = wx.BoxSizer()
        self.table_comment_box.Add(self.table_comment_lable, proportion=0, flag=wx.ALL, border=5)
        self.table_comment_box.Add(self.table_comment_text, proportion=1)
        self.table_divide_box = wx.BoxSizer()
        self.table_divide_box.Add(self.table_divide_lable, proportion=0, flag=wx.ALL, border=5)
        self.table_divide_box.Add(self.table_divide_text, proportion=1)
        self.table_store_box = wx.BoxSizer()
        self.table_store_box.Add(self.table_store_lable, proportion=0, flag=wx.ALL, border=5)
        self.table_store_box.Add(self.table_store_text, proportion=1)
        self.table_path_box = wx.BoxSizer()
        self.table_path_box.Add(self.table_path_lable, proportion=0, flag=wx.ALL, border=5)
        self.table_path_box.Add(self.table_path_text, proportion=1)
        self.table_type_box = wx.BoxSizer()
        self.table_type_box.Add(self.table_type_lable, proportion=0, flag=wx.ALL, border=5)
        self.table_type_box.Add(self.table_type_text, proportion=1)
        self.table_type_box.Add(self.create_table_button, proportion=0, flag=wx.LEFT, border=5)
        self.table_box = wx.BoxSizer(wx.VERTICAL)
        self.table_box.Add(self.table_name_box, flag=wx.EXPAND)
        self.table_box.Add(self.table_comment_box, flag=wx.EXPAND)
        self.table_box.Add(self.table_divide_box, flag=wx.EXPAND)
        self.table_box.Add(self.table_store_box, flag=wx.EXPAND)
        self.table_box.Add(self.table_path_box, flag=wx.EXPAND)
        self.table_box.Add(self.table_type_box, flag=wx.EXPAND)
        self.column_box = wx.BoxSizer()
        self.column_box.Add(self.column_grid, flag=wx.EXPAND)
        self.create_table_dialog_vbox = wx.BoxSizer(wx.VERTICAL)
        self.create_table_dialog_vbox.Add(self.column_box, proportion=1, flag=wx.ALL | wx.EXPAND, border=5)
        self.create_table_dialog_vbox.Add(self.table_box, proportion=0, flag=wx.ALL | wx.EXPAND, border=5)
        self.create_table_dialog_panel.SetSizer(self.create_table_dialog_vbox)
        self.column_grid.Bind(wg.EVT_GRID_LABEL_LEFT_CLICK, self.grid_insert_row)
        self.column_grid.Bind(wg.EVT_GRID_LABEL_RIGHT_CLICK, self.grid_delete_row)
        self.create_table_button.Bind(wx.EVT_BUTTON, self.create_table_sql)

        # 快捷键
        keyboard = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('o'), self.open_menu.GetId()),
            (wx.ACCEL_CTRL, ord('s'), self.save_menu.GetId()),
            (wx.ACCEL_CTRL, ord('f'), self.search_menu.GetId()),
            (wx.ACCEL_CTRL, ord('q'), self.comment_menu.GetId()),
        ])
        self.SetAcceleratorTable(keyboard)
        self.Bind(wx.EVT_MENU, self.add_comment, id=self.comment_menu.GetId())

        # 读取预设变量
        self.set_info = configparser.ConfigParser()
        if os.path.exists('set_info.ini'):
            self.set_info.read('set_info.ini')
            set_data = dict(self.set_info.items('set_info'))
            # 配置信息校验（ps：如果配置值出现非bool值，需单独设置）
            for i in ['comma', 'table', 'space', 'row', 'show_space', 'wrap', 'kw_tip', 'end_semicolon']:
                if i not in set_data.keys():
                    self.set_info.set('set_info', i, '0')
                    set_data[i] = '0'
            self.set_info.write(open('set_info.ini', 'w+'))
            self.comma_menu.Check(int(set_data['comma']))
            self.table_menu.Check(int(set_data['table']))
            self.space_menu.Check(int(set_data['space']))
            self.row_menu.Check(int(set_data['row']))
            self.show_space_menu.Check(int(set_data['show_space']))
            self.wrap_menu.Check(int(set_data['wrap']))
            self.kw_tip_menu.Check(int(set_data['kw_tip']))
            self.show_end_semicolon_menu.Check(int(set_data['end_semicolon']))
        else:
            self.set_info.add_section('set_info')

        # 页卡
        self.sf_notebook = wa.AuiNotebook(self, style=wa.AUI_NB_CLOSE_ON_ALL_TABS | wa.AUI_NB_WINDOWLIST_BUTTON)
        self.sf_panel1 = SqlFormatPanel(self.sf_notebook, self.comma_menu, self.table_menu, self.space_menu,
                                        self.row_menu, self.show_space_menu, self.wrap_menu, self.kw_tip_menu,
                                        self.show_end_semicolon_menu)
        self.sf_notebook.AddPage(self.sf_panel1, 'new 1')
        self.notebook_list = [1]
        # 页卡动作
        self.sf_notebook.Bind(wa.EVT_AUINOTEBOOK_PAGE_CHANGED, self.notebook_update)
        self.Bind(wa.EVT_AUINOTEBOOK_BG_DCLICK, self.notebook_new, self.sf_notebook)
        self.Show()

    # 表格新增行
    def grid_insert_row(self, event):
        self.column_grid.InsertRows(pos=self.column_grid.GetGridCursorRow() + 1, numRows=1, updateLabels=True)

    # 表格删除行
    def grid_delete_row(self, event):
        self.column_grid.DeleteRows(pos=self.column_grid.GetGridCursorRow(), numRows=1, updateLabels=True)

    # 生成建表语句
    def create_table_sql(self, event):
        if self.table_name_text != "":
            pass
        else:
            exit(1)
        if self.table_type_text.GetValue() == '外部表':
            table_type = "external"
        else:
            table_type = ""
        column_sql_list = [[], []]
        for i in range(self.column_grid.GetNumberCols()):
            if len(self.column_grid.GetCellValue(i, 0)) > 0:
                tmp_sql = "`{0}` {1} comment '{2}'".format(self.column_grid.GetCellValue(i, 0),
                                                           self.column_grid.GetCellValue(i, 1),
                                                           self.column_grid.GetCellValue(i, 2))
                if self.column_grid.GetCellValue(i, 3) == '1':
                    column_sql_list[1].append(tmp_sql)
                else:
                    column_sql_list[0].append(tmp_sql)
        if len(column_sql_list[1]) > 0:
            partition_sql = "partitioned by ({0})".format(",".join(column_sql_list[1]))
        else:
            partition_sql = ""
        if len(self.table_path_text.GetValue()) > 0:
            location_sql = "location '{0}'".format(self.table_path_text.GetValue())
        else:
            location_sql = ""
        ct_sql = "create {0} table {1} ({2}) comment '{3}' {4} row format delimited fields terminated by '{5}' " \
                 "store as {6} {7}".format(table_type, self.table_name_text.GetValue(), ",".join(column_sql_list[0]),
                                           self.table_comment_text.GetValue(), partition_sql,
                                           self.table_divide_text.GetValue(), self.table_store_text.GetValue(),
                                           location_sql)
        self.sf_panel1.sql_text.SetValue(ct_sql)

    # 菜单栏配置
    def menu_event(self, event):
        sf_panel = self.sf_notebook.GetCurrentPage()
        event_id = event.GetId()
        if event_id == self.new_menu.GetId():
            self.sf_notebook.ChangeSelection(self.notebook_new(event))
        elif event_id == self.open_menu.GetId():
            self.sf_notebook.ChangeSelection(self.notebook_open())
        elif event_id == self.save_menu.GetId():
            self.notebook_save()
        elif event_id == self.close_menu.GetId():
            self.notebook_close()
        elif event_id == self.search_menu.GetId():
            self.search_dialog.Show()
        elif event_id == self.hive_menu.GetId():
            self.create_table_dialog.Title = 'Hive建表'
            self.create_table_dialog.Show()
        elif event_id == self.font_menu.GetId():
            font_dlg = wx.FontDialog()
            if font_dlg.ShowModal() == wx.ID_OK:
                data = font_dlg.GetFontData()
                sf_panel.sql_text.StyleSetFont(stc.STC_SQL_IDENTIFIER, data.GetChosenFont())
            font_dlg.Destroy()
        elif event_id == self.show_space_menu.GetId():
            sf_panel.sql_text.SetViewWhiteSpace(self.show_space_menu.IsChecked())
        elif event_id == self.wrap_menu.GetId():
            sf_panel.sql_text.SetWrapMode(self.wrap_menu.IsChecked())
        elif event_id == self.show_end_semicolon_menu.GetId():
            if self.show_end_semicolon_menu.IsChecked() is False:
                sf_panel.sql_text.SetValue(re.sub(r';(?=\s*$)', '', sf_panel.sql_text.GetValue()))
            elif re.search(r'.+;\s*$', sf_panel.sql_text.GetValue()):
                pass
            else:
                sf_panel.sql_text.SetValue(re.sub(r'\s*$', '', sf_panel.sql_text.GetValue()) + ';\n')
        # 记录配置
        self.set_info.set('set_info', 'comma', str(int(self.comma_menu.IsChecked())))
        self.set_info.set('set_info', 'table', str(int(self.table_menu.IsChecked())))
        self.set_info.set('set_info', 'space', str(int(self.space_menu.IsChecked())))
        self.set_info.set('set_info', 'row', str(int(self.row_menu.IsChecked())))
        self.set_info.set('set_info', 'show_space', str(int(self.show_space_menu.IsChecked())))
        self.set_info.set('set_info', 'wrap', str(int(self.wrap_menu.IsChecked())))
        self.set_info.set('set_info', 'kw_tip', str(int(self.kw_tip_menu.IsChecked())))
        self.set_info.set('set_info', 'end_semicolon', str(int(self.show_end_semicolon_menu.IsChecked())))
        self.set_info.write(open('set_info.ini', 'w+'))

    # 获取当前页卡并更新
    def notebook_update(self, event):
        sf_panel = self.sf_notebook.GetCurrentPage()
        sf_panel.sql_text.SetViewWhiteSpace(self.show_space_menu.IsChecked())
        sf_panel.sql_text.SetWrapMode(self.wrap_menu.IsChecked())

    # 新建页卡
    def notebook_new(self, event):
        if len(self.notebook_list) == 0:
            self.notebook_list.append(1)
        else:
            self.notebook_list.append(self.notebook_list[-1] + 1)
        sf_panel = SqlFormatPanel(self.sf_notebook, self.comma_menu, self.table_menu, self.space_menu, self.row_menu,
                                  self.show_space_menu, self.wrap_menu, self.kw_tip_menu, self.show_end_semicolon_menu)
        self.sf_notebook.AddPage(sf_panel, 'new {0}'.format(self.notebook_list[-1]))
        return len(self.notebook_list) - 1

    # 已知文件打开页卡
    def notebook_open(self):
        file_open_dialog = wx.FileDialog(self, message="打开", defaultDir=os.getcwd(), wildcard='*.sql',
                                         size=(428, 266), style=wx.FD_OPEN | wx.FD_CHANGE_DIR)
        file_open_dialog.Position = (self.Position[0] + self.Size[0] / 2 - file_open_dialog.Size[0] / 2,
                                     self.Position[1] + self.Size[1] / 2 - file_open_dialog.Size[1] / 2)
        if file_open_dialog.ShowModal() == wx.ID_OK:
            filename = file_open_dialog.GetPath()
            save_file = open(filename, 'rb')
            sql = save_file.read()
            save_file.close()
            sf_panel = SqlFormatPanel(self.sf_notebook, self.comma_menu, self.table_menu, self.space_menu,
                                      self.row_menu, self.show_space_menu, self.wrap_menu, self.kw_tip_menu,
                                      self.show_end_semicolon_menu)
            sf_panel.sql_text.SetValue(sql)
            self.sf_notebook.AddPage(sf_panel, '{0}'.format(file_open_dialog.Filename))
            self.notebook_list.append(self.notebook_list[-1] + 1)
        file_open_dialog.Destroy()
        return len(self.notebook_list) - 1

    # 关闭页卡
    def notebook_close(self):
        curr_page_num = self.sf_notebook.GetSelection()
        self.notebook_list.pop(curr_page_num)
        self.sf_notebook.DeletePage(curr_page_num)

    def notebook_save(self):
        curr_page_num = self.sf_notebook.GetSelection()
        curr_page_name = self.sf_notebook.GetPageText(curr_page_num)
        file_save_dialog = wx.FileDialog(self, message="保存", defaultDir=os.getcwd(), wildcard='*.sql', size=(428, 266),
                                         style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT | wx.FD_CHANGE_DIR,
                                         defaultFile=curr_page_name)
        file_save_dialog.Position = (self.Position[0] + self.Size[0] / 2 - file_save_dialog.Size[0] / 2,
                                     self.Position[1] + self.Size[1] / 2 - file_save_dialog.Size[1] / 2)
        sf_panel = self.sf_notebook.GetCurrentPage()
        sql_text = sf_panel.sql_text.GetValue()
        # print(sql_text)
        if file_save_dialog.ShowModal() == wx.ID_OK:
            filename = file_save_dialog.GetPath()
            save_file = open(filename, 'w')
            save_file.write(sql_text)
            save_file.close()
            self.sf_notebook.SetPageText(curr_page_num, file_save_dialog.Filename)
        file_save_dialog.Destroy()

    def find(self, event):
        sf_panel = self.sf_notebook.GetCurrentPage()
        if self.case_sensitive_box.IsChecked():
            flags = 5
        else:
            flags = 0
        curr_pos = sf_panel.sql_text.GetCurrentPos()
        sf_panel.sql_text.SetSelection(curr_pos, curr_pos)
        find_object = self.find_text.GetValue().encode("utf-8")
        find_len = len(find_object)
        sql_content = sf_panel.sql_text.GetValue().encode('utf-8')
        sql_len = len(sql_content)
        direction = self.direction_box.GetSelection()
        if direction == 0:
            curr_pos = curr_pos - find_len
            max_pos = 0
        else:
            max_pos = sql_len
        curr_pos = sf_panel.sql_text.FindText(curr_pos, max_pos, find_object, flags)
        if curr_pos == -1 and direction == 1:
            curr_pos = sf_panel.sql_text.FindText(0, sql_len, find_object, flags)
        elif curr_pos == -1 and direction == 0:
            curr_pos = sf_panel.sql_text.FindText(sql_len, 0, find_object, flags)
        sf_panel.sql_text.SetCurrentPos(curr_pos)
        sf_panel.sql_text.ScrollToLine(sf_panel.sql_text.GetCurrentLine())
        if curr_pos != -1:
            sf_panel.sql_text.SetSelection(curr_pos, curr_pos + find_len)

    def replace(self, event):
        sf_panel = self.sf_notebook.GetCurrentPage()
        if self.case_sensitive_box.IsChecked():
            flags = 5
        else:
            flags = 0
        curr_pos = sf_panel.sql_text.GetCurrentPos()
        sf_panel.sql_text.SetSelection(curr_pos, curr_pos)
        find_object = self.find_text.GetValue().encode("utf-8")
        find_len = len(find_object)
        replace_object = self.replace_text.GetValue().encode("utf-8")
        replace_len = len(replace_object)
        sql_content = sf_panel.sql_text.GetValue().encode('utf-8')
        sql_len = len(sql_content)
        direction = self.direction_box.GetSelection()
        if direction == 0:
            curr_pos = curr_pos - find_len
            max_pos = 0
        else:
            max_pos = sql_len
        curr_pos = sf_panel.sql_text.FindText(curr_pos, max_pos, find_object, flags)
        if curr_pos == -1 and direction == 1:
            curr_pos = sf_panel.sql_text.FindText(0, sql_len, find_object, flags)
        elif curr_pos == -1 and direction == 0:
            curr_pos = sf_panel.sql_text.FindText(sql_len, 0, find_object, flags)
        sf_panel.sql_text.SetCurrentPos(curr_pos)
        sf_panel.sql_text.ScrollToLine(sf_panel.sql_text.GetCurrentLine())
        if curr_pos != -1:
            sf_panel.sql_text.SetValue(sql_content[:curr_pos] + replace_object + sql_content[curr_pos + find_len:])
            sf_panel.sql_text.SetSelection(curr_pos, curr_pos + replace_len)

    # 注释
    def add_comment(self, event):
        sf_panel = self.sf_notebook.GetCurrentPage()
        curr_pos = sf_panel.sql_text.GetCurrentPos()
        select_text = sf_panel.sql_text.GetSelectedText().encode('utf-8')
        tmp_text = sf_panel.sql_text.GetValue().encode('utf-8')
        if len(select_text) != 0:
            tmp_select_text = re.findall(r'(^\s+|\S.*(\n\s+)?)(?=(\S|$))', select_text)
            mdf_select_text = ''
            for text_ant in tmp_select_text:
                if re.match(r'^\s*$', text_ant[0]):
                    mdf_select_text += text_ant[0]
                elif re.match(r'^--', text_ant[0]):
                    tmp_text_ant = re.sub(r'--', '', text_ant[0], 1)
                    mdf_select_text += tmp_text_ant
                else:
                    mdf_select_text += '--' + text_ant[0]
            # 替换
            ss_pos = sf_panel.sql_text.GetSelectionStart()
            se_pos = sf_panel.sql_text.GetSelectionEnd()
            result_text = tmp_text[:ss_pos] + mdf_select_text + tmp_text[se_pos:]
            sf_panel.sql_text.SetValue(result_text.decode('utf-8'))
        else:
            if tmp_text[curr_pos:curr_pos + 2] == '--':
                sf_panel.sql_text.DeleteRange(curr_pos, 2)
            else:
                sf_panel.sql_text.InsertText(curr_pos, '--')
        sf_panel.sql_text.SetEmptySelection(curr_pos)


if __name__ == '__main__':
    app = wx.App()
    SqlFormat()
    app.MainLoop()


