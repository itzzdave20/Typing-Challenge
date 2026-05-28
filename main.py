import kivy.app
import kivy.uix.label
import kivy.uix.textinput
import kivy.uix.boxlayout
import kivy.uix.button
import kivy.uix.screenmanager
import kivy.uix.scrollview
import kivy.uix.widget
import kivy.uix.gridlayout
import kivy.uix.anchorlayout
import kivy.clock
import kivy.core.window
import kivy.utils
import kivy.graphics
import kivy.animation
import kivy.core.audio
import kivy.storage.jsonstore
import kivy.resources
import hashlib

kivy.core.window.Window.clearcolor = (0.05, 0.05, 0.1, 1)  # dark navy background
# iOS/mobile: keep the active text input visible when the software keyboard appears.
try:
    kivy.core.window.Window.softinput_mode = "below_target"
except Exception:
    pass

# Responsive UI scaling (bigger on laptop/PC, still fits phones/tablets).
BASE_BTN_H = 40
BASE_BTN_FS = 17


def ui_scale():
    w, h = kivy.core.window.Window.size
    w = w or 800
    h = h or 600
    # Reference: 900x700 ≈ 1.0
    s = min(w / 900.0, h / 700.0)
    return max(0.90, min(1.85, s))


def ui_btn_h():
    return int(round(BASE_BTN_H * ui_scale()))


def ui_btn_fs():
    return int(round(BASE_BTN_FS * ui_scale()))


def ui_col_w(layout_width):
    s = ui_scale()
    max_w = int(round(640 * s))
    min_w = int(round(260 * s))
    return min(max_w, max(min_w, int(layout_width * 0.62)))


def ui_card_w():
    """Convenience: responsive card width based on current window width."""
    return ui_col_w(kivy.core.window.Window.width or 800)


def _draw_rounded_card(widget, fill_instr, line_instr, radius=18):
    """Graphics must use widget.pos (same as GameButton), not (0,0), or the panel draws at the wrong place."""

    def _draw(*_a):
        x, y = widget.pos
        w, h = max(1, widget.width), max(1, widget.height)
        fill_instr.pos = (x, y)
        fill_instr.size = (w, h)
        line_instr.rounded_rectangle = (x, y, w, h, radius)

    widget.bind(pos=_draw, size=_draw)
    _draw()


def apply_rounded_card_backing(widget, radius=18, line_width=1.2):
    """Dark navy rounded panel behind labels/buttons (canvas.before, matches menu card look)."""
    with widget.canvas.before:
        kivy.graphics.Color(0.06, 0.08, 0.13, 0.94)
        fill = kivy.graphics.RoundedRectangle(pos=widget.pos, size=widget.size, radius=[radius] * 4)
        kivy.graphics.Color(0.62, 0.76, 0.92, 0.38)
        line = kivy.graphics.Line(rounded_rectangle=(0, 0, 0, 0, radius), width=line_width)
    _draw_rounded_card(widget, fill, line, radius)

def _users_store_path():
    app = kivy.app.App.get_running_app()
    base = getattr(app, "user_data_dir", ".") if app else "."
    return f"{base}/users.json"

def _hash_password(password: str) -> str:
    # Local demo only: SHA-256 hash (no salt). For class demo purposes.
    if password is None:
        password = ""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def _load_users():
    try:
        store = kivy.storage.jsonstore.JsonStore(_users_store_path())
        if store.exists("users"):
            data = store.get("users").get("data", {})
            return data if isinstance(data, dict) else {}
        return {}
    except Exception:
        return {}

def _save_users(users: dict):
    try:
        store = kivy.storage.jsonstore.JsonStore(_users_store_path())
        store.put("users", data=users)
    except Exception:
        pass


DEFAULT_WORDS_BY_CATEGORY = {
    "Coding": [
        "python", "kivy", "function", "variable", "compile", "debug", "syntax", "algorithm", "iterate", "recursion",
        "dictionary", "exception", "package", "dependency", "terminal", "keyboard", "performance", "refactor",
    ],
    "Common": [
        "speed", "typing", "game", "challenge", "accuracy", "practice", "focus", "energy", "future", "improve",
        "moment", "friend", "window", "planet", "summer", "winter", "simple", "random",
    ],
    "Animals": [
        "tiger", "elephant", "giraffe", "dolphin", "penguin", "rabbit", "hamster", "falcon", "octopus", "panther",
        "leopard", "kangaroo", "butterfly", "crocodile", "squirrel", "flamingo", "hedgehog", "chameleon",
    ],
    "Nature": [
        "forest", "river", "mountain", "ocean", "valley", "meadow", "canyon", "volcano", "waterfall", "glacier",
        "sunset", "thunder", "rainbow", "blizzard", "hurricane", "earthquake", "wildflower", "bamboo",
    ],
    "Food": [
        "pizza", "burger", "sushi", "pasta", "salad", "sandwich", "pancake", "waffle", "avocado", "broccoli",
        "chocolate", "vanilla", "cinnamon", "honey", "caramel", "marshmallow", "watermelon", "blueberry",
    ],
    "Sports": [
        "basketball", "football", "soccer", "tennis", "volleyball", "baseball", "hockey", "swimming", "cycling",
        "marathon", "sprint", "goalkeeper", "championship", "tournament", "medal", "stadium", "referee",
    ],
    "Science": [
        "physics", "chemistry", "biology", "astronomy", "experiment", "molecule", "electron", "gravity",
        "telescope", "microscope", "hypothesis", "theory", "discovery", "laboratory", "radiation", "quantum",
    ],
    "Travel": [
        "airport", "passport", "luggage", "destination", "adventure", "backpack", "cruise", "resort",
        "explore", "journey", "voyage", "itinerary", "landmark", "museum", "hostel", "vacation",
    ],
    "Music": [
        "guitar", "piano", "violin", "drummer", "symphony", "melody", "rhythm", "concert", "orchestra",
        "harmony", "chorus", "album", "playlist", "microphone", "amplifier", "acoustic", "rehearsal",
    ],
    "School": [
        "homework", "textbook", "notebook", "pencil", "classroom", "semester", "graduation", "assignment",
        "professor", "library", "calculator", "schedule", "deadline", "presentation", "research", "campus",
    ],
}

def load_words_by_category():
    # Kivy-only version: use built-in categories (no stdlib imports / file IO).
    return DEFAULT_WORDS_BY_CATEGORY

# ---------- Styled Factories ----------
def styled_label(text, color_hex, font_size=24):
    """Centered title/body label: `halign` needs `text_size` width (bound to widget width)."""
    lbl = kivy.uix.label.Label(
        text=text,
        font_size=font_size,
        color=kivy.utils.get_color_from_hex(color_hex),
        bold=True,
        halign="center",
        valign="middle",
        markup=True,
        size_hint_y=None,
        text_size=(None, None),
    )

    def _fit(*_a):
        w = int(lbl.width) if lbl.width else 400
        lbl.text_size = (max(1, w), None)
        lbl.height = lbl.texture_size[1] + 6

    lbl.bind(width=_fit, texture_size=_fit, text=_fit)
    _fit()
    return lbl


def hud_line_label(text, color_hex, font_size=17):
    """HUD stat line: explicit height from text (avoids BoxLayout overlap when size_hint_y=1)."""
    lbl = kivy.uix.label.Label(
        text=text,
        font_size=font_size,
        color=kivy.utils.get_color_from_hex(color_hex),
        bold=True,
        halign="center",
        valign="middle",
        markup=True,
        size_hint_y=None,
        text_size=(None, None),
    )

    def _fit(*_a):
        tw = max(1, int(lbl.width) - 4) if lbl.width else 220
        lbl.text_size = (tw, None)
        lbl.height = lbl.texture_size[1] + 6

    lbl.bind(width=_fit, texture_size=_fit)
    return lbl

def add_background(widget, color_hex="#0B0F1A", center_panel=True):
    def _lcg_next(state: int) -> int:
        return (1103515245 * state + 12345) % 2147483647

    def _rand01(state: int):
        state = _lcg_next(state)
        return state, (state / 2147483647.0)

    seed = (id(widget) * 2654435761) % 2147483647

    with widget.canvas.before:
        # Base fill
        kivy.graphics.Color(*kivy.utils.get_color_from_hex(color_hex))
        base = kivy.graphics.Rectangle(pos=widget.pos, size=widget.size)

        # Gradient overlay (stacked translucent bands)
        grad_rects = []
        for i in range(10):
            t = i / 9.0
            # navy -> purple-ish
            r = 0.04 + (0.18 - 0.04) * t
            g = 0.05 + (0.07 - 0.05) * t
            b = 0.10 + (0.22 - 0.10) * t
            a = 0.18
            kivy.graphics.Color(r, g, b, a)
            rr = kivy.graphics.Rectangle(pos=widget.pos, size=widget.size)
            grad_rects.append((i, rr))

        # Soft blobs (big low-opacity circles)
        blobs = []
        for _ in range(3):
            seed, x01 = _rand01(seed)
            seed, y01 = _rand01(seed)
            seed, s01 = _rand01(seed)
            seed, c01 = _rand01(seed)
            size = 220 + int(260 * s01)
            cx = x01
            cy = y01
            # purple/blue palette
            r = 0.35 + 0.25 * c01
            g = 0.15 + 0.20 * (1 - c01)
            b = 0.55 + 0.35 * c01
            kivy.graphics.Color(r, g, b, 0.055)
            e = kivy.graphics.Ellipse(pos=(widget.x, widget.y), size=(size, size))
            blobs.append((cx, cy, size, e))

        # Stars (tiny dots)
        stars = []
        for _ in range(35):
            seed, x01 = _rand01(seed)
            seed, y01 = _rand01(seed)
            seed, s01 = _rand01(seed)
            radius = 1 + int(2 * s01)
            alpha = 0.25 + 0.35 * s01
            kivy.graphics.Color(1, 1, 1, alpha)
            e = kivy.graphics.Ellipse(pos=(widget.x, widget.y), size=(radius * 2, radius * 2))
            stars.append((x01, y01, radius, e))

        # Grid overlay (faint lines)
        kivy.graphics.Color(0.2, 0.75, 0.9, 0.06)
        grid_lines = []
        for _ in range(12):
            ln = kivy.graphics.Line(points=[0, 0, 0, 0], width=1)
            grid_lines.append(("v", ln))
        for _ in range(8):
            ln = kivy.graphics.Line(points=[0, 0, 0, 0], width=1)
            grid_lines.append(("h", ln))

        # Center panel (readability "card"); optional — screens with their own card set False.
        panel = None
        panel_border = None
        if center_panel:
            kivy.graphics.Color(0.08, 0.10, 0.16, 0.78)
            panel = kivy.graphics.RoundedRectangle(pos=(widget.x, widget.y), size=(100, 100), radius=[18])
            kivy.graphics.Color(0.45, 0.75, 0.95, 0.10)
            panel_border = kivy.graphics.Line(rounded_rectangle=[0, 0, 100, 100, 18], width=1.2)

    def _update(_instance, _value):
        x, y = widget.pos
        w, h = widget.size
        base.pos = (x, y)
        base.size = (w, h)

        # Gradient: stack horizontal bands from top->bottom
        for i, rr in grad_rects:
            band_h = h / 10.0 if h else 0
            rr.pos = (x, y + (9 - i) * band_h)
            rr.size = (w, band_h + 1)

        # Blobs and stars anchored in normalized coordinates
        for cx, cy, size, e in blobs:
            px = x + (w - size) * cx
            py = y + (h - size) * cy
            e.pos = (px, py)
            e.size = (size, size)

        for sx, sy, radius, e in stars:
            px = x + (w * sx) - radius
            py = y + (h * sy) - radius
            e.pos = (px, py)
            e.size = (radius * 2, radius * 2)

        # Grid lines
        cols = 12
        rows = 8
        idx = 0
        for _ in range(cols):
            t = idx / max(1, cols - 1)
            gx = x + w * t
            kind, ln = grid_lines[idx]
            ln.points = [gx, y, gx, y + h]
            idx += 1
        for r in range(rows):
            t = r / max(1, rows - 1)
            gy = y + h * t
            kind, ln = grid_lines[idx]
            ln.points = [x, gy, x + w, gy]
            idx += 1

        if center_panel and panel is not None:
            pw = min(520, max(280, w * 0.86))
            ph = min(650, max(320, h * 0.86))
            px = x + (w - pw) / 2
            py = y + (h - ph) / 2
            panel.pos = (px, py)
            panel.size = (pw, ph)
            panel_border.rounded_rectangle = [px, py, pw, ph, 18]

    widget.bind(pos=_update, size=_update)
    _update(widget, None)
    return base

def safe_load_sound(filename):
    try:
        resolved = kivy.resources.resource_find(f"sounds/{filename}") or kivy.resources.resource_find(filename)
        if resolved:
            return kivy.core.audio.SoundLoader.load(resolved)
    except Exception:
        return None
    return None


_ui_click_sound_cache = None


def _get_ui_click_sound():
    global _ui_click_sound_cache
    if _ui_click_sound_cache is None:
        _ui_click_sound_cache = safe_load_sound("click.wav") or safe_load_sound("ui_click.wav")
    return _ui_click_sound_cache


class GameButton(kivy.uix.button.Button):
    """Rounded, hover-aware button with optional UI click sound."""

    def __init__(self, text="", color_hex="#FFFFFF", font_size=22, corner_radius=14, **kwargs):
        kwargs.setdefault("size_hint", (1, None))
        kwargs.setdefault("height", 60)
        super().__init__(
            text=text,
            font_size=font_size,
            background_normal="",
            background_down="",
            background_color=(0, 0, 0, 0),
            **kwargs,
        )
        self._corner_radius = corner_radius
        self._hovering = False
        self._hover_bound = False
        base = list(kivy.utils.get_color_from_hex(color_hex))
        if len(base) == 3:
            base.append(1.0)
        self._base_rgba = base

        font_path = kivy.resources.resource_find("fonts/ui.ttf") or kivy.resources.resource_find(
            "fonts/Roboto-Medium.ttf"
        )
        if font_path:
            self.font_name = font_path

        br, bg, bb = self._base_rgba[0], self._base_rgba[1], self._base_rgba[2]
        lum = 0.299 * br + 0.587 * bg + 0.114 * bb
        self.color = (0.12, 0.12, 0.14, 1) if lum > 0.72 else (1, 1, 1, 1)

        with self.canvas.before:
            self._bg_color_instr = kivy.graphics.Color(*self._base_rgba)
            self._bg_rect = kivy.graphics.RoundedRectangle(
                pos=self.pos, size=self.size, radius=[corner_radius] * 4
            )
            kivy.graphics.Color(1, 1, 1, 0.2)
            self._border_line = kivy.graphics.Line(rounded_rectangle=(0, 0, 0, 0, corner_radius), width=1.1)

        self.bind(pos=self._draw_bg_geom, size=self._draw_bg_geom)
        self.bind(state=self._on_state_visual)
        self.bind(disabled=self._on_state_visual)

        self._draw_bg_geom()
        self._apply_bg_color()
        self.fbind("parent", self._on_parent_changed)

    def _on_parent_changed(self, _instance, parent):
        plat = kivy.utils.platform
        mobile = plat in ("android", "ios")
        if parent is None:
            if self._hover_bound:
                try:
                    kivy.core.window.Window.unbind(mouse_pos=self._on_window_mouse_pos)
                except Exception:
                    pass
                self._hover_bound = False
            self._hovering = False
            self._apply_bg_color()
        elif not mobile and not self._hover_bound:
            kivy.core.window.Window.bind(mouse_pos=self._on_window_mouse_pos)
            self._hover_bound = True

    def _play_click_sound(self, *_args):
        s = _get_ui_click_sound()
        if s:
            s.play()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.disabled:
            self._play_click_sound()
        return super().on_touch_down(touch)

    def _on_window_mouse_pos(self, *_args):
        if not self.get_root_window():
            return
        if self.disabled or self.opacity < 0.01:
            if self._hovering:
                self._hovering = False
                self._apply_bg_color()
            return
        pos = kivy.core.window.Window.mouse_pos
        inside = self.collide_point(*self.to_widget(*pos))
        if inside != self._hovering:
            self._hovering = inside
            self._apply_bg_color()

    def _draw_bg_geom(self, *_args):
        x, y = self.pos
        w, h = self.size
        r = self._corner_radius
        self._bg_rect.pos = (x, y)
        self._bg_rect.size = (w, h)
        self._border_line.rounded_rectangle = (x, y, w, h, r)

    def _on_state_visual(self, *_args):
        self._apply_bg_color()

    def _apply_bg_color(self):
        b = self._base_rgba
        if self.disabled:
            rgba = (
                min(1.0, b[0] * 0.4),
                min(1.0, b[1] * 0.4),
                min(1.0, b[2] * 0.4),
                b[3] * 0.65,
            )
        elif self.state == "down":
            rgba = (
                min(1.0, b[0] * 0.72),
                min(1.0, b[1] * 0.72),
                min(1.0, b[2] * 0.72),
                b[3],
            )
        elif self._hovering:
            rgba = (
                min(1.0, b[0] * 1.12),
                min(1.0, b[1] * 1.12),
                min(1.0, b[2] * 1.12),
                b[3],
            )
        else:
            rgba = tuple(b)
        self._bg_color_instr.rgba = rgba


def styled_button(text, color_hex, font_size=22, **kwargs):
    return GameButton(text=text, color_hex=color_hex, font_size=font_size, **kwargs)


class CategoryPicker(kivy.uix.boxlayout.BoxLayout):
    """Inline expand/collapse category list (reliable on all platforms; avoids DropDown quirks)."""

    def __init__(self, categories, initial, on_change=None, **kwargs):
        kwargs.setdefault("orientation", "vertical")
        kwargs.setdefault("spacing", 8)
        kwargs.setdefault("size_hint", (1, None))
        kwargs.setdefault("padding", (0, 0, 0, 0))
        super().__init__(**kwargs)
        self._categories = list(categories)
        self.selected_category = initial
        self._on_change = on_change
        self._expanded = False

        # List viewport: scroll happens only here, not the whole setup screen.
        self._panel_max_h = min(280, 8 + 48 * max(1, len(self._categories)))

        self._main_btn = GameButton(
            text=self._format_main_label(initial, opened=False),
            color_hex="#5C4D9A",
            font_size=20,
            height=62,
            corner_radius=14,
        )
        self._main_btn.bind(on_release=self._toggle_expand)
        self.add_widget(self._main_btn)

        self._inner = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=6,
            padding=(6, 8, 6, 8),
            size_hint_y=None,
        )
        self._inner.bind(minimum_height=self._set_inner_height)

        with self._inner.canvas.before:
            kivy.graphics.Color(0.09, 0.11, 0.18, 0.96)
            self._panel_bg = kivy.graphics.RoundedRectangle(
                pos=self._inner.pos, size=self._inner.size, radius=[14, 14, 14, 14]
            )
            kivy.graphics.Color(0.45, 0.75, 0.95, 0.16)
            self._panel_line = kivy.graphics.Line(
                rounded_rectangle=(0, 0, 0, 0, 14), width=1.1
            )
        self._inner.bind(pos=self._draw_panel, size=self._draw_panel)

        for cat in self._categories:
            row = GameButton(
                text=cat,
                color_hex="#3D4F75",
                font_size=19,
                height=46,
                corner_radius=10,
            )
            row.bind(on_release=lambda btn, c=cat: self._choose(c))
            self._inner.add_widget(row)

        self._scroll = kivy.uix.scrollview.ScrollView(
            size_hint=(1, None),
            height=0,
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=6,
            bar_color=(0.45, 0.72, 0.95, 0.55),
            scroll_type=["bars", "content"],
            scroll_wheel_distance=48,
        )
        self._scroll.add_widget(self._inner)

        self._main_btn.bind(height=self._sync_outer_height)
        self._sync_outer_height()

    def _set_inner_height(self, _inst, val):
        self._inner.height = val
        self._draw_panel()

    def _draw_panel(self, *_args):
        x, y = self._inner.pos
        w, h = self._inner.size
        self._panel_bg.pos = (x, y)
        self._panel_bg.size = (max(1, w), max(1, h))
        self._panel_line.rounded_rectangle = (x, y, w, h, 14)

    def _sync_outer_height(self, *_args):
        h = self._main_btn.height
        if self._scroll.parent is not None:
            h += self.spacing + self._scroll.height
        self.height = h

    def _format_main_label(self, cat, opened):
        if opened:
            return f"{cat}  |  tap to close list"
        return f"{cat}  |  tap to change topic"

    def _toggle_expand(self, *_args):
        self._expanded = not self._expanded
        if self._expanded:
            self._scroll.height = self._panel_max_h
            if self._scroll.parent is None:
                self.add_widget(self._scroll)
            kivy.clock.Clock.schedule_once(lambda _dt: self._finish_expand(), 0)

        else:
            if self._scroll.parent is not None:
                self.remove_widget(self._scroll)
            self._scroll.height = 0
        self._main_btn.text = self._format_main_label(self.selected_category, opened=self._expanded)
        self._sync_outer_height()

    def _finish_expand(self):
        if not self._expanded:
            return
        self._inner.height = max(self._inner.minimum_height, self._inner.height)
        self._draw_panel()
        self._sync_outer_height()

    def _collapse(self):
        if self._expanded:
            self._expanded = False
            if self._scroll.parent is not None:
                self.remove_widget(self._scroll)
            self._scroll.height = 0
            self._main_btn.text = self._format_main_label(self.selected_category, opened=False)
            self._sync_outer_height()

    def _choose(self, cat, *_args):
        self.selected_category = cat
        self._main_btn.text = self._format_main_label(cat, opened=False)
        if self._on_change:
            self._on_change(cat)
        self._collapse()

# ---------------- GAME SCREEN ----------------
class GameScreen(kivy.uix.screenmanager.Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = kivy.uix.boxlayout.BoxLayout(orientation="vertical", padding=[16, 14, 16, 14])
        # Game screen already uses fitted cards (play/HUD/actions); disable the big fixed center panel.
        add_background(self.layout, "#0B0F1A", center_panel=False)

        self._center_column = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint_y=None,
        )
        self.layout.add_widget(kivy.uix.widget.Widget(size_hint_y=1))
        self.layout.add_widget(self._center_column)
        self.layout.add_widget(kivy.uix.widget.Widget(size_hint_y=1))

        self.word_label = kivy.uix.label.Label(
            text="Press Start!",
            font_size=34,
            color=kivy.utils.get_color_from_hex("#FFD700"),
            bold=True,
            halign="center",
            valign="middle",
            markup=True,
            size_hint_y=None,
        )

        self.game_over_stats_label = kivy.uix.label.Label(
            text="",
            font_size=24,
            markup=True,
            bold=True,
            halign="center",
            valign="middle",
            color=kivy.utils.get_color_from_hex("#E8F8E8"),
            size_hint=(1, None),
            height=0,
            opacity=0,
            line_height=1.15,
            disabled=True,
        )
        self.game_over_stats_label._saved_size_hint = (1, None)
        self.game_over_stats_label._saved_height = 88

        self.input = kivy.uix.textinput.TextInput(
            multiline=False,
            font_size=26,
            size_hint=(1, None),
            height=48,
            halign="center",
            background_color=(0.18, 0.18, 0.22, 1),
            foreground_color=(1, 1, 1, 1),
            text_validate_unfocus=False,
            padding=[12, 10, 12, 8],
        )
        self.input.bind(on_text_validate=self.check_word)

        self._play_col = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=8,
            padding=[14, 14, 14, 14],
            size_hint_x=None,
            size_hint_y=None,
            width=300,
        )
        apply_rounded_card_backing(self._play_col, radius=16)
        self._play_row = kivy.uix.boxlayout.BoxLayout(orientation="horizontal", size_hint_y=None, spacing=0)
        self._play_row.add_widget(kivy.uix.widget.Widget())
        self._play_row.add_widget(self._play_col)
        self._play_row.add_widget(kivy.uix.widget.Widget())
        self._play_col.add_widget(self.word_label)
        self._play_col.add_widget(self.game_over_stats_label)
        self._play_col.add_widget(self.input)
        self._center_column.add_widget(self._play_row)

        self.hud_row = kivy.uix.boxlayout.BoxLayout(orientation="horizontal", size_hint_y=None, spacing=0)
        self.hud_row.add_widget(kivy.uix.widget.Widget())
        self._hud_card = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=6,
            padding=[14, 12, 14, 12],
            size_hint_x=None,
            width=300,
        )
        apply_rounded_card_backing(self._hud_card, radius=14, line_width=1.0)

        self.score_label = hud_line_label("Score: 0 | Accuracy: 100%", "#00FF00", 19)
        self.streak_label = hud_line_label("Streak: 0 | Mult: x1.0", "#87CEFA", 17)
        self.lives_label = hud_line_label("Lives: 3", "#FFB6C1", 17)
        self.timer_label = hud_line_label("Time: 30 | Word: 0", "#FF4500", 18)
        self.powerup_label = hud_line_label("Power-up: None", "#DDA0DD", 16)
        self._hud_card.add_widget(self.score_label)
        self._hud_card.add_widget(self.streak_label)
        self._hud_card.add_widget(self.lives_label)
        self._hud_card.add_widget(self.timer_label)
        self._hud_card.add_widget(self.powerup_label)
        self.hud_row.add_widget(self._hud_card)
        self.hud_row.add_widget(kivy.uix.widget.Widget())

        def _sync_hud(*_a):
            self._hud_card.width = ui_col_w(self.layout.width)
            self._hud_card.height = self._hud_card.minimum_height
            self.hud_row.height = self._hud_card.height

        self._hud_card.bind(minimum_height=lambda *_x: _sync_hud())
        self.layout.bind(width=_sync_hud)
        _sync_hud()
        self._center_column.add_widget(self.hud_row)

        self.pause_button = styled_button("Pause", "#D4AF37", ui_btn_fs(), height=ui_btn_h())
        self.pause_button.bind(on_press=self.toggle_pause)
        self.skip_button = styled_button("Skip (0)", "#7B68A6", ui_btn_fs(), height=ui_btn_h())
        self.skip_button.bind(on_press=self.skip_word)
        self.restart_button = styled_button("Restart", "#2d9d4f", ui_btn_fs(), height=ui_btn_h())
        self.restart_button.bind(on_press=self.restart_game)
        self.back_button = styled_button("Menu", "#3d7eae", ui_btn_fs(), height=ui_btn_h())
        self.back_button.bind(on_press=self.go_back)

        self._action_grid = kivy.uix.gridlayout.GridLayout(
            cols=2,
            spacing=[10, 8],
            size_hint=(None, None),
            width=300,
            height=2 * ui_btn_h() + 8,
        )
        self._action_grid.add_widget(self.pause_button)
        self._action_grid.add_widget(self.skip_button)
        self._action_grid.add_widget(self.restart_button)
        self._action_grid.add_widget(self.back_button)

        self._action_shell = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            padding=[10, 10, 10, 10],
            size_hint=(None, None),
        )
        apply_rounded_card_backing(self._action_shell, radius=16)
        self._action_shell.add_widget(self._action_grid)

        self.action_row = kivy.uix.boxlayout.BoxLayout(orientation="horizontal", size_hint_y=None, spacing=0)
        self.action_row.add_widget(kivy.uix.widget.Widget())

        def _sync_actions(*_a):
            w = ui_col_w(self.layout.width)
            self._action_grid.width = w
            self._action_shell.width = w + 20
            self._action_shell.height = self._action_grid.height + 20
            self.action_row.height = self._action_shell.height

        self.layout.bind(width=_sync_actions)
        _sync_actions()
        self.action_row.add_widget(self._action_shell)
        self.action_row.add_widget(kivy.uix.widget.Widget())
        self._center_column.add_widget(self.action_row)

        self.layout.bind(width=self._sync_play_row)
        self.word_label.bind(texture_size=self._sync_play_row)
        self.word_label.bind(text=self._sync_play_row)
        kivy.clock.Clock.schedule_once(lambda _dt: self._sync_play_row(), 0)

        self.add_widget(self.layout)

        self.score = 0
        self.attempts = 0
        self.correct_attempts = 0
        self.time_left = 30
        self.word_index = 0
        self.difficulty = "Medium"
        self.category = "Common"
        self.words = []

        self.lives = 3
        self.streak = 0
        self.best_streak = 0
        self.multiplier = 1.0

        self.paused = False
        self.game_over = False

        self.word_time_left = 0
        self.word_time_limit = 0

        self.skip_tokens = 0
        self.double_points_words_left = 0
        self.next_powerup_at = 5
        self._rng_state = 123456789
        self._current_word = None
        self.shield_charges = 0

        self._tick_ev = None

        self.sound_correct = safe_load_sound("correct.wav")
        self.sound_wrong = safe_load_sound("wrong.wav")
        self.sound_powerup = safe_load_sound("powerup.wav")
        self.sound_gameover = safe_load_sound("gameover.wav")

    def _sync_play_row(self, *_a):
        """Keep word + input column width aligned with HUD/actions; size word label from text."""
        w = ui_col_w(self.layout.width)
        self._play_col.width = w
        tw = max(1, int(w) - 8)
        self.word_label.text_size = (tw, None)
        self.word_label.height = max(self.word_label.texture_size[1] + 12, 36)
        self.game_over_stats_label.text_size = (tw, None)
        self._play_col.height = self._play_col.minimum_height
        self._play_row.height = self._play_col.height

    def _refocus_input(self, *_args):
        if self.game_over or self.paused or self.input.disabled:
            return
        self.input.focus = True

    def _schedule_refocus_input(self):
        kivy.clock.Clock.schedule_once(self._refocus_input, 0)

    def _set_widget_visible(self, widget, visible: bool):
        widget.disabled = not visible
        widget.opacity = 1 if visible else 0
        if hasattr(widget, "_saved_size_hint"):
            pass
        if not hasattr(widget, "_saved_size_hint"):
            widget._saved_size_hint = widget.size_hint
            widget._saved_height = widget.height
        if visible:
            widget.size_hint = widget._saved_size_hint
            widget.height = widget._saved_height
        else:
            widget.size_hint = (1, None)
            widget.height = 0
        if widget is self.skip_button and visible:
            self._sync_skip_button_state()
        kivy.clock.Clock.schedule_once(lambda _dt: self._sync_play_row(), 0)

    def _sync_skip_button_state(self):
        w = self.skip_button
        if w.opacity < 0.5 or w.height < 2:
            return
        w.disabled = self.skip_tokens <= 0 or self.paused or self.game_over

    def _show_only_game_over(self):
        # Hide everything except the main word label.
        self._set_widget_visible(self.input, False)
        self._set_widget_visible(self.hud_row, False)
        self._set_widget_visible(self.action_row, False)
        self._set_widget_visible(self.word_label, True)
        self.word_label.text = "[color=#FF0000][b]Game Over![/b][/color]"
        acc = self._final_accuracy_for_display()
        self.game_over_stats_label.text = (
            f"[color=#7CFC00][b]Final score: {self.score}[/b][/color]\n"
            f"[color=#ADD8E6]Accuracy: {acc:.1f}%[/color]"
        )
        self._set_widget_visible(self.game_over_stats_label, True)
        self.input.text = ""
        self.input.focus = False

    def _show_game_ui(self):
        self._set_widget_visible(self.game_over_stats_label, False)
        self._set_widget_visible(self.input, True)
        self._set_widget_visible(self.hud_row, True)
        self._set_widget_visible(self.action_row, True)
        self._set_widget_visible(self.word_label, True)

    def _final_accuracy_for_display(self):
        """
        Accuracy displayed on game-over and saved to leaderboard must use the same rule.
        If the global timer ended while a word is still active, count that active word
        as one additional missed attempt.
        """
        attempts = self.attempts
        if self.time_left <= 0 and self.word_time_left > 0:
            attempts += 1
        if attempts <= 0:
            return 0.0
        return (self.correct_attempts / attempts) * 100.0

    def start_game(self, difficulty="Medium", category="Common"):
        self._show_game_ui()
        self.game_over = False
        self.paused = False
        self.pause_button.text = "Pause"

        self.score = 0
        self.attempts = 0
        self.correct_attempts = 0
        self.word_index = 0
        self.difficulty = difficulty
        self.category = category

        words_by_cat = load_words_by_category()
        self.words = list(words_by_cat.get(category) or [])
        if not self.words:
            # Fallback to any available category.
            self.words = list(next(iter(words_by_cat.values())))
            self.category = next(iter(words_by_cat.keys()))

        # Deterministic seed (avoid importing Python stdlib modules).
        self._rng_state = 1103515245 + (len(self.words) * 12345) + (self.time_left * 97)

        if difficulty == "Easy":
            self.time_left = 40
            self.word_time_limit = 7
            self.lives = 5
        elif difficulty == "Hard":
            self.time_left = 20
            self.word_time_limit = 4
            self.lives = 3
        else:
            self.time_left = 30
            self.word_time_limit = 5
            self.lives = 4

        self.word_time_left = self.word_time_limit

        self.streak = 0
        self.best_streak = 0
        self.multiplier = 1.0
        self.skip_tokens = 0
        self.double_points_words_left = 0
        self.next_powerup_at = 5
        self.powerup_label.text = "Power-up: None"
        self.skip_button.text = f"Skip ({self.skip_tokens})"

        self.next_word()
        if self._tick_ev is not None:
            kivy.clock.Clock.unschedule(self._tick_ev)
        self._tick_ev = kivy.clock.Clock.schedule_interval(self.update_timer, 1)
        self._schedule_refocus_input()
        self._refresh_hud()

    def next_word(self):
        if not self.words:
            return
        self._current_word = self._pick_word()
        self.word_label.text = self._current_word
        self.word_index += 1
        self.word_time_left = self.word_time_limit
        self._schedule_refocus_input()

    def check_word(self, instance):
        if self.game_over or self.paused:
            self.input.text = ""
            return
        self.attempts += 1
        typed = self.input.text.strip().lower()
        target = self.word_label.text.lower()
        correct = typed == target

        if correct:
            self.correct_attempts += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            self.multiplier = 1.0 + min(1.0, self.streak * 0.05)  # cap at x2.0
            base = 1
            if self.double_points_words_left > 0:
                base *= 2
                self.double_points_words_left -= 1
            # Perfect bonus if you finish the word with plenty of time left.
            bonus = 1 if self.word_time_left > (self.word_time_limit * 0.6) else 0
            gained = int(round(base * self.multiplier)) + bonus
            self.score += max(1, gained)
            self._feedback(correct=True)
            if self.score >= self.next_powerup_at:
                self.next_powerup_at += 5
                self._grant_powerup()
        else:
            self.streak = 0
            self.multiplier = 1.0
            if self.shield_charges > 0:
                self.shield_charges -= 1
                self.powerup_label.text = "Shield absorbed a miss!"
            else:
                self.lives -= 1
                self._feedback(correct=False)
            if self.lives <= 0:
                self.end_game()
                return

        accuracy = (self.correct_attempts / self.attempts) * 100
        self.score_label.text = f"Score: {self.score} | Accuracy: {accuracy:.1f}%"
        self.input.text = ""
        self.next_word()
        self._refresh_hud()

    def update_timer(self, dt):
        if self.game_over:
            return
        if self.paused:
            return
        self.time_left -= 1
        self.word_time_left -= 1
        self.timer_label.text = f"Time: {self.time_left} | Word: {self.word_time_left}"

        if self.word_time_left <= 0:
            # Word timeout counts as a mistake.
            self.attempts += 1
            self.streak = 0
            self.multiplier = 1.0
            if self.shield_charges > 0:
                self.shield_charges -= 1
                self.powerup_label.text = "Shield absorbed a miss!"
            else:
                self.lives -= 1
                self._feedback(correct=False, timeout=True)
            self.input.text = ""
            if self.lives <= 0:
                self.end_game()
                return
            # Do not advance to a new word if the round timer is already over.
            if self.time_left <= 0:
                self.end_game()
                return
            self.next_word()
            self._refresh_hud()

        if self.time_left <= 0:
            self.end_game()

    def save_score(self):
        accuracy = self._final_accuracy_for_display()
        entry = {
            "score": int(self.score),
            "accuracy": round(accuracy, 1),
            "difficulty": str(self.difficulty),
            "category": str(self.category),
        }
        self.manager.get_screen("leaderboard").add_score(entry)

    def restart_game(self, instance):
        if self._tick_ev is not None:
            kivy.clock.Clock.unschedule(self._tick_ev)
            self._tick_ev = None
        self.start_game(difficulty=self.difficulty, category=self.category)

    def go_back(self, instance):
        if self._tick_ev is not None:
            kivy.clock.Clock.unschedule(self._tick_ev)
            self._tick_ev = None
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="right")
        self.manager.current = "menu"

    def toggle_pause(self, instance):
        if self.game_over:
            return
        self.paused = not self.paused
        if self.paused:
            self.pause_button.text = "Resume"
            self.input.disabled = True
            self.input.focus = False
            self._set_widget_visible(self.input, False)
            self.word_label.text = "[color=#AAAAAA]Paused[/color]"
        else:
            self.pause_button.text = "Pause"
            self.input.disabled = False
            self._set_widget_visible(self.input, True)
            self.word_label.text = self._current_word or "Ready"
            self._schedule_refocus_input()
        self._sync_skip_button_state()

    def skip_word(self, instance):
        if self.game_over or self.paused:
            return
        if self.skip_tokens <= 0:
            return
        self.skip_tokens -= 1
        self.skip_button.text = f"Skip ({self.skip_tokens})"
        self.word_time_left = self.word_time_limit
        self.input.text = ""
        self.next_word()
        self._refresh_hud()

    def _refresh_hud(self):
        self.lives_label.text = f"Lives: {self.lives}"
        self.streak_label.text = f"Streak: {self.streak} | Mult: x{self.multiplier:.1f}"
        self.timer_label.text = f"Time: {self.time_left} | Word: {self.word_time_left}"
        self.skip_button.text = f"Skip ({self.skip_tokens})"
        if self.shield_charges > 0:
            self.powerup_label.text = f"Shield ready x{self.shield_charges}"
        self._sync_skip_button_state()

    def _grant_powerup(self):
        # Randomly grant one of several power-ups.
        kind = ["time", "double", "skip", "shield"][self._rand_mod(4)]
        if kind == "time":
            self.time_left += 5
            self.powerup_label.text = "Power-up: +5 seconds"
        elif kind == "double":
            self.double_points_words_left += 3
            self.powerup_label.text = "Power-up: Double points (3 words)"
        elif kind == "skip":
            self.skip_tokens += 1
            self.powerup_label.text = "Power-up: +1 skip"
            self.skip_button.text = f"Skip ({self.skip_tokens})"
        else:
            self.shield_charges += 1
            self.powerup_label.text = "Power-up: Shield (1 mistake)"
        self._sync_skip_button_state()
        if self.sound_powerup:
            self.sound_powerup.play()

    def _rand_mod(self, n: int) -> int:
        # Simple deterministic RNG (LCG) to avoid importing Python's random module.
        self._rng_state = (1103515245 * self._rng_state + 12345) % 2147483647
        return 0 if n <= 0 else int(self._rng_state % n)

    def _pick_word(self) -> str:
        if not self.words:
            return ""
        idx = self._rand_mod(len(self.words))
        return self.words[idx]

    def _feedback(self, correct: bool, timeout: bool = False):
        # Sounds (optional).
        if correct and self.sound_correct:
            self.sound_correct.play()
        if (not correct) and self.sound_wrong:
            self.sound_wrong.play()

        # Visual feedback: flash input + shake on wrong.
        if correct:
            anim = kivy.animation.Animation(background_color=(0.1, 0.5, 0.1, 1), duration=0.08) + kivy.animation.Animation(
                background_color=(0.2, 0.2, 0.2, 1), duration=0.12
            )
            anim.start(self.input)
        else:
            anim = kivy.animation.Animation(background_color=(0.6, 0.1, 0.1, 1), duration=0.08) + kivy.animation.Animation(
                background_color=(0.2, 0.2, 0.2, 1), duration=0.12
            )
            anim.start(self.input)
            ox, oy = self.layout.pos
            shake = (
                kivy.animation.Animation(x=ox - 10, duration=0.03)
                + kivy.animation.Animation(x=ox + 10, duration=0.03)
                + kivy.animation.Animation(x=ox - 6, duration=0.03)
                + kivy.animation.Animation(x=ox + 6, duration=0.03)
                + kivy.animation.Animation(x=ox, duration=0.03)
            )
            shake.start(self.layout)
            if timeout:
                self.powerup_label.text = "Power-up: (Timed out)"

    def end_game(self):
        if self.game_over:
            return
        self.game_over = True
        if self._tick_ev is not None:
            kivy.clock.Clock.unschedule(self._tick_ev)
            self._tick_ev = None
        if self.sound_gameover:
            self.sound_gameover.play()
        self._show_only_game_over()
        # Subtle game-over pulse on the text.
        try:
            base_size = self.word_label.font_size
            anim = (
                kivy.animation.Animation(font_size=base_size * 1.25, duration=0.3)
                + kivy.animation.Animation(font_size=base_size * 0.95, duration=0.25)
            )
            anim.start(self.word_label)
        except Exception:
            pass
        self.save_score()
        # Keep the "only Game Over" screen, then return to menu automatically.
        kivy.clock.Clock.schedule_once(lambda _dt: self._auto_return_to_menu(), 2.0)

    def _auto_return_to_menu(self):
        if self.manager:
            self.manager.transition = kivy.uix.screenmanager.FadeTransition()
            self.manager.current = "menu"

# ---------------- LEADERBOARD SCREEN ----------------
class LeaderboardScreen(kivy.uix.screenmanager.Screen):
    # Column weights: rank | points | accuracy | category | difficulty (sum = 1)
    _LB_COLS = (0.06, 0.12, 0.18, 0.36, 0.28)
    _LB_ROW_H = 32

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = kivy.uix.boxlayout.BoxLayout(orientation="vertical", padding=20)
        add_background(self.layout, "#0B0F1A", center_panel=False)

        self._entries_box = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=10,
            size_hint_y=None,
            height=120,
        )

        self.back_button = styled_button("Back to Menu", "#FF6347", ui_btn_fs(), height=ui_btn_h())
        self.back_button.size_hint = (None, None)
        self.back_button.bind(on_press=self.go_back)

        self._lb_col = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=14,
            padding=[18, 20, 18, 20],
            size_hint=(None, None),
            width=320,
        )
        apply_rounded_card_backing(self._lb_col, radius=18)

        back_wrap = kivy.uix.anchorlayout.AnchorLayout(anchor_x="center", size_hint_y=None, height=ui_btn_h() + 6)
        back_wrap.add_widget(self.back_button)

        self._lb_col.add_widget(self._entries_box)
        self._lb_col.add_widget(back_wrap)

        center = kivy.uix.anchorlayout.AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 1))
        center.add_widget(self._lb_col)
        self.layout.add_widget(center)

        self.add_widget(self.layout)
        self.leaderboard = []
        self._store = None
        self.layout.bind(width=self._sync_lb_layout)
        self._entries_box.bind(minimum_height=lambda *_x: self._sync_lb_layout())
        self._load()
        self.display_leaderboard()
        self._sync_lb_layout()

    def _sync_lb_layout(self, *_a):
        # Wide enough for 5 columns; avoid Diff / headers spilling past the card edge.
        lw = self.layout.width or 400
        w = max(ui_col_w(lw), 340)
        if lw > 80:
            w = min(w, int(lw - 40))
        self._lb_col.width = w
        self.back_button.width = min(360, int(max(200, w * 0.92)))
        self._entries_box.height = max(1, self._entries_box.minimum_height)
        self._lb_col.height = max(1, self._lb_col.minimum_height)

    def _normalize_entry(self, entry):
        if not isinstance(entry, dict):
            return None
        try:
            score = int(entry.get("score", 0))
        except Exception:
            score = 0
        try:
            accuracy = float(entry.get("accuracy", 0.0))
        except Exception:
            accuracy = 0.0
        accuracy = max(0.0, min(100.0, accuracy))
        return {
            "score": max(0, score),
            "accuracy": round(accuracy, 1),
            "difficulty": str(entry.get("difficulty", "—")),
            "category": str(entry.get("category", "—")),
        }

    def _load(self):
        try:
            app = kivy.app.App.get_running_app()
            base = getattr(app, "user_data_dir", ".") if app else "."
            self._store = kivy.storage.jsonstore.JsonStore(f"{base}/leaderboard.json")
            if self._store.exists("scores"):
                data = self._store.get("scores").get("items", [])
                if isinstance(data, list):
                    clean = []
                    for x in data:
                        nx = self._normalize_entry(x)
                        if nx is not None:
                            clean.append(nx)
                    self.leaderboard = sorted(clean, key=lambda x: int(x.get("score", 0)), reverse=True)[:5]
                    self._save()
        except Exception:
            self.leaderboard = []
            self._store = None

    def _save(self):
        try:
            if self._store is not None:
                self._store.put("scores", items=self.leaderboard)
        except Exception:
            pass

    def add_score(self, entry):
        clean = self._normalize_entry(entry)
        if clean is None:
            return
        self.leaderboard.append(clean)
        self.leaderboard = sorted(self.leaderboard, key=lambda x: int(x.get("score", 0)), reverse=True)[:5]
        self._save()
        self.display_leaderboard()

    def _lb_header_cell(self, text, col_w, halign="left"):
        lbl = kivy.uix.label.Label(
            text=f"[b][color=#FFD700]{text}[/color][/b]",
            markup=True,
            font_size=13,
            size_hint_x=col_w,
            size_hint_y=1,
            halign=halign,
            valign="middle",
            text_size=(None, None),
        )

        def _hfit(*_a):
            lbl.text_size = (max(1, int(lbl.width) - 2), None)

        lbl.bind(width=_hfit)
        return lbl

    def _lb_data_cell(self, text, col_w, halign="left", shorten=False):
        lbl = kivy.uix.label.Label(
            text=text,
            font_size=14,
            color=kivy.utils.get_color_from_hex("#E8EEF8"),
            size_hint_x=col_w,
            size_hint_y=1,
            halign=halign,
            valign="middle",
            shorten=shorten,
            max_lines=1,
        )

        def _fit(*_a):
            lbl.text_size = (max(1, int(lbl.width) - 2), None)

        lbl.bind(width=_fit)
        return lbl

    def display_leaderboard(self):
        self._entries_box.clear_widgets()
        cw = self._LB_COLS
        rh = self._LB_ROW_H

        title = kivy.uix.label.Label(
            text="Leaderboard",
            font_size=22,
            bold=True,
            color=kivy.utils.get_color_from_hex("#FFFFFF"),
            size_hint_y=None,
            height=46,
            halign="center",
            valign="middle",
        )

        def _title_fit(*_a):
            title.text_size = (max(1, int(title.width)), None)

        title.bind(width=_title_fit)
        self._entries_box.add_widget(title)

        header = kivy.uix.boxlayout.BoxLayout(
            orientation="horizontal",
            spacing=4,
            size_hint_y=None,
            height=rh,
        )
        headers = [
            ("#", cw[0], "right"),
            ("Pts", cw[1], "right"),
            ("Acc %", cw[2], "right"),
            ("Category", cw[3], "left"),
            ("Diff", cw[4], "left"),
        ]
        for txt, wgt, ha in headers:
            header.add_widget(self._lb_header_cell(txt, wgt, ha))
        self._entries_box.add_widget(header)

        if not self.leaderboard:
            empty = kivy.uix.label.Label(
                text="No scores yet. Play a game!",
                font_size=15,
                color=kivy.utils.get_color_from_hex("#8899AA"),
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=44,
            )
            self._entries_box.add_widget(empty)
        else:
            for i, entry in enumerate(self.leaderboard, 1):
                score = entry.get("score", "—")
                acc = entry.get("accuracy", "—")
                cat = str(entry.get("category", "—"))
                diff = str(entry.get("difficulty", "—"))
                if isinstance(acc, (int, float)):
                    acc_s = f"{float(acc):.1f}%"
                else:
                    acc_s = f"{acc}%" if acc != "—" else "—"
                row = kivy.uix.boxlayout.BoxLayout(
                    orientation="horizontal",
                    spacing=4,
                    size_hint_y=None,
                    height=rh,
                )
                pts_txt = f"{score}\u00A0pts" if score != "—" else "—"
                row.add_widget(self._lb_data_cell(str(i), cw[0], "right"))
                row.add_widget(self._lb_data_cell(pts_txt, cw[1], "right"))
                row.add_widget(self._lb_data_cell(acc_s, cw[2], "right"))
                row.add_widget(self._lb_data_cell(cat, cw[3], "left", shorten=True))
                row.add_widget(self._lb_data_cell(diff, cw[4], "left"))
                self._entries_box.add_widget(row)

        kivy.clock.Clock.schedule_once(lambda _dt: self._sync_lb_layout(), 0)

    def go_back(self, instance):
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="right")
        self.manager.current = "menu"

# ---------------- SETUP SCREEN (CATEGORY + DIFFICULTY) ----------------
class DifficultyScreen(kivy.uix.screenmanager.Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = kivy.uix.boxlayout.BoxLayout(orientation="vertical", spacing=14, padding=[20, 16, 20, 16])
        # No fixed full-screen center card — form draws its own fitted card so controls stay inside it.
        add_background(layout, "#0B0F1A", center_panel=False)

        self.words_by_cat = load_words_by_category()
        categories = list(self.words_by_cat.keys())
        self.selected_category = categories[0] if categories else "Common"

        title = styled_label("Set Up Your Game", "#FFFFFF", 28)
        layout.add_widget(title)

        # Top-anchored form + scroll: vertical centering made the card draw upward and overlap the title when tall.
        setup_scroll = kivy.uix.scrollview.ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=6,
            bar_color=(0.45, 0.72, 0.95, 0.45),
            scroll_type=["bars", "content"],
        )
        setup_body = kivy.uix.anchorlayout.AnchorLayout(
            anchor_x="center",
            anchor_y="top",
            size_hint=(1, None),
        )
        card = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=[20, 18, 20, 22],
            size_hint=(None, None),
            width=320,
        )

        apply_rounded_card_backing(card, radius=18)

        cat_heading = styled_label("Word category", "#FFD700", 22)
        card.add_widget(cat_heading)
        hint = kivy.uix.label.Label(
            text=(
                "[b][color=#E8EEF8]Choose a word topic.[/color][/b] "
                "The [color=#C4B5FD]purple bar[/color] below is your category control — "
                "tap it to open the list, then tap a topic to select it."
            ),
            markup=True,
            font_size=15,
            color=kivy.utils.get_color_from_hex("#B8C4D4"),
            halign="center",
            valign="top",
            size_hint_y=None,
            line_height=1.25,
        )

        def _hint_height(*_a):
            hint.height = hint.texture_size[1] + 6

        def _hint_text_width(*_a):
            hint.text_size = (max(80, card.width - 20), None)

        card.add_widget(hint)
        hint.bind(texture_size=_hint_height)

        self.category_picker = CategoryPicker(
            categories,
            self.selected_category,
            on_change=self._on_category_changed,
        )
        card.add_widget(self.category_picker)

        diff_heading = styled_label("Difficulty", "#FFD700", 22)
        card.add_widget(diff_heading)
        diff_hint = kivy.uix.label.Label(
            text="Easy = more time & lives   |   Hard = less time",
            font_size=13,
            color=kivy.utils.get_color_from_hex("#AAAAAA"),
            halign="center",
            size_hint_y=None,
            height=22,
        )
        card.add_widget(diff_hint)

        setup_h = ui_btn_h()
        setup_fs = ui_btn_fs()
        btn_easy = styled_button("Easy", "#228B22", setup_fs, height=setup_h)
        btn_easy.bind(on_press=lambda x: self.start_game("Easy"))
        card.add_widget(btn_easy)
        btn_medium = styled_button("Medium", "#4169E1", setup_fs, height=setup_h)
        btn_medium.bind(on_press=lambda x: self.start_game("Medium"))
        card.add_widget(btn_medium)
        btn_hard = styled_button("Hard", "#B22222", setup_fs, height=setup_h)
        btn_hard.bind(on_press=lambda x: self.start_game("Hard"))
        card.add_widget(btn_hard)

        back_btn = styled_button("Back to Menu", "#708090", setup_fs, height=setup_h)
        back_btn.bind(on_press=self.go_back)
        card.add_widget(back_btn)

        def _sync_card_width(*_a):
            card.width = ui_col_w(layout.width)
            _hint_text_width()

        def _sync_setup_scroll(*_a):
            setup_body.height = max(card.height, 1)

        def _sync_card_height(*_a):
            card.height = max(card.minimum_height, 1)
            _sync_setup_scroll()

        card.bind(minimum_height=lambda *_x: _sync_card_height())
        self.category_picker.bind(
            height=lambda *_a: kivy.clock.Clock.schedule_once(lambda _dt: _sync_card_height(), 0)
        )

        setup_body.add_widget(card)
        setup_scroll.add_widget(setup_body)
        layout.add_widget(setup_scroll)

        def _sync_layout_width(*_a):
            _sync_card_width()
            _sync_setup_scroll()

        card.bind(height=lambda *_x: _sync_setup_scroll())
        layout.bind(width=_sync_layout_width)
        kivy.clock.Clock.schedule_once(
            lambda _dt: (_sync_card_width(), _sync_card_height(), _sync_setup_scroll()),
            0,
        )
        _sync_card_width()
        _sync_card_height()
        _sync_setup_scroll()

        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="right")
        self.manager.current = "menu"

    def _on_category_changed(self, text):
        self.selected_category = text

    def start_game(self, difficulty):
        game_screen = self.manager.get_screen("game")
        game_screen.start_game(difficulty=difficulty, category=self.selected_category)
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="left")
        self.manager.current = "game"

# ---------------- INSTRUCTIONS SCREEN ----------------
class InstructionsScreen(kivy.uix.screenmanager.Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = kivy.uix.boxlayout.BoxLayout(orientation="vertical", padding=24)
        add_background(layout, "#0B0F1A", center_panel=False)

        title = styled_label("How To Play", "#FFFFFF", 30)
        subtitle = kivy.uix.label.Label(
            text="Controls, scoring, and power-ups",
            font_size=16,
            color=kivy.utils.get_color_from_hex("#AAAAAA"),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=28,
        )

        text = (
            "[color=#FFD700][b]Goal[/b][/color]\n"
            "Type each word correctly before time runs out. Score points, build streaks, and use power-ups to climb the leaderboard.\n\n"
            "[color=#FFD700][b]Controls[/b][/color]\n"
            "• Choose a category and difficulty, then start.\n"
            "• Type the word shown and press [b]Enter[/b].\n"
            "• [b]Pause[/b] - freeze the timer. [b]Skip[/b] - skip the word (uses a skip token).\n\n"
            "[color=#FFD700][b]Scoring[/b][/color]\n"
            "• Base points per correct word. Consecutive correct words build a [b]streak[/b] and multiply your score (up to 2×).\n"
            "• Finish a word with plenty of time left for a small [b]perfect bonus[/b].\n\n"
            "[color=#FFD700][b]Lives & Game Over[/b][/color]\n"
            "• A wrong answer or word timeout costs one life. Game ends when lives hit zero or the main timer reaches 0; your score is saved to the leaderboard.\n\n"
            "[color=#FFD700][b]Power-Ups[/b][/color]\n"
            "• [b]+5 sec[/b] - add 5 seconds to the timer.\n"
            "• [b]Double points[/b] - next 3 words score double.\n"
            "• [b]Skip[/b] - one free word skip.\n"
            "• [b]Shield[/b] - absorb one mistake without losing a life."
        )
        def _scroll_h():
            h = kivy.core.window.Window.height
            return max(220, min(520, int(h * 0.42)))

        scroll = kivy.uix.scrollview.ScrollView(
            size_hint=(1, None),
            height=_scroll_h(),
            bar_width=8,
            scroll_type=["bars"],
        )
        inner = kivy.uix.boxlayout.BoxLayout(orientation="vertical", size_hint_y=None, padding=(12, 8))
        inner.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))

        instructions = kivy.uix.label.Label(
            text=text,
            font_size=17,
            color=kivy.utils.get_color_from_hex("#E8E8E8"),
            halign="center",
            valign="top",
            markup=True,
            size_hint_y=None,
            line_height=1.35,
        )
        def _update_text_size(_instance, value):
            w = value if (value is not None and value > 1) else (inner.width or layout.width or 300)
            instructions.text_size = (max(80, w * 0.96), None)

        inner.bind(width=_update_text_size)
        _update_text_size(inner, None)

        inner.add_widget(instructions)
        scroll.add_widget(inner)

        back_btn = styled_button("Back to Menu", "#708090", ui_btn_fs(), height=ui_btn_h())
        back_btn.size_hint = (None, None)
        back_wrap = kivy.uix.anchorlayout.AnchorLayout(anchor_x="center", size_hint_y=None, height=ui_btn_h() + 8)
        back_wrap.add_widget(back_btn)

        col = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=12,
            padding=[20, 18, 20, 22],
            size_hint=(None, None),
            width=320,
        )
        apply_rounded_card_backing(col, radius=18)

        def _howto_w(*_a):
            w = ui_col_w(layout.width)
            col.width = w
            back_btn.width = min(360, int(max(200, w * 0.92)))
            scroll.height = _scroll_h()
            col.height = max(1, col.minimum_height)

        def _on_instr_tex(inst, val):
            inst.height = val[1]
            kivy.clock.Clock.schedule_once(lambda _dt: _howto_w(), 0)

        instructions.bind(texture_size=_on_instr_tex)

        col.add_widget(title)
        col.add_widget(subtitle)
        col.add_widget(scroll)
        col.add_widget(back_wrap)
        back_btn.bind(on_press=self.go_back)

        center = kivy.uix.anchorlayout.AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 1))
        center.add_widget(col)

        layout.add_widget(kivy.uix.widget.Widget(size_hint_y=1))
        layout.add_widget(center)
        layout.add_widget(kivy.uix.widget.Widget(size_hint_y=1))

        layout.bind(width=_howto_w)
        kivy.clock.Clock.schedule_once(lambda _dt: _howto_w(), 0)
        _howto_w()

        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="right")
        self.manager.current = "menu"

# ---------------- AUTH SCREEN (LOCAL DEMO) ----------------
class LoginScreen(kivy.uix.screenmanager.Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = kivy.uix.boxlayout.BoxLayout(orientation="vertical", padding=[24, 18, 24, 18])
        add_background(layout, "#0B0F1A", center_panel=False)

        title = styled_label("Log In", "#FFFFFF", 30)

        card = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=[20, 18, 20, 22],
            size_hint=(None, None),
            width=ui_card_w(),
        )
        apply_rounded_card_backing(card, radius=18, line_width=1.15)

        # Username
        user_lbl = kivy.uix.label.Label(
            text="Username",
            font_size=14,
            color=kivy.utils.get_color_from_hex("#AAB8C8"),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=22,
        )
        self.user_inp = kivy.uix.textinput.TextInput(
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=44,
            halign="left",
            background_color=(0.18, 0.18, 0.22, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[12, 10, 12, 8],
        )

        # Password
        pass_lbl = kivy.uix.label.Label(
            text="Password",
            font_size=14,
            color=kivy.utils.get_color_from_hex("#AAB8C8"),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=22,
        )
        self.pass_inp = kivy.uix.textinput.TextInput(
            multiline=False,
            password=True,
            font_size=18,
            size_hint=(1, None),
            height=44,
            halign="left",
            background_color=(0.18, 0.18, 0.22, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[12, 10, 12, 8],
        )

        self.status_lbl = kivy.uix.label.Label(
            text="",
            font_size=14,
            color=kivy.utils.get_color_from_hex("#FFB6C1"),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=26,
        )

        self.login_btn = styled_button("Log In", "#2d9d4f", ui_btn_fs(), height=ui_btn_h())
        self.login_btn.bind(on_press=self._do_login)

        self.signup_btn = styled_button("Create Account", "#708090", ui_btn_fs(), height=ui_btn_h())
        self.signup_btn.bind(on_press=self._go_signup)

        card.add_widget(user_lbl)
        card.add_widget(self.user_inp)
        card.add_widget(pass_lbl)
        card.add_widget(self.pass_inp)
        card.add_widget(self.status_lbl)
        card.add_widget(self.login_btn)
        card.add_widget(self.signup_btn)

        # Ensure the rounded backing matches the BoxLayout content height.
        card.bind(
            minimum_height=lambda *_x: setattr(card, "height", max(1, card.minimum_height))
        )
        card.height = max(1, card.minimum_height)

        center = kivy.uix.anchorlayout.AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 1))
        center.add_widget(card)

        layout.add_widget(title)
        layout.add_widget(center)
        layout.add_widget(kivy.uix.widget.Widget(size_hint_y=1))
        layout.bind(width=lambda *_x: setattr(card, "width", ui_col_w(layout.width)))
        self.add_widget(layout)

    def _go_signup(self, *_a):
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="left")
        self.manager.current = "signup"

    def _do_login(self, *_a):
        username = (self.user_inp.text or "").strip()
        password = self.pass_inp.text or ""
        if not username or not password:
            self.status_lbl.text = "Please enter username and password."
            return

        users = _load_users()
        rec = users.get(username)
        if not rec:
            self.status_lbl.text = "User not found. Please sign up."
            return

        expected = rec.get("pw", "")
        got = _hash_password(password)
        if got != expected:
            self.status_lbl.text = "Incorrect password."
            return

        # Success: store session in the running app instance.
        app = kivy.app.App.get_running_app()
        if app is not None:
            app.current_user = username

        self.manager.transition = kivy.uix.screenmanager.FadeTransition()
        self.manager.current = "menu"


class SignupScreen(kivy.uix.screenmanager.Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = kivy.uix.boxlayout.BoxLayout(orientation="vertical", padding=[24, 18, 24, 18])
        add_background(layout, "#0B0F1A", center_panel=False)

        title = styled_label("Sign Up", "#FFFFFF", 30)

        card = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=10,
            padding=[20, 18, 20, 22],
            size_hint=(None, None),
            width=ui_card_w(),
        )
        apply_rounded_card_backing(card, radius=18, line_width=1.15)

        user_lbl = kivy.uix.label.Label(
            text="Username",
            font_size=14,
            color=kivy.utils.get_color_from_hex("#AAB8C8"),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=22,
        )
        self.user_inp = kivy.uix.textinput.TextInput(
            multiline=False,
            font_size=18,
            size_hint=(1, None),
            height=44,
            halign="left",
            background_color=(0.18, 0.18, 0.22, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[12, 10, 12, 8],
        )

        pass_lbl = kivy.uix.label.Label(
            text="Password",
            font_size=14,
            color=kivy.utils.get_color_from_hex("#AAB8C8"),
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=22,
        )
        self.pass_inp = kivy.uix.textinput.TextInput(
            multiline=False,
            password=True,
            font_size=18,
            size_hint=(1, None),
            height=44,
            halign="left",
            background_color=(0.18, 0.18, 0.22, 1),
            foreground_color=(1, 1, 1, 1),
            padding=[12, 10, 12, 8],
        )

        self.status_lbl = kivy.uix.label.Label(
            text="",
            font_size=14,
            color=kivy.utils.get_color_from_hex("#FFB6C1"),
            halign="center",
            valign="middle",
            size_hint_y=None,
            height=26,
        )

        self.signup_btn = styled_button("Create Account", "#2d9d4f", ui_btn_fs(), height=ui_btn_h())
        self.signup_btn.bind(on_press=self._do_signup)

        self.back_btn = styled_button("Back to Log In", "#708090", ui_btn_fs(), height=ui_btn_h())
        self.back_btn.bind(on_press=self._go_login)

        card.add_widget(user_lbl)
        card.add_widget(self.user_inp)
        card.add_widget(pass_lbl)
        card.add_widget(self.pass_inp)
        card.add_widget(self.status_lbl)
        card.add_widget(self.signup_btn)
        card.add_widget(self.back_btn)

        # Ensure the rounded backing matches the BoxLayout content height.
        card.bind(
            minimum_height=lambda *_x: setattr(card, "height", max(1, card.minimum_height))
        )
        card.height = max(1, card.minimum_height)

        center = kivy.uix.anchorlayout.AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 1))
        center.add_widget(card)

        layout.add_widget(title)
        layout.add_widget(center)
        layout.add_widget(kivy.uix.widget.Widget(size_hint_y=1))
        layout.bind(width=lambda *_x: setattr(card, "width", ui_col_w(layout.width)))
        self.add_widget(layout)

    def _go_login(self, *_a):
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="right")
        self.manager.current = "login"

    def _do_signup(self, *_a):
        username = (self.user_inp.text or "").strip()
        password = self.pass_inp.text or ""
        if not username or not password:
            self.status_lbl.text = "Please enter username and password."
            return
        if len(password) < 4:
            self.status_lbl.text = "Password must be at least 4 characters."
            return

        users = _load_users()
        if username in users:
            self.status_lbl.text = "Username already exists. Try another."
            return

        users[username] = {"pw": _hash_password(password)}
        _save_users(users)

        self.status_lbl.color = kivy.utils.get_color_from_hex("#7CFC00")
        self.status_lbl.text = "Account created! Log in now."
        self.pass_inp.text = ""

# ---------------- MENU SCREEN ----------------
class MenuScreen(kivy.uix.screenmanager.Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = kivy.uix.floatlayout.FloatLayout()
        add_background(layout, "#0B0F1A", center_panel=False)

        body = kivy.uix.anchorlayout.AnchorLayout(anchor_x="center", anchor_y="center", size_hint=(1, 1))
        menu_card = kivy.uix.boxlayout.BoxLayout(
            orientation="vertical",
            spacing=12,
            padding=[22, 22, 22, 24],
            size_hint=(None, None),
            width=ui_card_w(),
        )
        apply_rounded_card_backing(menu_card, radius=18, line_width=1.15)

        title = styled_label("Typing Challenge", "#FFFFFF", 30)
        menu_card.add_widget(title)
        tagline = kivy.uix.label.Label(
            text="Speed • Accuracy • Leaderboard",
            font_size=15,
            color=kivy.utils.get_color_from_hex("#AAB8C8"),
            halign="center",
            size_hint_y=None,
            height=26,
        )
        menu_card.add_widget(tagline)

        btn_col = kivy.uix.boxlayout.BoxLayout(orientation="vertical", spacing=8, size_hint_y=None)
        btn_col.bind(minimum_height=lambda *_x: setattr(btn_col, "height", max(1, btn_col.minimum_height)))
        btn_col.height = max(1, btn_col.minimum_height)
        start_button = styled_button("Start Game", "#2d9d4f", ui_btn_fs(), height=ui_btn_h())
        start_button.bind(on_press=self.select_difficulty)
        btn_col.add_widget(start_button)
        howto_button = styled_button("How To Play", "#d4a80a", ui_btn_fs(), height=ui_btn_h())
        howto_button.bind(on_press=self.view_instructions)
        btn_col.add_widget(howto_button)
        leaderboard_button = styled_button("View Leaderboard", "#c43546", ui_btn_fs(), height=ui_btn_h())
        leaderboard_button.bind(on_press=self.view_leaderboard)
        btn_col.add_widget(leaderboard_button)
        menu_card.add_widget(btn_col)

        def _menu_layout(*_a):
            menu_card.width = ui_col_w(layout.width)
            menu_card.height = menu_card.minimum_height

        menu_card.bind(minimum_height=lambda *_x: _menu_layout())
        layout.bind(width=_menu_layout)
        kivy.clock.Clock.schedule_once(lambda _dt: _menu_layout(), 0)
        _menu_layout()

        body.add_widget(menu_card)

        logout_btn = styled_button(
            "Log Out",
            "#FF6347",
            16,
            size_hint=(None, None),
            width=120,
            height=34,
            corner_radius=12,
        )

        def _logout(_instance):
            app = kivy.app.App.get_running_app()
            if app is not None:
                app.current_user = None
            self.manager.transition = kivy.uix.screenmanager.FadeTransition()
            self.manager.current = "login"

        logout_btn.bind(on_press=_logout)
        logout_anchor = kivy.uix.anchorlayout.AnchorLayout(anchor_x="left", anchor_y="top", size_hint=(1, 1))
        logout_anchor.add_widget(logout_btn)

        layout.add_widget(body)
        layout.add_widget(logout_anchor)

        self.add_widget(layout)

    def select_difficulty(self, instance):
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="left")
        self.manager.current = "difficulty"

    def view_leaderboard(self, instance):
        self.manager.transition = kivy.uix.screenmanager.FadeTransition()
        self.manager.current = "leaderboard"

    def view_instructions(self, instance):
        self.manager.transition = kivy.uix.screenmanager.SlideTransition(direction="left")
        self.manager.current = "howto"

# ---------------- APP ----------------
class TypingApp(kivy.app.App):
    def build(self):
        sm = kivy.uix.screenmanager.ScreenManager()
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(SignupScreen(name="signup"))
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(DifficultyScreen(name="difficulty"))
        sm.add_widget(GameScreen(name="game"))
        sm.add_widget(LeaderboardScreen(name="leaderboard"))
        sm.add_widget(InstructionsScreen(name="howto"))
        sm.current = "login"
        return sm

if __name__ == "__main__":
    TypingApp().run()