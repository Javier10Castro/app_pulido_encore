import sqlite3
import tkinter as tk
from collections import defaultdict
from datetime import datetime
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

import database as db
import exporter
from theme import *

PERIODS = {"Últimos 7 días": 7, "Últimos 30 días": 30, "Últimos 90 días": 90, "Todo el historial": None}
TURNOS = [BLANK, "A", "B", "C"]


class View(ctk.CTkFrame):
    title, subtitle = "", ""

    def __init__(self, app):
        super().__init__(app.content, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 10))
        label(head, self.title, 26, "bold").pack(anchor="w")
        label(head, self.subtitle, 13, color=MUTED).pack(anchor="w")

    def on_show(self):
        pass


def field(parent, text):
    label(parent, text, 12, color=MUTED).pack(anchor="w", padx=22, pady=(14, 4))


# ======================= DASHBOARD =======================
class Chart(ctk.CTkFrame):
    def __init__(self, parent, title):
        super().__init__(parent, fg_color=CARD, corner_radius=20, border_width=1, border_color=BORDER)
        label(self, title, 15, "bold").pack(anchor="w", padx=18, pady=(14, 0))
        self.fig = Figure(figsize=(4, 2.8), dpi=100, facecolor=CARD, layout="tight")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        w = self.canvas.get_tk_widget()
        w.configure(bg=CARD, highlightthickness=0, height=260)
        w.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def axes(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(CARD)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(BORDER)
        ax.tick_params(colors=MUTED, labelsize=8)
        ax.grid(axis="y", color=BORDER, alpha=.5, linewidth=.6)
        ax.set_axisbelow(True)
        return ax

    def empty(self, ax):
        ax.text(.5, .5, "Sin datos", ha="center", va="center", color=MUTED, transform=ax.transAxes)
        ax.axis("off")


class Dashboard(View):
    title, subtitle = "Dashboard", "Resumen de capturas de material"

    def __init__(self, app):
        super().__init__(app)
        self._k = None
        b = ctk.CTkScrollableFrame(self, fg_color="transparent")
        b.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        b.grid_columnconfigure(0, weight=1)

        specs = [("Capturar Datos", "Registrar material por empleado", "capture", ACCENT, ACCENT_HOVER),
                 ("Agregar Empleados", "Alta y gestión de personal", "employees", BLUE, BLUE_HOVER),
                 ("Agregar Materiales", "Catálogo de materiales", "materials", "#2E4A9E", "#3A5AB8")]
        self.actions = ctk.CTkFrame(b, fg_color="transparent")
        self.actions.grid(row=0, column=0, sticky="ew")
        self.action_btns = [ctk.CTkButton(self.actions, text=f"{t}\n{s}", height=76, corner_radius=18,
                                          fg_color=c, hover_color=h, font=font(15, "bold"),
                                          command=lambda k=k: self.app.show(k)) for t, s, k, c, h in specs]

        fc = card(b)
        fc.grid(row=1, column=0, sticky="ew", padx=8, pady=8)
        row = ctk.CTkFrame(fc, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=12)
        label(row, "Filtros", 15, "bold").pack(side="left", padx=(0, 16))
        self.f_turno = tk.StringVar(value="Todos")
        self.f_mat = tk.StringVar(value="Todos")
        self.f_per = tk.StringVar(value="Últimos 30 días")
        self.mat_menu = None
        for txt, var, vals in (("Turno", self.f_turno, ["Todos", "A", "B", "C"]),
                               ("Material", self.f_mat, ["Todos"]),
                               ("Periodo", self.f_per, list(PERIODS))):
            label(row, txt, 12, color=MUTED).pack(side="left", padx=(8, 6))
            m = menu(row, vals, var, command=lambda _: self.refresh(), width=150)
            m.pack(side="left", padx=(0, 8))
            if txt == "Material":
                self.mat_menu = m

        self.kpi_frame = ctk.CTkFrame(b, fg_color="transparent")
        self.kpi_frame.grid(row=2, column=0, sticky="ew")
        self.kpis, self.kpi_vals = [], []
        for t in ("Total de piezas", "Registros", "Empleados activos", "Material principal"):
            c = card(self.kpi_frame)
            label(c, t, 12, color=MUTED).pack(anchor="w", padx=20, pady=(16, 0))
            v = label(c, "—", 24, "bold")
            v.pack(anchor="w", padx=20, pady=(2, 16))
            self.kpis.append(c)
            self.kpi_vals.append(v)

        self.chart_frame = ctk.CTkFrame(b, fg_color="transparent")
        self.chart_frame.grid(row=3, column=0, sticky="ew")
        self.c_day = Chart(self.chart_frame, "Piezas por día")
        self.c_mat = Chart(self.chart_frame, "Piezas por material")
        self.c_turno = Chart(self.chart_frame, "Distribución por turno")
        self.c_emp = Chart(self.chart_frame, "Top empleados")
        self.charts = [self.c_day, self.c_mat, self.c_turno, self.c_emp]
        self.bind("<Configure>", self._layout, add="+")

    def _layout(self, e):
        cols = (3 if e.width >= 760 else 1, 4 if e.width >= 1100 else 2, 2 if e.width >= 1000 else 1)
        if cols == self._k:
            return
        self._k = cols
        reflow(self.actions, self.action_btns, cols[0])
        reflow(self.kpi_frame, self.kpis, cols[1])
        reflow(self.chart_frame, self.charts, cols[2])

    def on_show(self):
        vals = ["Todos"] + db.list_materials()
        self.mat_menu.configure(values=vals)
        if self.f_mat.get() not in vals:
            self.f_mat.set("Todos")
        self.refresh()

    def refresh(self):
        g = lambda v: None if v.get() == "Todos" else v.get()
        rows = db.report_rows(g(self.f_turno), g(self.f_mat), PERIODS[self.f_per.get()])
        by = lambda key: self._sum(rows, key)
        mats = sorted(by("material").items(), key=lambda x: -x[1])
        self.kpi_vals[0].configure(text=f"{sum(r['cantidad'] for r in rows):,}")
        self.kpi_vals[1].configure(text=f"{len(rows):,}")
        self.kpi_vals[2].configure(text=str(len({r['empleado'] for r in rows})))
        self.kpi_vals[3].configure(text=(mats[0][0][:16] if mats else "—"))
        self._day(rows)
        self._bars(self.c_mat, mats[:6], CHART[0])
        self._donut(by("turno"))
        emps = sorted(self._sum(rows, "nombre").items(), key=lambda x: -x[1])
        self._bars(self.c_emp, emps[:5], CHART[2])

    @staticmethod
    def _sum(rows, key):
        d = defaultdict(int)
        for r in rows:
            d[r[key]] += r["cantidad"]
        return d

    def _day(self, rows):
        ax = self.c_day.axes()
        d = defaultdict(int)
        for r in rows:
            d[r["fecha"][:10]] += r["cantidad"]
        if not d:
            self.c_day.empty(ax)
        else:
            keys = sorted(d)
            vals = [d[k] for k in keys]
            x = list(range(len(keys)))
            ax.plot(x, vals, color=ACCENT, linewidth=2.5, marker="o", markersize=4)
            ax.fill_between(x, vals, color=ACCENT, alpha=.18)
            ax.xaxis.set_major_locator(MaxNLocator(integer=True, nbins=6))
            ax.xaxis.set_major_formatter(FuncFormatter(
                lambda v, _: keys[round(v)][5:] if 0 <= round(v) < len(keys) else ""))
        self.c_day.canvas.draw_idle()

    def _bars(self, chart, pairs, color):
        ax = chart.axes()
        if not pairs:
            chart.empty(ax)
        else:
            pairs = pairs[::-1]
            ax.barh([str(p[0])[:16] for p in pairs], [p[1] for p in pairs], color=color, height=.55)
            ax.grid(axis="y", visible=False)
            ax.grid(axis="x", color=BORDER, alpha=.5)
        chart.canvas.draw_idle()

    def _donut(self, data):
        ax = self.c_turno.axes()
        if not data:
            self.c_turno.empty(ax)
        else:
            ks = sorted(data)
            ax.pie([data[k] for k in ks], labels=[f"Turno {k}" for k in ks], colors=CHART, startangle=90,
                   wedgeprops=dict(width=.38, edgecolor=CARD), textprops=dict(color=MUTED, fontsize=9),
                   autopct="%1.0f%%", pctdistance=.8)
            ax.grid(False)
        self.c_turno.canvas.draw_idle()


# ======================= REGISTROS =======================
class Records(View):
    title, subtitle = "Registros", "Historial de capturas: revisa, filtra, elimina y exporta a Excel"

    def __init__(self, app):
        super().__init__(app)
        self.is_admin = bool(app.user["is_admin"])
        card_ = card(self)
        card_.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        card_.grid_columnconfigure(0, weight=1)
        card_.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(card_, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 4))
        label(top, "Historial de registros", 15, "bold").pack(side="left")
        button(top, "Exportar a Excel", self.export, kind="blue", width=170).pack(side="right")

        flt = ctk.CTkFrame(card_, fg_color="transparent")
        flt.grid(row=1, column=0, sticky="ew", padx=18, pady=(4, 8))
        self.f_turno = tk.StringVar(value="Todos")
        self.f_mat = tk.StringVar(value="Todos")
        self.f_per = tk.StringVar(value="Todo el historial")
        self.mat_menu = None
        for txt, var, vals in (("Turno", self.f_turno, ["Todos", "A", "B", "C"]),
                               ("Material", self.f_mat, ["Todos"]),
                               ("Periodo", self.f_per, list(PERIODS))):
            label(flt, txt, 12, color=MUTED).pack(side="left", padx=(8, 6))
            m = menu(flt, vals, var, command=lambda _: self.refresh(), width=150)
            m.pack(side="left", padx=(0, 8))
            if txt == "Material":
                self.mat_menu = m

        self.table = DataTable(card_, [("id", "ID", 50), ("fecha", "Fecha", 140), ("emp", "Empleado", 70),
                                       ("nombre", "Nombre", 150), ("turno", "Turno", 60),
                                       ("mat", "Material", 150), ("cant", "Cantidad", 80)], height=14)
        self.table.grid(row=2, column=0, sticky="nsew", padx=14)

        bt = ctk.CTkFrame(card_, fg_color="transparent")
        bt.grid(row=3, column=0, sticky="ew", padx=14, pady=14)
        self.del_btn = button(bt, "Eliminar registro", self.delete, kind="danger", width=170,
                              state="normal" if self.is_admin else "disabled")
        self.del_btn.pack(side="left")
        if not self.is_admin:
            label(bt, "Solo el administrador puede eliminar registros.",
                  12, color=MUTED).pack(side="left", padx=12)
        self.refresh()

    def on_show(self):
        vals = ["Todos"] + db.list_materials()
        self.mat_menu.configure(values=vals)
        if self.f_mat.get() not in vals:
            self.f_mat.set("Todos")
        self.refresh()

    def refresh(self):
        g = lambda v: None if v.get() == "Todos" else v.get()
        rows = db.report_rows(g(self.f_turno), g(self.f_mat), PERIODS[self.f_per.get()])
        self.table.set_rows([(r["id"], r["fecha"], r["empleado"], r["nombre"], r["turno"],
                              r["material"], r["cantidad"]) for r in rows])

    def delete(self):
        if not self.is_admin:
            return messagebox.showwarning("Eliminar", "Solo el administrador puede eliminar registros.")
        s = self.table.selected()
        if not s:
            return messagebox.showinfo("Eliminar", "Selecciona un registro de la lista.")
        if messagebox.askyesno("Eliminar",
                               f"¿Eliminar el registro #{s[0]}?\n{s[3]} · {s[5]} → {s[6]} unidades "
                               f"({s[1]})\nEsta acción no se puede deshacer."):
            db.delete_report(int(s[0]))
            self.refresh()

    def export(self):
        path = filedialog.asksaveasfilename(
            title="Exportar a Excel", defaultextension=".xlsx",
            filetypes=[("Libro de Excel", "*.xlsx")],
            initialfile=f"EnCore_Export_{datetime.now():%Y%m%d_%H%M%S}.xlsx")
        if not path:
            return
        try:
            exporter.export_xlsx(path)
        except PermissionError:
            return messagebox.showerror("Error", "El archivo está abierto. Ciérralo e inténtalo de nuevo.")
        messagebox.showinfo("Exportado", f"Datos exportados correctamente:\n{path}")


# ======================= CAPTURAR DATOS =======================
class Capture(View):
    title, subtitle = "Capturar Datos", "Registra la cantidad de material por empleado, paso a paso"

    def __init__(self, app):
        super().__init__(app)
        wrap = ctk.CTkScrollableFrame(self, fg_color="transparent")
        wrap.grid(row=1, column=0, sticky="nsew", padx=16)
        wrap.grid_columnconfigure(0, weight=1)
        self.card = card(wrap, width=620)
        self.card.grid(row=0, column=0, pady=8)
        fit_width(self, self.card)
        c = self.card
        self.emp = None

        field(c, "Paso 1 · Número de empleado")
        r = ctk.CTkFrame(c, fg_color="transparent")
        r.pack(fill="x", padx=22)
        self.num = tk.StringVar()
        digits_only(self.num)
        self.num_entry = entry(r, textvariable=self.num, placeholder_text="Ej. 10234")
        self.num_entry.pack(side="left", fill="x", expand=True)
        self.num_entry.bind("<Return>", lambda e: self.validate())
        self.val_btn = button(r, "Validar", self.validate, width=110)
        self.val_btn.pack(side="left", padx=(10, 0))
        self.status = label(c, "", 12, color=MUTED, anchor="w", justify="left", wraplength=520)
        self.status.pack(anchor="w", padx=22, pady=(8, 0))

        field(c, "Paso 2 · Material")
        self.mat = tk.StringVar(value=BLANK)
        self.mat_menu = menu(c, [BLANK], self.mat, command=self._on_mat)
        self.mat_menu.pack(fill="x", padx=22)

        field(c, "Paso 3 · Cantidad")
        self.qty = tk.StringVar()
        digits_only(self.qty, 7)
        self.qty.trace_add("write", lambda *_: self._update_save())
        self.qty_entry = entry(c, textvariable=self.qty, placeholder_text="Solo números")
        self.qty_entry.pack(fill="x", padx=22)

        self.save_btn = button(c, "Guardar registro", self.save, kind="blue", height=48)
        self.save_btn.pack(fill="x", padx=22, pady=(24, 6))
        button(c, "Limpiar / cambiar empleado", self.reset, kind="ghost").pack(fill="x", padx=22, pady=(0, 24))
        self.reset()

    def on_show(self):
        self.reset()

    def reset(self):
        self.emp = None
        self.num.set("")
        self.qty.set("")
        self.mat.set(BLANK)
        self.status.configure(text="Ingresa el número y presiona Validar.", text_color=MUTED)
        set_enabled([self.num_entry, self.val_btn], True)
        set_enabled([self.mat_menu, self.qty_entry, self.save_btn], False)
        self.num_entry.focus()

    def validate(self):
        txt = self.num.get().strip()
        if not txt:
            self.status.configure(text="Escribe un número de empleado.", text_color=WARN)
            return
        emp = db.get_employee(int(txt))
        if emp is None:
            self.status.configure(text=f"El empleado {txt} no existe. Inténtalo de nuevo.", text_color=DANGER)
            messagebox.showwarning("Empleado no encontrado", f"El empleado {txt} no existe.\nVerifica el número e inténtalo de nuevo.")
            self.num_entry.select_range(0, "end")
            self.num_entry.focus()
            return
        self.emp = emp
        self.status.configure(text=f"✔ {emp['nombre']} · Turno {emp['turno']}", text_color=OK)
        set_enabled([self.num_entry, self.val_btn], False)
        mats = db.list_materials()
        self.mat_menu.configure(values=[BLANK] + mats, state="normal")
        self.mat.set(BLANK)
        if not mats:
            self.status.configure(text="No hay materiales registrados. Agrégalos primero.", text_color=WARN)

    def _on_mat(self, _=None):
        ok = self.mat.get() != BLANK
        self.qty_entry.configure(state="normal" if ok else "disabled")
        self._update_save()

    def _update_save(self):
        q = self.qty.get()
        valid = self.emp is not None and self.mat.get() != BLANK and q.isdigit() and int(q) > 0
        self.save_btn.configure(state="normal" if valid else "disabled")

    def save(self):
        db.add_report(self.emp["id"], self.mat.get(), int(self.qty.get()))
        messagebox.showinfo("Guardado", "Registro guardado correctamente.")
        self.reset()


# ======================= EMPLEADOS =======================
class Employees(View):
    title, subtitle = "Empleados", "Alta, edición y baja de personal"

    def __init__(self, app):
        super().__init__(app)
        self.edit_id = None
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.form, self.tcard = card(self.body), card(self.body)
        f = self.form
        self.form_title = label(f, "Nuevo empleado", 17, "bold")
        self.form_title.pack(anchor="w", padx=22, pady=(20, 0))
        field(f, "Paso 1 · Número de empleado")
        self.num = tk.StringVar()
        digits_only(self.num)
        self.num_entry = entry(f, textvariable=self.num, placeholder_text="Ej. 10234")
        self.num_entry.pack(fill="x", padx=22)
        self.num_entry.bind("<Return>", lambda e: self.verify())
        self.verify_btn = button(f, "Verificar disponibilidad", self.verify, kind="blue")
        self.verify_btn.pack(fill="x", padx=22, pady=(10, 0))
        self.msg = label(f, "", 12, color=MUTED, anchor="w", justify="left", wraplength=280)
        self.msg.pack(anchor="w", padx=22, pady=(8, 0))
        field(f, "Paso 2 · Nombre")
        self.name = tk.StringVar()
        self.name.trace_add("write", lambda *_: self._update_save())
        self.name_entry = entry(f, textvariable=self.name, placeholder_text="Nombre completo")
        self.name_entry.pack(fill="x", padx=22)
        field(f, "Paso 3 · Turno")
        self.turno = tk.StringVar(value=BLANK)
        self.turno_menu = menu(f, TURNOS, self.turno, command=lambda _: self._update_save())
        self.turno_menu.pack(fill="x", padx=22)
        self.save_btn = button(f, "Guardar empleado", self.save, height=46)
        self.save_btn.pack(fill="x", padx=22, pady=(22, 6))
        button(f, "Cancelar / limpiar", self.reset, kind="ghost").pack(fill="x", padx=22, pady=(0, 22))

        t = self.tcard
        top = ctk.CTkFrame(t, fg_color="transparent")
        top.pack(fill="x", padx=18, pady=(16, 8))
        label(top, "Lista de empleados", 15, "bold").pack(side="left")
        self.search = tk.StringVar()
        self.search.trace_add("write", lambda *_: self.refresh())
        entry(top, textvariable=self.search, placeholder_text="Buscar…", width=200).pack(side="right")
        self.table = DataTable(t, [("id", "Empleado", 90), ("nombre", "Nombre", 220), ("turno", "Turno", 70)], height=12)
        self.table.pack(fill="both", expand=True, padx=14)
        bt = ctk.CTkFrame(t, fg_color="transparent")
        bt.pack(fill="x", padx=14, pady=14)
        button(bt, "Editar", self.edit, kind="ghost", width=110).pack(side="left", padx=(0, 8))
        button(bt, "Eliminar", self.delete, kind="danger", width=110).pack(side="left")
        self._k = None
        self.bind("<Configure>", self._layout, add="+")
        self.reset()

    def _layout(self, e):
        k = e.width >= 1000
        if k != self._k:
            self._k = k
            reflow(self.body, [self.form, self.tcard], 2 if k else 1, weights=(2, 3) if k else None, expand_rows=True)

    def on_show(self):
        self.reset()

    def _fields(self, on):
        set_enabled([self.name_entry, self.turno_menu], on)

    def reset(self):
        self.edit_id = None
        self.num.set("")
        self.name.set("")
        self.turno.set(BLANK)
        self.form_title.configure(text="Nuevo empleado")
        self.save_btn.configure(text="Guardar empleado", state="disabled")
        self.msg.configure(text="Ingresa un número para verificar que no exista.", text_color=MUTED)
        set_enabled([self.num_entry, self.verify_btn], True)
        self._fields(False)
        self.refresh()

    def verify(self):
        txt = self.num.get().strip()
        if not txt:
            self.msg.configure(text="Escribe un número de empleado.", text_color=WARN)
            return
        if db.employee_exists(int(txt)):
            self.msg.configure(text=f"El empleado {txt} ya existe.", text_color=DANGER)
            messagebox.showwarning("Empleado existente", f"El número {txt} ya está registrado.")
            self.num_entry.select_range(0, "end")
            return
        self.msg.configure(text="✔ Número disponible. Completa los datos.", text_color=OK)
        set_enabled([self.num_entry, self.verify_btn], False)
        self._fields(True)
        self.name_entry.focus()

    def _update_save(self):
        ok = self.name.get().strip() != "" and self.turno.get() != BLANK and \
             (self.edit_id is not None or self.num_entry.cget("state") == "disabled")
        self.save_btn.configure(state="normal" if ok else "disabled")

    def save(self):
        n, t = self.name.get().strip(), self.turno.get()
        if self.edit_id is not None:
            db.update_employee(self.edit_id, n, t)
        else:
            db.add_employee(int(self.num.get()), n, t)
        messagebox.showinfo("Guardado", "Empleado guardado correctamente.")
        self.reset()

    def edit(self):
        s = self.table.selected()
        if not s:
            return messagebox.showinfo("Editar", "Selecciona un empleado de la lista.")
        self.reset()
        self.edit_id = int(s[0])
        self.num.set(str(s[0]))
        set_enabled([self.num_entry, self.verify_btn], False)
        self._fields(True)
        self.name.set(str(s[1]))
        self.turno.set(str(s[2]))
        self.form_title.configure(text=f"Editando empleado {s[0]}")
        self.save_btn.configure(text="Actualizar empleado")
        self.msg.configure(text="Modo edición (el número no se puede cambiar).", text_color=MUTED)
        self._update_save()

    def delete(self):
        s = self.table.selected()
        if s and messagebox.askyesno("Eliminar", f"¿Eliminar al empleado {s[0]} – {s[1]}?\nSus registros históricos se conservan."):
            db.delete_employee(int(s[0]))
            self.reset()

    def refresh(self):
        q = self.search.get().strip().lower()
        self.table.set_rows([(e["id"], e["nombre"], e["turno"]) for e in db.list_employees()
                             if q in str(e["id"]) or q in e["nombre"].lower()])


# ======================= MATERIALES =======================
class Materials(View):
    title, subtitle = "Materiales", "Catálogo de materiales (los nombres no se pueden repetir)"

    def __init__(self, app):
        super().__init__(app)
        self.old = None
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.form, self.tcard = card(self.body), card(self.body)
        f = self.form
        self.form_title = label(f, "Nuevo material", 17, "bold")
        self.form_title.pack(anchor="w", padx=22, pady=(20, 0))
        field(f, "Nombre del material")
        self.name = tk.StringVar()
        self.entry = entry(f, textvariable=self.name, placeholder_text="Ej. Aluminio 6061")
        self.entry.pack(fill="x", padx=22)
        self.entry.bind("<Return>", lambda e: self.save())
        self.msg = label(f, "", 12, color=MUTED, anchor="w", justify="left", wraplength=280)
        self.msg.pack(anchor="w", padx=22, pady=(8, 0))
        self.save_btn = button(f, "Agregar material", self.save, height=46)
        self.save_btn.pack(fill="x", padx=22, pady=(18, 6))
        button(f, "Cancelar / limpiar", self.reset, kind="ghost").pack(fill="x", padx=22, pady=(0, 22))

        t = self.tcard
        label(t, "Lista de materiales", 15, "bold").pack(anchor="w", padx=18, pady=(16, 8))
        self.table = DataTable(t, [("nombre", "Material", 300)], height=12)
        self.table.pack(fill="both", expand=True, padx=14)
        bt = ctk.CTkFrame(t, fg_color="transparent")
        bt.pack(fill="x", padx=14, pady=14)
        button(bt, "Renombrar", self.edit, kind="ghost", width=120).pack(side="left", padx=(0, 8))
        button(bt, "Eliminar", self.delete, kind="danger", width=110).pack(side="left")
        self._k = None
        self.bind("<Configure>", self._layout, add="+")
        self.reset()

    def _layout(self, e):
        k = e.width >= 1000
        if k != self._k:
            self._k = k
            reflow(self.body, [self.form, self.tcard], 2 if k else 1, weights=(2, 3) if k else None, expand_rows=True)

    def on_show(self):
        self.reset()

    def reset(self):
        self.old = None
        self.name.set("")
        self.form_title.configure(text="Nuevo material")
        self.save_btn.configure(text="Agregar material")
        self.msg.configure(text="Se revisará que el nombre no exista.", text_color=MUTED)
        self.table.set_rows([(m,) for m in db.list_materials()])

    def save(self):
        n = self.name.get().strip()
        if not n:
            self.msg.configure(text="Escribe el nombre del material.", text_color=WARN)
            return
        same = self.old is not None and n.lower() == self.old.lower()
        if db.material_exists(n) and not same:
            self.msg.configure(text=f"El material «{n}» ya existe.", text_color=DANGER)
            messagebox.showwarning("Material existente", f"«{n}» ya está registrado.")
            return
        db.rename_material(self.old, n) if self.old else db.add_material(n)
        messagebox.showinfo("Guardado", "Material guardado correctamente.")
        self.reset()

    def edit(self):
        s = self.table.selected()
        if not s:
            return messagebox.showinfo("Renombrar", "Selecciona un material de la lista.")
        self.old = str(s[0])
        self.name.set(self.old)
        self.form_title.configure(text="Renombrar material")
        self.save_btn.configure(text="Actualizar material")
        self.msg.configure(text="Los registros previos se actualizan con el nuevo nombre.", text_color=MUTED)

    def delete(self):
        s = self.table.selected()
        if s and messagebox.askyesno("Eliminar", f"¿Eliminar el material «{s[0]}»?\nLos registros históricos se conservan."):
            db.delete_material(str(s[0]))
            self.reset()


# ======================= USUARIOS (solo admin) =======================
class Users(View):
    title, subtitle = "Usuarios", "Solo el administrador puede crear accesos a la app"

    def __init__(self, app):
        super().__init__(app)
        self.body = ctk.CTkFrame(self, fg_color="transparent")
        self.body.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        self.form, self.tcard = card(self.body), card(self.body)
        f = self.form
        label(f, "Nuevo usuario", 17, "bold").pack(anchor="w", padx=22, pady=(20, 0))
        field(f, "Usuario")
        self.u = entry(f, placeholder_text="Mínimo 3 caracteres")
        self.u.pack(fill="x", padx=22)
        field(f, "Contraseña")
        self.p = entry(f, placeholder_text="Mínimo 6 caracteres", show="•")
        self.p.pack(fill="x", padx=22)
        self.admin = ctk.CTkSwitch(f, text="Es administrador", font=font(13), progress_color=ACCENT)
        self.admin.pack(anchor="w", padx=22, pady=16)
        self.msg = label(f, "", 12, color=MUTED, anchor="w", wraplength=280, justify="left")
        self.msg.pack(anchor="w", padx=22)
        button(f, "Crear usuario", self.create, height=46).pack(fill="x", padx=22, pady=(12, 22))
        t = self.tcard
        label(t, "Usuarios", 15, "bold").pack(anchor="w", padx=18, pady=(16, 8))
        self.table = DataTable(t, [("id", "ID", 60), ("user", "Usuario", 220), ("rol", "Rol", 120)], height=10)
        self.table.pack(fill="both", expand=True, padx=14)
        button(t, "Eliminar", self.delete, kind="danger", width=110).pack(anchor="w", padx=14, pady=14)
        self._k = None
        self.bind("<Configure>", self._layout, add="+")

    def _layout(self, e):
        k = e.width >= 1000
        if k != self._k:
            self._k = k
            reflow(self.body, [self.form, self.tcard], 2 if k else 1, weights=(2, 3) if k else None, expand_rows=True)

    def on_show(self):
        self.table.set_rows([(u["id"], u["username"], "Admin" if u["is_admin"] else "Usuario") for u in db.list_users()])

    def create(self):
        u, p = self.u.get().strip(), self.p.get()
        if len(u) < 3 or len(p) < 6:
            return self.msg.configure(text="Usuario (3+) y contraseña (6+) requeridos.", text_color=WARN)
        try:
            db.create_user(u, p, bool(self.admin.get()))
        except sqlite3.IntegrityError:
            return self.msg.configure(text=f"El usuario «{u}» ya existe.", text_color=DANGER)
        self.u.delete(0, "end")
        self.p.delete(0, "end")
        self.msg.configure(text="✔ Usuario creado.", text_color=OK)
        self.on_show()

    def delete(self):
        s = self.table.selected()
        if not s:
            return
        if int(s[0]) == self.app.user["id"]:
            return messagebox.showwarning("Eliminar", "No puedes eliminar tu propio usuario.")
        if messagebox.askyesno("Eliminar", f"¿Eliminar al usuario {s[1]}?"):
            db.delete_user(int(s[0]))
            self.on_show()
