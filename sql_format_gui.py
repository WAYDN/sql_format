# coding=utf-8

"""
20190319 wq 新增逗号前置功能
"""

import wx
import wx.stc as ws
from common import sql_format

sf_app = wx.App()
sf_frame = wx.Frame(None, title='SQL格式助手', size=(800, 800), style=wx.DEFAULT_FRAME_STYLE)
# 菜单栏设置
menu_bar = wx.MenuBar()
set_menu = wx.Menu()
font_menu = wx.MenuItem(set_menu, 1, "字体", kind=wx.ITEM_NORMAL)
show_space_menu = wx.MenuItem(set_menu, 2, "显示空格", kind=wx.ITEM_CHECK)
wrap_menu = wx.MenuItem(set_menu, 3, "自动换行", kind=wx.ITEM_CHECK)
set_menu.Append(font_menu)
set_menu.Append(show_space_menu)
set_menu.Append(wrap_menu)
trans_menu = wx.Menu()
comma_menu = wx.MenuItem(set_menu, 4, "逗号前置", kind=wx.ITEM_CHECK)
trans_menu.Append(comma_menu)
menu_bar.Append(set_menu, title="设置")
menu_bar.Append(trans_menu, title="变换")

sf_frame.SetMenuBar(menu_bar)
sf_frame.Center()
sf_panel = wx.Panel(sf_frame)
sf_panel.SetBackgroundColour('#F5F5F5')

source_sql_label = wx.StaticText(sf_panel, label='待处理SQL:')
source_sql_text = ws.StyledTextCtrl(sf_panel, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_RICH)
source_sql_text.SetMarginType(1, ws.STC_MARGIN_NUMBER)
source_sql_text.SetMarginWidth(1, 25)
source_sql_text.StyleSetFontAttr(0, 10, "Consolas", False, False, False)
source_sql_text.SetUseTabs(False)
source_sql_text.SetValue("""
select  a.user_id,
        a.name
  from  (
        select  user_id,
                trim(name) as name,--中文名字
                row_number() over (partiti  on by user_id  order by apply_time desc) as rn
          from  ods.ods_chain_store_user_auth
         where  regexp_like(trim(name), '^[\u4E00-\u9FA5]+$')
        ) a
 where  rn = 1
 """)
sql_label = wx.StaticText(sf_panel, label='处理后SQL:')
sql_text = ws.StyledTextCtrl(sf_panel, style=wx.TE_MULTILINE | wx.HSCROLL | wx.TE_RICH)
sql_text.SetMarginType(1, ws.STC_MARGIN_NUMBER)
sql_text.SetMarginWidth(1, 25)
sql_text.StyleSetFontAttr(0, 10, "Consolas", False, False, False)

# 按钮控件
button = wx.Button(sf_panel, label="格式化", style=wx.BORDER_MASK)
button.SetDefault()
def exec_format(event):
    source_sql = source_sql_text.GetValue()
    sql = sql_format.sql_format(source_sql)
    if comma_menu.IsChecked():
        sql_text.SetValue(sql_format.comma_trans(sql))
    else:
         sql_text.SetValue(sql)
button.Bind(wx.EVT_BUTTON, exec_format)

def eventMenu(event):
    id = event.GetId()
    if id == 1:
        dlg = wx.FontDialog()
        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetFontData()
            source_sql_text.StyleSetFont(0, data.GetChosenFont())
            sql_text.StyleSetFont(0, data.GetChosenFont())
        dlg.Destroy()
    elif id == 2:
        source_sql_text.SetViewWhiteSpace(show_space_menu.IsChecked())
        source_sql_text.SetWhitespaceForeground(True, 'Red')
        source_sql_text.SetWhitespaceSize(2)
        sql_text.SetViewWhiteSpace(show_space_menu.IsChecked())
        sql_text.SetWhitespaceForeground(True, 'Red')
        sql_text.SetWhitespaceSize(2)
    elif id == 3:
        if wrap_menu.IsChecked():
            source_sql_text.SetWrapMode(1)
            sql_text.SetWrapMode(1)
        else:
            source_sql_text.SetWrapMode(0)
            sql_text.SetWrapMode(0)
set_menu.Bind(wx.EVT_MENU, eventMenu)


source_v_box = wx.BoxSizer(wx.VERTICAL)
source_v_box.Add(source_sql_label, proportion=0)
source_v_box.Add(source_sql_text, proportion=1, flag=wx.EXPAND)
v_box = wx.BoxSizer(wx.VERTICAL)
v_box.Add(sql_label, proportion=0)
v_box.Add(sql_text, proportion=1, flag=wx.EXPAND)
v_box_2 = wx.BoxSizer(wx.VERTICAL)
v_box_2.Add(source_v_box, proportion=1, flag=wx.EXPAND)
v_box_2.Add(button, proportion=0, flag=wx.EXPAND)
v_box_2.Add(v_box, proportion=1, flag=wx.EXPAND)
sf_panel.SetSizer(v_box_2)

sf_frame.Show()
sf_app.MainLoop()
