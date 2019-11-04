# coding=utf-8

import wx
import wx.stc as ws
import sql_format_exec

sf_app = wx.App()
sf_frame = wx.Frame(None, title='SQL格式助手', size=(640, 480), style=wx.DEFAULT_FRAME_STYLE)
sf_frame.SetIcon(wx.Icon('sql_format.ico'))
sf_frame.SetBackgroundColour("#FFFFFF")
sf_frame.Center()
# 菜单栏设置
menu_bar = wx.MenuBar()
set_menu = wx.Menu()
font_menu = wx.MenuItem(set_menu, 1, "字体", kind=wx.ITEM_NORMAL)
comma_menu = wx.MenuItem(set_menu, 4, "逗号前置", kind=wx.ITEM_CHECK)
table_menu = wx.MenuItem(set_menu, 5, "输出表名", kind=wx.ITEM_CHECK)
set_menu.Append(font_menu)
set_menu.AppendSeparator()
set_menu.Append(comma_menu)
set_menu.Append(table_menu)

show_menu = wx.Menu()
show_space_menu = wx.MenuItem(set_menu, 2, "显示空格", kind=wx.ITEM_CHECK)
wrap_menu = wx.MenuItem(set_menu, 3, "自动换行", kind=wx.ITEM_CHECK)
show_menu.Append(show_space_menu)
show_menu.Append(wrap_menu)

menu_bar.Append(set_menu, title="设置")
menu_bar.Append(show_menu, title="显示")
sf_frame.SetMenuBar(menu_bar)

sf_panel = wx.Panel(sf_frame)
sf_panel.SetBackgroundColour('#F5F5F5')

sql_text = ws.StyledTextCtrl(sf_panel, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_RICH)
sql_text.SetMarginType(1, ws.STC_MARGIN_NUMBER)
sql_text.SetMarginWidth(1, 25)
sql_text.StyleSetFontAttr(0, 10, "Consolas", False, False, False)
sql_text.SetUseTabs(False)
sql_text.SetValue(u"""
select  a.user_id,
        a.name
  from  (
        -- 测试数据
        select  user_id,
                trim(name) as name,--中文名字
                row_number() over (partition by user_id  order by apply_time desc) as rn,
                case when 1=1 then endddd else appendas end,
                test
          from  ods.ods_chain_store_user_auth
         where  regexp_like(trim(name), '^[\u4E00-\u9FA5]+$')
           and  (1 = 1 or 2<> 2)
        ) a
 where  rn = 1
 """)

# 按钮控件
button = wx.Button(sf_panel, label="格式化", style=wx.Center)
button.SetWindowStyleFlag(wx.NO_BORDER)
button.SetDefault()
button_bc = button.GetBackgroundColour()
button_fc = button.GetForegroundColour()


def button_enter(event):
    button.SetBackgroundColour("#338BB8")
    button.SetForegroundColour("#FFFFFF")


def button_leave(event):
    button.SetBackgroundColour(button_bc)
    button.SetForegroundColour(button_fc)


def exec_format(event):
    source_sql = sql_text.GetValue()
    try:
        result = sql_format_exec.sql_format(source_sql, comma_menu.IsChecked())
        result_sql = result[0]
        if table_menu.IsChecked() == 1:
            result_sql = result_sql + '\r\n\r\n-- ' + ','.join(result[1])
        sql_text.SetValue(result_sql)
    except Exception as a:
        sql_text.SetValue("调用出现问题:{0}".format(a))


button.Bind(wx.EVT_ENTER_WINDOW, button_enter)
button.Bind(wx.EVT_LEAVE_WINDOW, button_leave)
button.Bind(wx.EVT_BUTTON, exec_format)


def event_menu(event):
    event_id = event.GetId()
    if event_id == 1:
        dlg = wx.FontDialog()
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetFontData()
            sql_text.StyleSetFont(0, data.GetChosenFont())
        dlg.Destroy()
    elif event_id == 2:
        sql_text.SetViewWhiteSpace(show_space_menu.IsChecked())
        sql_text.SetWhitespaceForeground(True, 'Red')
        sql_text.SetWhitespaceSize(2)
    elif event_id == 3:
        if wrap_menu.IsChecked():
            sql_text.SetWrapMode(1)
        else:
            sql_text.SetWrapMode(0)


set_menu.Bind(wx.EVT_MENU, event_menu)
show_menu.Bind(wx.EVT_MENU, event_menu)


v_box = wx.BoxSizer(wx.VERTICAL)
v_box.Add(sql_text, proportion=1, flag=wx.EXPAND)
v_box.Add(button, proportion=0, flag=wx.ALIGN_CENTER | wx.ALL, border=5)
sf_panel.SetSizer(v_box)

sf_frame.Show()
sf_app.MainLoop()
