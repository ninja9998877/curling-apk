"""
冰壶赛道互动演示 - Kivy 安卓版
由 matplotlib 版本移植而来，物理逻辑保持一致，改为纯 Python 实现。
入口文件必须命名为 main.py（Buildozer 要求）。
"""
import os
import math

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.graphics import Color, Line, Ellipse, Rectangle
from kivy.core.text import LabelBase

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


# ---------------------------------------------------------------------------
# 物理模拟（与原 matplotlib 版本完全一致，去掉 numpy 依赖）
# ---------------------------------------------------------------------------
def simulate_curling(speed=3.5, rotation_rate=2.0, line_angle=0.0, sweep_factor=1.0,
                     ice_friction=1.0, ice_swing=1.0, time=45.0, dt=0.05):
    n = int(time / dt)
    xs = [0.0] * n
    ys = [0.0] * n
    vx = speed * math.sin(math.radians(line_angle))   # 小横向分量
    vy = speed * math.cos(math.radians(line_angle))   # 主要纵向
    for i in range(1, n):
        speed_current = math.sqrt(vx * vx + vy * vy) + 1e-6
        friction = 0.018 * ice_friction / (sweep_factor ** 0.8)
        vx -= vx * friction * dt
        vy -= vy * friction * dt
        curl_factor = rotation_rate * 0.08 * ice_swing
        perp_x = -vy / speed_current
        perp_y = vx / speed_current
        curl_acc = curl_factor * (1.0 / (speed_current ** 0.3 + 0.5))
        vx += perp_x * curl_acc * dt * 0.8
        vy += perp_y * curl_acc * dt * 0.8
        xs[i] = xs[i - 1] + vx * dt
        ys[i] = ys[i - 1] + vy * dt
    return xs, ys


# ---------------------------------------------------------------------------
# 赛道绘制 Widget
# 世界坐标：x ∈ [-6, 6]（左右宽度，米）, y ∈ [0, 80]（冰道长度，米）
# ---------------------------------------------------------------------------
WORLD_XMIN, WORLD_XMAX = -6.0, 6.0
WORLD_YMIN, WORLD_YMAX = 0.0, 80.0
HOG_Y = 15.0            # 前卫线
HOUSE_Y = 70.0          # 大本营中心
HOUSE_RADII = [6.0, 4.0, 2.5, 0.6]
HOUSE_COLORS = [
    (1.0, 0.8, 0.8),    # 浅红
    (1.0, 1.0, 1.0),    # 白
    (0.0, 0.0, 1.0),    # 蓝
    (1.0, 0.0, 0.0),    # 红心
]


class TrackWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.params = dict(speed=3.5, rotation_rate=2.0, line_angle=0.0,
                           sweep_factor=1.2, ice_friction=1.0, ice_swing=1.0)
        self.bind(pos=self._redraw, size=self._redraw)

    # 世界坐标 -> 屏幕像素
    def _wx(self, x):
        return self.x + (x - WORLD_XMIN) / (WORLD_XMAX - WORLD_XMIN) * self.width

    def _wy(self, y):
        return self.y + (y - WORLD_YMIN) / (WORLD_YMAX - WORLD_YMIN) * self.height

    def _wr(self, r):
        # 半径按横向比例换算（大本营为圆，使用较小的缩放维度保持不过度拉伸）
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

            # 中线（虚线用短线段模拟）
            Color(1, 1, 1, 0.85)
            cx = self._wx(0)
            seg = 6
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
            Line(points=[self._wx(-6), self._wy(HOG_Y), self._wx(6), self._wy(HOG_Y)], width=2.5)

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
# 带标签的滑竿行
# ---------------------------------------------------------------------------
class LabeledSlider(BoxLayout):
    def __init__(self, text, vmin, vmax, vinit, fmt="{:.1f}", on_change=None, **kw):
        super().__init__(orientation="horizontal", size_hint_y=None, height=48, **kw)
        self.fmt = fmt
        self.on_change_cb = on_change
        self.name_lbl = Label(text=text, size_hint_x=0.32, **_lbl_kwargs())
        self.slider = Slider(min=vmin, max=vmax, value=vinit, size_hint_x=0.5)
        self.val_lbl = Label(text=fmt.format(vinit), size_hint_x=0.18, **_lbl_kwargs())
        self.slider.bind(value=self._on_val)
        self.add_widget(self.name_lbl)
        self.add_widget(self.slider)
        self.add_widget(self.val_lbl)

    def _on_val(self, inst, val):
        self.val_lbl.text = self.fmt.format(val)
        if self.on_change_cb:
            self.on_change_cb()


# ---------------------------------------------------------------------------
# 主应用
# ---------------------------------------------------------------------------
class CurlingApp(App):
    def build(self):
        root = BoxLayout(orientation="vertical")

        title = Label(text="真实冰壶赛道互动演示", size_hint_y=None, height=44,
                      font_size="20sp", **_lbl_kwargs())
        root.add_widget(title)

        self.track = TrackWidget(size_hint_y=0.62)
        root.add_widget(self.track)

        controls = BoxLayout(orientation="vertical", size_hint_y=None, height=48 * 6,
                             padding=6, spacing=2)

        self.s_speed = LabeledSlider("速度", 1.0, 6.0, 3.5, "{:.1f}", self._update)
        self.s_rot = LabeledSlider("旋转强度", 0.1, 6.0, 2.0, "{:.1f}", self._update)
        self.s_angle = LabeledSlider("初始角度(度)", -12, 12, 0, "{:.0f}", self._update)
        self.s_sweep = LabeledSlider("刷冰强度", 0.5, 2.5, 1.2, "{:.1f}", self._update)
        self.s_fric = LabeledSlider("冰面摩擦", 0.7, 1.5, 1.0, "{:.2f}", self._update)
        self.s_swing = LabeledSlider("冰面摆动性", 0.5, 2.0, 1.0, "{:.1f}", self._update)

        for s in (self.s_speed, self.s_rot, self.s_angle,
                  self.s_sweep, self.s_fric, self.s_swing):
            controls.add_widget(s)
        root.add_widget(controls)

        self._update()
        return root

    def _update(self, *args):
        self.track.update_params(
            speed=self.s_speed.slider.value,
            rotation_rate=self.s_rot.slider.value,
            line_angle=self.s_angle.slider.value,
            sweep_factor=self.s_sweep.slider.value,
            ice_friction=self.s_fric.slider.value,
            ice_swing=self.s_swing.slider.value,
        )


if __name__ == "__main__":
    CurlingApp().run()
