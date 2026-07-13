"""
冰壶赛道互动演示 - Kivy 安卓版
由 matplotlib 版本移植而来，物理逻辑保持一致，改为纯 Python 实现。
入口文件必须命名为 main.py（Buildozer 要求）。

界面按三种角色拆分为三个模块：
  1. 滑行人（速度/旋转/初始角度）——常驻底部
  2. 冰面（摩擦/摆动性）——按钮展开的面板
  3. 扫冰（刷冰强度/刷到哪条线）——半透明叠在场地上，按钮开关
三个面板互斥展开。
"""
import os
import math

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.core.text import LabelBase
from kivy.metrics import dp

# ---------------------------------------------------------------------------
# 中文字体：安卓系统自带 CJK 字体，若存在则注册，保证中文正常显示
# ---------------------------------------------------------------------------
FONT_NAME = None
for _p in (
    "/system/fonts/NotoSansCJK-Regular.ttc",
    "/system/fonts/NotoSansSC-Regular.otf",
    "/system/fonts/DroidSansFallback.ttf",
    "C:/Windows/Fonts/msyh.ttc",      # 本地 Windows 测试用
    "C:/Windows/Fonts/simhei.ttf",
):
    if os.path.exists(_p):
        try:
            LabelBase.register(name="CJK", fn_regular=_p)
            FONT_NAME = "CJK"
            break
        except Exception:
            pass


def _lbl_kwargs(**kw):
    """给 Label/Slider 文本统一加上中文字体。"""
    if FONT_NAME:
        kw["font_name"] = FONT_NAME
    return kw


def _btn_font(btn):
    """给按钮设置中文字体。"""
    if FONT_NAME:
        btn.font_name = FONT_NAME
    return btn


# ---------------------------------------------------------------------------
# 赛道坐标常量
# 世界坐标：x ∈ [-6, 6]（左右宽度，米）, y ∈ [0, 80]（冰道长度，米）
# ---------------------------------------------------------------------------
WORLD_XMIN, WORLD_XMAX = -6.0, 6.0
WORLD_YMIN, WORLD_YMAX = 0.0, 80.0
HOG_Y = 15.0            # 前卫线（下线）
HOUSE_Y = 70.0          # 大本营中心
HOUSE_LINE_Y = 70.0     # 大本营中线（营线）
TOP_Y = 78.0            # 顶线（底线附近）
HOUSE_RADII = [6.0, 4.0, 2.5, 0.6]
HOUSE_COLORS = [
    (1.0, 0.8, 0.8),    # 浅红
    (1.0, 1.0, 1.0),    # 白
    (0.0, 0.0, 1.0),    # 蓝
    (1.0, 0.0, 0.0),    # 红心
]

# 刷冰目标线：名称 -> 刷到的纵向位置 y（仅 y < 该值的路段被刷）
SWEEP_TARGETS = [
    ("不刷冰", 0.0),
    ("刷到前卫线", HOG_Y),
    ("刷到营线", HOUSE_LINE_Y),
    ("刷到顶线", TOP_Y),
]


# ---------------------------------------------------------------------------
# 物理模拟
# ---------------------------------------------------------------------------
def simulate_curling(speed=3.5, rotation_rate=2.0, line_angle=0.0, sweep_factor=1.2,
                     ice_friction=1.0, ice_swing=1.0, sweep_to_y=0.0,
                     time=60.0, dt=0.05):
    """
    动摩擦模型：冰壶受恒定减速度，速度归零即停 —— 初速度越大滑得越远。
    刷冰（sweep）只对 y < sweep_to_y 的路段减小摩擦，使冰壶在该段滑得更远、curl 更小。
    """
    xs = [0.0]
    ys = [0.0]
    vx = speed * math.sin(math.radians(line_angle))   # 小横向分量
    vy = speed * math.cos(math.radians(line_angle))   # 主要纵向
    x, y = 0.0, 0.0

    base_decel = 0.26 * ice_friction
    swept_decel = base_decel / (sweep_factor ** 0.8)   # 刷过的路段摩擦更小

    n = int(time / dt)
    for _ in range(1, n):
        speed_current = math.sqrt(vx * vx + vy * vy)
        if speed_current < 0.05:
            break  # 冰壶停下，轨迹结束

        # 当前路段是否被刷冰（在目标线之前）
        swept = y < sweep_to_y
        decel = swept_decel if swept else base_decel

        # 摩擦减速：沿运动反方向
        ax = -decel * vx / speed_current
        ay = -decel * vy / speed_current

        # 旋转横向偏移(curl)：速度越慢偏移越明显；刷冰的路段 curl 也被抑制
        curl_factor = rotation_rate * 0.05 * ice_swing
        if swept:
            curl_factor *= 0.5
        perp_x = -vy / speed_current
        perp_y = vx / speed_current
        curl_acc = curl_factor * (1.0 / (speed_current ** 0.6 + 0.3))
        ax += perp_x * curl_acc
        ay += perp_y * curl_acc

        vx += ax * dt
        vy += ay * dt
        x += vx * dt
        y += vy * dt
        xs.append(x)
        ys.append(y)
    return xs, ys


# ---------------------------------------------------------------------------
# 赛道绘制 Widget
# ---------------------------------------------------------------------------
class TrackWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params = dict(speed=3.5, rotation_rate=2.0, line_angle=0.0,
                           sweep_factor=1.2, ice_friction=1.0, ice_swing=1.0,
                           sweep_to_y=0.0)
        self.bind(pos=self._redraw, size=self._redraw)

    # 世界坐标 -> 屏幕像素
    def _wx(self, x):
        return self.x + (x - WORLD_XMIN) / (WORLD_XMAX - WORLD_XMIN) * self.width

    def _wy(self, y):
        return self.y + (y - WORLD_YMIN) / (WORLD_YMAX - WORLD_YMIN) * self.height

    def _wr(self, r):
        sx = self.width / (WORLD_XMAX - WORLD_XMIN)
        sy = self.height / (WORLD_YMAX - WORLD_YMIN)
        return r * min(sx, sy)

    def update_params(self, **kw):
        self.params.update(kw)
        self._redraw()

    def _redraw(self, *args):
        self.canvas.clear()
        with self.canvas:
            # 冰面背景
            Color(0.878, 0.941, 1.0, 1)  # #e0f0ff
            Rectangle(pos=self.pos, size=self.size)

            # 刷冰路段高亮（浅黄），直观显示刷到哪条线
            sweep_to_y = self.params.get("sweep_to_y", 0.0)
            if sweep_to_y > 0:
                Color(1.0, 0.95, 0.55, 0.35)
                y0 = self._wy(0)
                yb = self._wy(sweep_to_y)
                Rectangle(pos=(self.x, y0), size=(self.width, yb - y0))

            # 中线（虚线用短线段模拟）
            Color(1, 1, 1, 0.85)
            cx = self._wx(0)
            y0 = self._wy(0)
            y1 = self._wy(80)
            step = (y1 - y0) / 40
            yy = y0
            k = 0
            while yy < y1:
                if k % 2 == 0:
                    Line(points=[cx, yy, cx, min(yy + step, y1)], width=1.5)
                yy += step
                k += 1

            # 前卫线（红）
            Color(1, 0, 0, 1)
            Line(points=[self._wx(-6), self._wy(HOG_Y),
                         self._wx(6), self._wy(HOG_Y)], width=2.5)

            # 大本营（同心圆）
            hcx = self._wx(0)
            hcy = self._wy(HOUSE_Y)
            for r, c in zip(HOUSE_RADII, HOUSE_COLORS):
                pr = self._wr(r)
                Color(*c, 0.9)
                Ellipse(pos=(hcx - pr, hcy - pr), size=(2 * pr, 2 * pr))
                Color(0, 0, 0, 1)
                Line(circle=(hcx, hcy, pr), width=1.2)
            # 大本营中线
            Color(1, 1, 1, 1)
            Line(points=[self._wx(-6), hcy, self._wx(6), hcy], width=2)

            # 冰壶轨迹
            xs, ys = simulate_curling(**self.params)
            pts = []
            for x, y in zip(xs, ys):
                if y > 80:
                    break
                pts.append(self._wx(x))
                pts.append(self._wy(y))
            if len(pts) >= 4:
                Color(0, 0, 1, 1)
                Line(points=pts, width=2.5)


# ---------------------------------------------------------------------------
# 带标签的滑竿行：上排「名称 + 当前值」，下排加高滑竿，手机上便于拖动
# ---------------------------------------------------------------------------
class LabeledSlider(BoxLayout):
    def __init__(self, text, vmin, vmax, vinit, fmt="{:.1f}", on_change=None, **kw):
        super().__init__(orientation="vertical", size_hint_y=None,
                         height=dp(60), padding=(dp(4), dp(2)), spacing=dp(1), **kw)
        self.fmt = fmt
        self.on_change_cb = on_change

        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20))
        self.name_lbl = Label(text=text, halign="left", valign="middle",
                              font_size="14sp", **_lbl_kwargs())
        self.name_lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.val_lbl = Label(text=fmt.format(vinit), halign="right", valign="middle",
                             size_hint_x=None, width=dp(66), font_size="14sp",
                             **_lbl_kwargs())
        self.val_lbl.bind(size=lambda w, s: setattr(w, "text_size", s))
        header.add_widget(self.name_lbl)
        header.add_widget(self.val_lbl)

        self.slider = Slider(min=vmin, max=vmax, value=vinit,
                             size_hint_y=None, height=dp(36),
                             cursor_size=(dp(26), dp(26)))
        self.slider.bind(value=self._on_val)

        self.add_widget(header)
        self.add_widget(self.slider)

    def _on_val(self, inst, val):
        self.val_lbl.text = self.fmt.format(val)
        if self.on_change_cb:
            self.on_change_cb()


# ---------------------------------------------------------------------------
# 一组横向排列的分段选择按钮（用于「刷到哪条线」）
# ---------------------------------------------------------------------------
class SegmentedButtons(BoxLayout):
    def __init__(self, options, on_select=None, init_index=0, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None,
                         height=dp(38), spacing=dp(4), **kw)
        self.on_select = on_select
        self._value = options[init_index][1]
        group = "seg_%d" % id(self)
        for i, (name, val) in enumerate(options):
            b = ToggleButton(text=name, group=group,
                             state="down" if i == init_index else "normal",
                             font_size="13sp")
            _btn_font(b)
            b._val = val
            b.bind(on_press=self._pick)
            self.add_widget(b)

    def _pick(self, btn):
        btn.state = "down"   # 禁止取消选中
        self._value = btn._val
        if self.on_select:
            self.on_select(self._value)

    @property
    def value(self):
        return self._value


# ---------------------------------------------------------------------------
# 可折叠面板：标题按钮 + 内容区，点击标题展开/收起
# ---------------------------------------------------------------------------
class CollapsiblePanel(BoxLayout):
    def __init__(self, title, on_toggle=None, bg=(0.15, 0.15, 0.2, 0.92), **kw):
        super().__init__(orientation="vertical", size_hint_y=None, **kw)
        self.on_toggle = on_toggle
        self._title = title
        self.expanded = False

        self.header_btn = Button(text="▸ " + title, size_hint_y=None, height=dp(40),
                                 font_size="15sp", background_color=(0.2, 0.4, 0.7, 1))
        _btn_font(self.header_btn)
        self.header_btn.bind(on_press=lambda *_: self.toggle())

        self.body = BoxLayout(orientation="vertical", size_hint_y=None,
                              padding=(dp(6), dp(4)), spacing=dp(4))
        self.body.bind(minimum_height=self.body.setter("height"))

        # 半透明背景
        with self.body.canvas.before:
            self._bg_color = Color(*bg)
            self._bg_rect = Rectangle(pos=self.body.pos, size=self.body.size)
        self.body.bind(pos=self._sync_bg, size=self._sync_bg)

        self.add_widget(self.header_btn)
        self._collapse_layout()

    def _sync_bg(self, *a):
        self._bg_rect.pos = self.body.pos
        self._bg_rect.size = self.body.size

    def add_content(self, w):
        self.body.add_widget(w)

    def _collapse_layout(self):
        if self.body.parent:
            self.remove_widget(self.body)
        self.height = self.header_btn.height
        self.header_btn.text = "▸ " + self._title

    def _expand_layout(self):
        if not self.body.parent:
            self.add_widget(self.body)
        self.height = self.header_btn.height + self.body.height
        self.header_btn.text = "▾ " + self._title

    def set_expanded(self, val):
        self.expanded = val
        if val:
            self._expand_layout()
        else:
            self._collapse_layout()

    def toggle(self):
        self.set_expanded(not self.expanded)
        if self.on_toggle:
            self.on_toggle(self)


# ---------------------------------------------------------------------------
# 主应用
# ---------------------------------------------------------------------------
class CurlingApp(App):
    def build(self):
        root = FloatLayout()
        self._root = root

        # ===== 场地：铺满整屏作为背景 =====
        self.track = TrackWidget(size_hint=(1, 1), pos_hint={"x": 0, "y": 0})
        root.add_widget(self.track)

        # ===== 标题 =====
        title = Label(text="冰壶赛道互动演示", size_hint=(1, None), height=dp(34),
                      pos_hint={"x": 0, "top": 1}, font_size="18sp",
                      color=(0.1, 0.1, 0.3, 1), **_lbl_kwargs())
        root.add_widget(title)

        # ===== 模块①：滑行人（常驻底部） =====
        self.s_speed = LabeledSlider("速度（力量）", 1.0, 6.0, 3.5, "{:.1f}", self._update)
        self.s_rot = LabeledSlider("旋转强度", 0.1, 6.0, 2.0, "{:.1f}", self._update)
        self.s_angle = LabeledSlider("初始角度(度)", -12, 12, 0, "{:.0f}", self._update)

        thrower_box = BoxLayout(orientation="vertical", size_hint=(1, None),
                                height=dp(60) * 3 + dp(30),
                                pos_hint={"x": 0, "y": 0}, padding=(dp(6), dp(4)),
                                spacing=dp(2))
        with thrower_box.canvas.before:
            Color(0.93, 0.93, 0.96, 0.95)
            self._tb_rect = Rectangle(pos=thrower_box.pos, size=thrower_box.size)
        thrower_box.bind(pos=lambda *a: setattr(self._tb_rect, "pos", thrower_box.pos),
                         size=lambda *a: setattr(self._tb_rect, "size", thrower_box.size))
        tb_title = Label(text="🥌 滑行人控制", size_hint_y=None, height=dp(24),
                         font_size="14sp", color=(0.1, 0.1, 0.3, 1), **_lbl_kwargs())
        thrower_box.add_widget(tb_title)
        thrower_box.add_widget(self.s_speed)
        thrower_box.add_widget(self.s_rot)
        thrower_box.add_widget(self.s_angle)
        root.add_widget(thrower_box)
        self._thrower_h = thrower_box.height

        # ===== 模块②：冰面面板（左侧，可展开） =====
        self.ice_panel = CollapsiblePanel("❄ 冰面参数", on_toggle=self._on_panel_toggle)
        self.s_fric = LabeledSlider("冰面摩擦", 0.7, 1.5, 1.0, "{:.2f}", self._update)
        self.s_swing = LabeledSlider("冰面摆动性", 0.5, 2.0, 1.0, "{:.1f}", self._update)
        self.ice_panel.add_content(self.s_fric)
        self.ice_panel.add_content(self.s_swing)
        self.ice_panel.size_hint = (0.5, None)
        self.ice_panel.pos_hint = {"x": 0.0, "y": 0.0}   # 位置在 reflow 时更新
        root.add_widget(self.ice_panel)

        # ===== 模块③：扫冰面板（右侧，半透明叠场地，可展开） =====
        self.sweep_panel = CollapsiblePanel("🧹 扫冰控制", on_toggle=self._on_panel_toggle)
        self.s_sweep = LabeledSlider("刷冰强度", 1.0, 3.0, 1.5, "{:.1f}", self._update)
        seg_title = Label(text="刷到哪条线", size_hint_y=None, height=dp(20),
                          halign="left", valign="middle", font_size="13sp",
                          color=(1, 1, 1, 1), **_lbl_kwargs())
        seg_title.bind(size=lambda w, s: setattr(w, "text_size", s))
        self.seg_sweep = SegmentedButtons(SWEEP_TARGETS, on_select=lambda v: self._update())
        self.sweep_panel.add_content(self.s_sweep)
        self.sweep_panel.add_content(seg_title)
        self.sweep_panel.add_content(self.seg_sweep)
        self.sweep_panel.size_hint = (0.5, None)
        self.sweep_panel.pos_hint = {"right": 1.0, "y": 0.0}
        root.add_widget(self.sweep_panel)

        # 面板初始位置随窗口/自身尺寸变化而重新贴到滑行人模块之上
        for p in (self.ice_panel, self.sweep_panel):
            p.bind(height=lambda *a: self._reflow_panels())
        root.bind(size=lambda *a: self._reflow_panels())
        self._reflow_panels()

        self._update()
        return root

    def _reflow_panels(self, *a):
        """把两个可折叠面板贴在滑行人模块的上方。"""
        base = self._thrower_h
        for p in (self.ice_panel, self.sweep_panel):
            p.y = base
        # 左右分置
        self.ice_panel.x = 0
        self.sweep_panel.x = self._root.width - self.sweep_panel.width

    def _on_panel_toggle(self, panel):
        """互斥：展开一个面板时收起另一个。"""
        if panel.expanded:
            other = self.sweep_panel if panel is self.ice_panel else self.ice_panel
            if other.expanded:
                other.set_expanded(False)
        self._reflow_panels()

    def _update(self, *args):
        self.track.update_params(
            speed=self.s_speed.slider.value,
            rotation_rate=self.s_rot.slider.value,
            line_angle=self.s_angle.slider.value,
            sweep_factor=self.s_sweep.slider.value,
            ice_friction=self.s_fric.slider.value,
            ice_swing=self.s_swing.slider.value,
            sweep_to_y=self.seg_sweep.value,
        )


if __name__ == "__main__":
    CurlingApp().run()
