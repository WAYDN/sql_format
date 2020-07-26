# coding=utf-8

import wx
import wx.stc as stc
import sql_format_exec
import re
import os
import configparser


class SqlFormat(wx.Frame):
    def __init__(self):
        super(SqlFormat, self).__init__(None, title='SQL格式助手', size=(640, 480), style=wx.DEFAULT_FRAME_STYLE)
        self.SetIcon(wx.Icon('sql_format.ico'))
        self.SetBackgroundColour("#FFFFFF")
        self.Center()

        self.menu_bar = wx.MenuBar()
        # 菜单栏-文件
        self.file_menu = wx.Menu()
        self.search_menu = wx.MenuItem(self.file_menu, 11, u"查找||替换", kind=wx.ITEM_NORMAL)
        self.file_menu.Append(self.search_menu)

        # 菜单栏-设置
        self.set_menu = wx.Menu()
        self.font_menu = wx.MenuItem(self.set_menu, 21, "字体", kind=wx.ITEM_NORMAL)
        self.comma_menu = wx.MenuItem(self.set_menu, 22, "逗号前置", kind=wx.ITEM_CHECK)
        self.table_menu = wx.MenuItem(self.set_menu, 23, "输出表名", kind=wx.ITEM_CHECK)
        # 后续考虑改成输入框，用户自定义关键词后续的空格个数
        self.space_menu = wx.MenuItem(self.set_menu, 24, "单空格", kind=wx.ITEM_CHECK)
        self.set_menu.Append(self.font_menu)
        self.set_menu.AppendSeparator()
        self.set_menu.Append(self.comma_menu)
        self.set_menu.Append(self.table_menu)
        self.set_menu.Append(self.space_menu)

        # 菜单栏-显示
        self.show_menu = wx.Menu()
        self.show_space_menu = wx.MenuItem(self.set_menu, 31, "显示空格", kind=wx.ITEM_CHECK)
        self.wrap_menu = wx.MenuItem(self.set_menu, 32, "自动换行", kind=wx.ITEM_CHECK)
        self.kw_tip_menu = wx.MenuItem(self.set_menu, 33, "关键词提示", kind=wx.ITEM_CHECK)
        self.show_menu.Append(self.show_space_menu)
        self.show_menu.Append(self.wrap_menu)
        self.show_menu.AppendSeparator()
        self.show_menu.Append(self.kw_tip_menu)

        self.menu_bar.Append(self.file_menu, title="文件")
        self.menu_bar.Append(self.set_menu, title="设置")
        self.menu_bar.Append(self.show_menu, title="显示")
        self.SetMenuBar(self.menu_bar)

        # 菜单动作
        self.file_menu.Bind(wx.EVT_MENU, self.event_menu)
        self.set_menu.Bind(wx.EVT_MENU, self.event_menu)
        self.show_menu.Bind(wx.EVT_MENU, self.event_menu)
        # 菜单搜索动作
        self.Bind(wx.EVT_FIND, self.find)
        self.Bind(wx.EVT_FIND_NEXT, self.find)
        self.Bind(wx.EVT_FIND_REPLACE, self.replace)

        # 读取预设变量
        self.set_info = configparser.ConfigParser()
        if os.path.exists('set_info.ini'):
            self.set_info.read('set_info.ini')
            set_data = dict(self.set_info.items('set_info'))
            self.comma_menu.Check(int(set_data['comma']))
            self.table_menu.Check(int(set_data['table']))
            self.space_menu.Check(int(set_data['space']))
            self.show_space_menu.Check(int(set_data['show_space']))
            self.wrap_menu.Check(int(set_data['wrap']))
            self.kw_tip_menu.Check(int(set_data['kw_tip']))
        else:
            self.set_info.add_section('set_info')

        self.sf_panel = wx.Panel(self)
        self.sf_panel.SetBackgroundColour('#F5F5F5')

        self.sql_text = stc.StyledTextCtrl(self.sf_panel, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_RICH)
        self.sql_text.SetMarginType(1, stc.STC_MARGIN_NUMBER)
        self.sql_text.SetMarginWidth(1, 25)
        self.sql_text.StyleSetFontAttr(0, 10, "Consolas", False, False, False)
        self.sql_text.SetUseTabs(False)
        self.sql_text.SetViewWhiteSpace(self.show_space_menu.IsChecked())
        self.sql_text.SetWhitespaceForeground(True, 'Red')
        self.sql_text.SetWhitespaceSize(2)
        self.sql_text.SetWrapMode(self.wrap_menu.IsChecked())
        self.sql_text_face = self.sql_text.StyleGetFaceName(0)
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
        self.sql_text.SetValue(u"""
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
         where  rn = 1; select 123;select 12333
         """)
        # 文本动作
        self.sql_text.Bind(stc.EVT_STC_UPDATEUI, self.highlight)
        self.sql_text.Bind(wx.EVT_KEY_UP, self.keyword_tip)

        # 按钮控件
        self.button = wx.Button(self.sf_panel, label="格式化", style=wx.Center)
        self.button.SetWindowStyleFlag(wx.NO_BORDER)
        self.button.SetDefault()
        self.button_bc = self.button.GetBackgroundColour()
        self.button_fc = self.button.GetForegroundColour()
        # 按钮动作
        self.button.Bind(wx.EVT_ENTER_WINDOW, self.button_enter)
        self.button.Bind(wx.EVT_LEAVE_WINDOW, self.button_leave)
        self.button.Bind(wx.EVT_BUTTON, self.exec_format)

        # 布局
        self.v_box = wx.BoxSizer(wx.VERTICAL)
        self.v_box.Add(self.sql_text, proportion=1, flag=wx.EXPAND)
        self.v_box.Add(self.button, proportion=0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
        self.sf_panel.SetSizer(self.v_box)

        self.Show()

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
        self.sql_text.StyleSetSpec(stc.STC_STYLE_BRACELIGHT, "fore:#000000,back:#87CEFF,face:{0}".format(self.sql_text_face))

        # 选择高亮
        select_context = self.sql_text.GetSelectedText()
        if re.search(r'^\w+$', select_context):
            self.sql_text.SetSelBackground(True, "#B4EEB4")
        else:
            self.sql_text.SetSelBackground(True, "#BDBDBD")

    # 关键词提示
    def keyword_tip(self, event):
        global last_pos
        if self.kw_tip_menu.IsChecked():
            current_pos = self.sql_text.GetCurrentPos()
            sql_content = self.sql_text.GetValue().encode('utf-8')
            word_start_pos = self.sql_text.WordStartPosition(current_pos, True)
            current_str = sql_content[word_start_pos:current_pos].decode('utf-8')
            tmp_kw = ['select', 'from', 'left', 'right', 'full', 'inner', 'join', 'on', 'where', 'group', 'by', 'order',
                      'limit', 'having', 'union', 'all', 'insert', 'create', 'lateral', 'view', 'with', 'as']
            kw = []
            sql_kw = re.findall(r'\w{2,}', self.sql_text.GetValue())
            tmp_kw += sql_kw
            tmp_kw = list(set(tmp_kw))
            key_code = event.GetKeyCode()
            if key_code in (13, 314, 315, 316, 317):
                # 自动填补时清除历史字符并重新定位光标
                if key_code == 13 and word_start_pos < last_pos and current_str != '':
                    self.sql_text.SetValue(sql_content[:word_start_pos] + sql_content[last_pos:])
                    self.sql_text.GotoPos(current_pos - last_pos + word_start_pos)
                    # print(current_pos, last_pos, word_start_pos)
                event.Skip()
            elif current_str != '':
                for i in tmp_kw:
                    if re.search(current_str, i) and current_str != i:
                        kw.append(i)
                kw.sort()
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
            last_pos = current_pos

    # 执行格式化
    def exec_format(self, event):
        source_sql = self.sql_text.GetValue()
        try:
            if self.space_menu.IsChecked() == 1:
                space_num = 1
            else:
                space_num = 2
            result = sql_format_exec.sql_format(source_sql, self.comma_menu.IsChecked(), space_num)
            result_sql = result[0]
            if self.table_menu.IsChecked() == 1 and result[1] != []:
                result_sql = result_sql + '\r\n\r\n-- ' + ','.join(result[1])
            self.sql_text.SetValue(result_sql)
        except Exception as a:
            self.sql_text.SetValue("调用出现问题:{0}".format(a))

    # 菜单栏配置
    def event_menu(self, event):
        event_id = event.GetId()
        if event_id == 11:
            self.find_replace(self.sql_text.GetSelectedText())
        elif event_id == 21:
            # 字体设置对话框
            font_dlg = wx.FontDialog()
            if font_dlg.ShowModal() == wx.ID_OK:
                data = font_dlg.GetFontData()
                self.sql_text.StyleSetFont(stc.STC_SQL_IDENTIFIER, data.GetChosenFont())
            font_dlg.Destroy()
        elif event_id == 31:
            self.sql_text.SetViewWhiteSpace(self.show_space_menu.IsChecked())
        elif event_id == 32:
            self.sql_text.SetWrapMode(self.wrap_menu.IsChecked())
        self.set_info.set('set_info', 'comma', str(int(self.comma_menu.IsChecked())))
        self.set_info.set('set_info', 'table', str(int(self.table_menu.IsChecked())))
        self.set_info.set('set_info', 'space', str(int(self.space_menu.IsChecked())))
        self.set_info.set('set_info', 'show_space', str(int(self.show_space_menu.IsChecked())))
        self.set_info.set('set_info', 'wrap', str(int(self.wrap_menu.IsChecked())))
        self.set_info.set('set_info', 'kw_tip', str(int(self.kw_tip_menu.IsChecked())))
        self.set_info.write(open('set_info.ini', 'w+', encoding="utf-8"))

    # 查找替换对话框
    def find_replace(self, search_text):
        data = wx.FindReplaceData()
        data.SetFindString(search_text)
        find_replace_dlg = wx.FindReplaceDialog(self, wx.FindReplaceData(), u"查找替换", wx.FR_REPLACEDIALOG)
        find_replace_dlg.Show()
        # 重置sql_text 避免对话框崩溃，具体崩溃原因待定
        self.sql_text.SetValue(self.sql_text.GetValue())

    def find(self, event):
        min_pos = self.sql_text.GetCurrentPos()
        find_text = event.GetFindString()
        find_len = len(find_text.encode("utf-8"))
        text_len = self.sql_text.GetTextLength()
        start_pos = self.sql_text.FindText(min_pos, text_len, find_text)
        if start_pos == -1:
            start_pos = self.sql_text.FindText(0, text_len, find_text)
        self.sql_text.SetSelection(start_pos, start_pos + find_len)
        self.sql_text.MoveCaretInsideView()

    def replace(self, event):
        find_text = event.GetFindString()
        replace_text = event.GetReplaceString()

    # 按钮样式
    def button_enter(self, event):
        self.button.SetBackgroundColour("#338BB8")
        self.button.SetForegroundColour("#FFFFFF")

    def button_leave(self, event):
        self.button.SetBackgroundColour(self.button_bc)
        self.button.SetForegroundColour(self.button_fc)


app = wx.App()
SqlFormat()
app.MainLoop()
