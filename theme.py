"""Paleta EnCore / Boeing + componentes reutilizables (estilo Vision UI: oscuro, tarjetas redondeadas)."""
import os
import tkinter as tk
from tkinter import ttk

import customtkinter as ctk
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))

# Colores: azul del swoosh del logo + azul Boeing sobre fondo navy
BG, SIDEBAR = "#0B1437", "#060B28"
CARD, CARD2, BORDER = "#111C44", "#1B2B63", "#26356F"
ACCENT, ACCENT_HOVER = "#4F9BD9", "#3B82C4"
BLUE, BLUE_HOVER = "#1D5BD6", "#174AB0"
TEXT, MUTED = "#FFFFFF", "#A3AED0"
OK, DANGER, WARN = "#01B574", "#E5484D", "#FFB547"
CHART = ["#4F9BD9", "#1D5BD6", "#7DD3FC", "#01B574", "#FFB547", "#A78BFA"]
FONT = "Segoe UI"
BLANK = "— Selecciona —"


def font(size=13, weight="normal"):
    return ctk.CTkFont(family=FONT, size=size, weight=weight)


def logo(width):
    img = Image.open(os.path.join(BASE, "assets", "logo_light.png")).convert("RGBA")
    img = img.crop(img.split()[3].point(lambda a: 255 if a > 20 else 0).getbbox())
    size = (width, int(width * img.height / img.width))
    return ctk.CTkImage(light_image=img, dark_image=img, size=size)


def card(parent, **kw):
    return ctk.CTkFrame(parent, fg_color=CARD, corner_radius=20, border_width=1, border_color=BORDER, **kw)


def label(parent, text, size=13, weight="normal", color=TEXT, **kw):
    return ctk.CTkLabel(parent, text=text, font=font(size, weight), text_color=color, **kw)


def entry(parent, **kw):
    kw.setdefault("height", 42)
    return ctk.CTkEntry(parent, corner_radius=12, fg_color=CARD2, border_color=BORDER,
                        text_color=TEXT, placeholder_text_color=MUTED, font=font(13), **kw)


def button(parent, text, command=None, kind="primary", **kw):
    colors = {"primary": (ACCENT, ACCENT_HOVER), "blue": (BLUE, BLUE_HOVER),
              "ghost": (CARD2, BORDER), "danger": (DANGER, "#C23A3F")}[kind]
    kw.setdefault("height", 42)
    return ctk.CTkButton(parent, text=text, command=command, corner_radius=12, fg_color=colors[0],
                         hover_color=colors[1], text_color=TEXT, font=font(13, "bold"),
                         text_color_disabled=MUTED, **kw)


def menu(parent, values, variable, command=None, **kw):
    return ctk.CTkOptionMenu(parent, values=values, variable=variable, command=command, height=42,
                             corner_radius=12, fg_color=CARD2, button_color=BLUE, button_hover_color=ACCENT,
                             dropdown_fg_color=CARD2, dropdown_hover_color=BLUE, text_color=TEXT,
                             font=font(13), dropdown_font=font(13), **kw)


def digits_only(var, maxlen=9):
    def _f(*_):
        v = "".join(ch for ch in var.get() if ch.isdigit())[:maxlen]
        if v != var.get():
            var.set(v)
    var.trace_add("write", _f)


def set_enabled(widgets, enabled):
    for w in widgets:
        w.configure(state="normal" if enabled else "disabled")


def reflow(container, widgets, cols, weights=None, expand_rows=False, pad=8):
    """Reacomoda widgets en `cols` columnas (diseño adaptable)."""
    for i in range(12):
        container.grid_columnconfigure(i, weight=0, uniform="")
        container.grid_rowconfigure(i, weight=0)
    rows = -(-len(widgets) // cols)
    for c in range(cols):
        w = weights[c] if weights else 1
        container.grid_columnconfigure(c, weight=w, uniform="" if weights else "g")
    for r in range(rows):
        container.grid_rowconfigure(r, weight=1 if expand_rows and (cols > 1 or r == rows - 1) else 0)
    for i, w in enumerate(widgets):
        w.grid(row=i // cols, column=i % cols, sticky="nsew", padx=pad, pady=pad)


def fit_width(parent, target, maxw=620):
    parent.bind("<Configure>", lambda e: target.configure(width=max(300, min(maxw, e.width - 60))), add="+")


def _style():
    s = ttk.Style()
    s.theme_use("clam")
    s.configure("Encore.Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                rowheight=36, borderwidth=0, font=(FONT, 11))
    s.configure("Encore.Treeview.Heading", background=CARD2, foreground=MUTED, relief="flat",
                font=(FONT, 10, "bold"), padding=8)
    s.map("Encore.Treeview", background=[("selected", BLUE)], foreground=[("selected", "white")])
    s.map("Encore.Treeview.Heading", background=[("active", CARD2)])


class DataTable(ctk.CTkFrame):
    def __init__(self, parent, columns, height=8):
        super().__init__(parent, fg_color="transparent")
        _style()
        self.tree = ttk.Treeview(self, columns=[c[0] for c in columns], show="headings",
                                 style="Encore.Treeview", selectmode="browse", height=height)
        for key, title, w in columns:
            self.tree.heading(key, text=title, anchor="w")
            self.tree.column(key, width=w, minwidth=60, anchor="w", stretch=True)
        self.tree.tag_configure("odd", background="#0F1A40")
        sb = ctk.CTkScrollbar(self, command=self.tree.yview, fg_color=CARD, button_color=CARD2)
        self.tree.configure(yscrollcommand=sb.set)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

    def set_rows(self, rows):
        self.tree.delete(*self.tree.get_children())
        for i, r in enumerate(rows):
            self.tree.insert("", "end", values=[str(v) for v in r], tags=("odd",) if i % 2 else ())

    def selected(self):
        sel = self.tree.selection()
        return self.tree.item(sel[0])["values"] if sel else None
