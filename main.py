"""EnCore · Control de Materiales — punto de entrada.  Ejecuta:  python main.py"""
import os

import customtkinter as ctk

import database as db
from theme import *
from views import Dashboard, Employees, Materials, Records, Users

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class Login(ctk.CTkFrame):
    def __init__(self, app):
        super().__init__(app, fg_color=BG)
        self.app = app
        self.setup = db.user_count() == 0
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        c = card(self)
        c.grid(row=0, column=0)
        box = ctk.CTkFrame(c, fg_color="transparent")
        box.pack(padx=44, pady=36)
        ctk.CTkLabel(box, text="", image=logo(200)).pack(pady=(0, 18))
        label(box, "Crear cuenta de administrador" if self.setup else "Bienvenido", 22, "bold").pack()
        label(box, "Primer uso: define tu usuario y contraseña" if self.setup else "Inicia sesión para continuar",
              12, color=MUTED).pack(pady=(4, 20))
        self.u = entry(box, placeholder_text="Usuario", width=300)
        self.u.pack(pady=6)
        self.p = entry(box, placeholder_text="Contraseña", show="•", width=300)
        self.p.pack(pady=6)
        self.p2 = None
        if self.setup:
            self.p2 = entry(box, placeholder_text="Confirmar contraseña", show="•", width=300)
            self.p2.pack(pady=6)
        self.err = label(box, "", 12, color=DANGER, wraplength=300)
        self.err.pack(pady=(4, 8))
        button(box, "Crear administrador" if self.setup else "Iniciar sesión", self.submit,
               width=300, height=46).pack()
        for e in (self.u, self.p, self.p2):
            if e:
                e.bind("<Return>", lambda ev: self.submit())
        self.after(200, self.u.focus)

    def submit(self):
        u, p = self.u.get().strip(), self.p.get()
        if self.setup:
            if len(u) < 3 or len(p) < 6:
                return self.err.configure(text="Usuario (3+ caracteres) y contraseña (6+) requeridos.")
            if p != self.p2.get():
                return self.err.configure(text="Las contraseñas no coinciden.")
            db.create_user(u, p, True)
        row = db.verify_user(u, p)
        if not row:
            return self.err.configure(text="Usuario o contraseña incorrectos.")
        self.app.on_login(row)


class App(ctk.CTk):
    def __init__(self):
        auto_scale()
        super().__init__()
        db.init_db()
        self.title("EnCore · Control de Materiales")
        self.geometry("1280x800")
        self.minsize(900, 620)
        self._set_icon()
        self.configure(fg_color=BG)
        self.user, self.views, self.current = None, {}, None
        self.bind("<F11>", lambda _: self.attributes("-fullscreen", not self.attributes("-fullscreen")))
        self.bind("<Map>", self._fit_screen, add="+")
        self.show_login()
        self._fit_screen()

    def _set_icon(self):
        """Ícono de la ventana y barra de tareas (solo el favicon, no el logo)."""
        ico = os.path.join(BASE, "assets", "favicon.ico")
        if not os.path.exists(ico):
            return
        try:
            self.iconbitmap(ico)
        except Exception:
            pass

    def _fit_screen(self, _=None):
        self.after(120, self._zoom)

    def _zoom(self):
        try:
            self.state("zoomed")
        except Exception:
            pass

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()
        self.views, self.current = {}, None

    def show_login(self):
        self._clear()
        self.user = None
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        Login(self).grid(row=0, column=0, sticky="nsew")

    def on_login(self, user):
        self.user = user
        self._clear()
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        sb = ctk.CTkFrame(self, fg_color=SIDEBAR, corner_radius=0, width=236)
        sb.grid(row=0, column=0, sticky="ns")
        sb.pack_propagate(False)
        self.content = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)

        ctk.CTkLabel(sb, text="", image=logo(170)).pack(pady=(28, 24))
        self.classes = {"dashboard": Dashboard, "records": Records,
                        "employees": Employees, "materials": Materials}
        items = [("dashboard", "Dashboard"), ("records", "Registros"),
                 ("employees", "Empleados"), ("materials", "Materiales")]
        if user["is_admin"]:
            self.classes["users"] = Users
            items.append(("users", "Usuarios"))
        self.nav = {}
        for key, text in items:
            b = ctk.CTkButton(sb, text=text, anchor="w", height=46, corner_radius=14, fg_color="transparent",
                              hover_color=CARD2, text_color=TEXT, font=font(14, "bold"),
                              command=lambda k=key: self.show(k))
            b.pack(fill="x", padx=16, pady=3)
            self.nav[key] = b
        button(sb, "Cerrar sesión", self.show_login, kind="ghost").pack(side="bottom", fill="x", padx=16, pady=20)
        label(sb, f"{user['username']}  ·  {'Admin' if user['is_admin'] else 'Usuario'}", 12,
              color=MUTED).pack(side="bottom", pady=(0, 4))
        self.show("dashboard")

    def show(self, key):
        if self.current:
            self.views[self.current].grid_forget()
            self.nav[self.current].configure(fg_color="transparent")
        if key not in self.views:
            self.views[key] = self.classes[key](self)
        self.current = key
        self.nav[key].configure(fg_color=BLUE)
        self.views[key].grid(row=0, column=0, sticky="nsew")
        self.views[key].on_show()


if __name__ == "__main__":
    App().mainloop()
