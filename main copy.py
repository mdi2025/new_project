import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import math

# ── Database Configuration ───────────────────────────────────────────────
DB_CONFIG = {
    'host': 'db.dev.erp.mdi',
    'user': 'erp',
    'password': 'erpdeveloper',
    'database': 'mdiacc',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

VALID_USERS = {"admin": "123456", "user": "password"}

def center_window(win, w=1100, h=720):
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    win.geometry("{}x{}+{}+{}".format(w, h, x, y))

# ── Reusable Login Window ────────────────────────────────────────────────
def show_login_window():
    login_win = tk.Tk()
    login_win.title("Login - DMS")
    login_win.configure(bg="#ecf0f1")
    center_window(login_win, 420, 480)
    login_win.resizable(False, False)

    tk.Label(login_win,
             text="DMS",
             font=("Helvetica", 48, "bold"),
             fg="#3498db",
             bg="#ecf0f1").pack(pady=(60,10))

    tk.Label(login_win,
             text="Drawing Management System",
             font=("Helvetica", 14),
             fg="#7f8c8d",
             bg="#ecf0f1").pack(pady=(0,50))

    frame = tk.Frame(login_win, bg="#ecf0f1")
    frame.pack(padx=60, fill="x")

    tk.Label(frame,
             text="Username",
             font=("Helvetica", 11, "bold"),
             bg="#ecf0f1",
             fg="#2c3e50").pack(anchor="w", pady=(0,6))

    entry_user = tk.Entry(frame,
                          font=("Helvetica", 13),
                          bg="white",
                          relief="flat",
                          highlightthickness=2,
                          highlightbackground="#bdc3c7",
                          highlightcolor="#3498db")
    entry_user.pack(fill="x", ipady=8, pady=(0,20))

    tk.Label(frame,
             text="Password",
             font=("Helvetica", 11, "bold"),
             bg="#ecf0f1",
             fg="#2c3e50").pack(anchor="w", pady=(0,6))

    entry_pass = tk.Entry(frame,
                          font=("Helvetica", 13),
                          show="*",
                          bg="white",
                          relief="flat",
                          highlightthickness=2,
                          highlightbackground="#bdc3c7",
                          highlightcolor="#3498db")
    entry_pass.pack(fill="x", ipady=8, pady=(0,30))

    def attempt_login():
        user = entry_user.get().strip()
        pwd = entry_pass.get()
        if user in VALID_USERS and VALID_USERS[user] == pwd:
            login_win.destroy()
            app = DrawingApp(user)
            app.mainloop()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")

    btn = tk.Button(frame,
                    text="SIGN IN",
                    command=attempt_login,
                    font=("Helvetica", 13, "bold"),
                    bg="#3498db",
                    fg="white",
                    relief="flat",
                    activebackground="#2980b9",
                    bd=0,
                    cursor="hand2")
    btn.pack(fill="x", ipady=14)

    login_win.bind("<Return>", lambda e: attempt_login())
    entry_user.focus()

    login_win.mainloop()


class DrawingApp(tk.Tk):
    def __init__(self, username):
        super().__init__()
        self.title("Drawing Management System")
        self.configure(bg="#f0f2f5")
        center_window(self, 1100, 720)
        self.minsize(980, 650)
        self.username = username

        self.sidebar_expanded = tk.BooleanVar(value=True)
        self.current_frame = None
        self.style = ttk.Style()
        self.style.theme_use('clam')

        self.menu_items = [
            "Drawing Requests",
            "Drawing Issuance",
            "Reports",
            "Drawing Receive",
            "Settings"
        ]

        # Pagination settings
        self.rows_per_page = 15
        self.current_page = 1
        self.all_drawings = []
        self.current_tree = None
        self.records_label = None

        self._setup_style()
        self._create_widgets()
        self._show_page("Drawing Requests")

    def logout(self):
        self.destroy()
        show_login_window()

    def _setup_style(self):
        self.style.configure("Sidebar.TFrame", background="#2c3e50")
        self.style.configure("Sidebar.TLabel",
                             background="#2c3e50",
                             foreground="white",
                             font=("Helvetica", 13))
        self.style.configure("Sidebar.Active.TLabel",
                             background="#34495e",
                             foreground="#3498db",
                             font=("Helvetica", 13, "bold"))

        self.style.configure("Title.TLabel",
                             font=("Helvetica", 22, "bold"),
                             background="#f0f2f5",
                             foreground="#2c3e50")

        self.style.configure("Placeholder.TLabel",
                             foreground="#7f8c8d",
                             background="#f0f2f5",
                             font=("Helvetica", 14))

        self.style.configure("Accent.TButton",
                             font=("Helvetica", 12, "bold"),
                             background="#3498db",
                             foreground="white",
                             padding=8)
        self.style.map("Accent.TButton",
                       background=[("active", "#2980b9")])

        self.style.configure("Modern.Treeview",
                             background="#ffffff",
                             foreground="#2c3e50",
                             fieldbackground="#ffffff",
                             rowheight=30,
                             borderwidth=0,
                             font=("Helvetica", 11))
        self.style.configure("Modern.Treeview.Heading",
                             background="#3498db",
                             foreground="white",
                             font=("Helvetica", 12, "bold"),
                             relief="flat",
                             padding=8)
        self.style.map("Modern.Treeview",
                       background=[("selected", "#d4e6ff")],
                       foreground=[("selected", "#1a3c6d")])

        self.style.configure("Modern.Vertical.TScrollbar",
                             background="#bdc3c7",
                             troughcolor="#ecf0f1",
                             arrowcolor="#2c3e50")
        self.style.map("Modern.Vertical.TScrollbar",
                       background=[("active", "#95a5a6")])

    def _create_widgets(self):
        # Header now matches sidebar color
        header = tk.Frame(self, bg="#2c3e50", height=70)
        header.pack(fill="x")

        tk.Label(header,
                 text="Drawing Management System",
                 font=("Helvetica", 20, "bold"),
                 bg="#2c3e50",
                 fg="white",
                 padx=25).pack(side="left", pady=15)

        top_right = tk.Frame(header, bg="#2c3e50")
        top_right.pack(side="right", padx=20, pady=10)

        tk.Label(top_right,
                 text=self.username,
                 font=("Helvetica", 11),
                 bg="#2c3e50",
                 fg="white").pack(side="left", padx=(0,15))

        logout_btn = tk.Button(top_right,
                               text="Logout",
                               font=("Helvetica", 11, "bold"),
                               bg="#e74c3c",
                               fg="white",
                               relief="flat",
                               bd=0,
                               activebackground="#c0392b",
                               padx=12,
                               pady=6,
                               cursor="hand2",
                               command=self.logout)
        logout_btn.pack(side="left")

        self.main_container = tk.Frame(self, bg="#f0f2f5")
        self.main_container.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(self.main_container, bg="#2c3e50", width=240)
        self.sidebar.pack(side="left", fill="y")

        self.toggle_btn = tk.Button(self.sidebar,
                                    text="<",
                                    font=("Helvetica", 14, "bold"),
                                    bg="#34495e",
                                    fg="white",
                                    relief="flat",
                                    bd=0,
                                    activebackground="#1abc9c",
                                    width=3,
                                    command=self._toggle_sidebar)
        self.toggle_btn.pack(anchor="ne", pady=8, padx=8)

        self.sidebar_content = tk.Frame(self.sidebar, bg="#2c3e50")
        self.sidebar_content.pack(fill="both", expand=True)

        self.menu_labels = {}
        for text in self.menu_items:
            f = tk.Frame(self.sidebar_content, bg="#2c3e50")
            f.pack(fill="x", pady=3)

            lbl = ttk.Label(f,
                            text=text,
                            style="Sidebar.TLabel",
                            padding=14,
                            anchor="w")
            lbl.pack(fill="x")
            lbl.bind("<Button-1>", lambda e, t=text: self._show_page(t))
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(style="Sidebar.Active.TLabel") if l != getattr(self, 'active_label', None) else None)
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(style="Sidebar.TLabel") if l != getattr(self, 'active_label', None) else None)
            self.menu_labels[text] = lbl

        self.content = tk.Frame(self.main_container, bg="#f0f2f5")
        self.content.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.pages = {}

    def _toggle_sidebar(self):
        expanded = self.sidebar_expanded.get()
        if expanded:
            self.sidebar.configure(width=50)
            self.toggle_btn.configure(text=">")
            for lbl in self.menu_labels.values():
                txt = lbl.cget("text")
                lbl.configure(text=txt[:3] if len(txt) > 2 else txt)
            self.sidebar_expanded.set(False)
        else:
            self.sidebar.configure(width=240)
            self.toggle_btn.configure(text="<")
            for text in self.menu_items:
                self.menu_labels[text].configure(text=text)
            self.sidebar_expanded.set(True)
        self.update_idletasks()

    def _load_drawings_data(self):
        try:
            conn = pymysql.connect(**DB_CONFIG)
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, drawing_no, title, latest_revision,
                           approve_date, current_status
                    FROM drawings_master_bal
                    ORDER BY id DESC LIMIT 200
                """)
                return cur.fetchall()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            return []
        finally:
            if 'conn' in locals():
                conn.close()

    def _request_drawing(self, drawing_id, drawing_no):
        if messagebox.askyesno("Confirm Request",
                               "Request drawing {} ({}) ?".format(drawing_no, drawing_id)):
            messagebox.showinfo(
                "Request Submitted",
                "Request sent for drawing:\n\n"
                "ID: {}\n"
                "Drawing No: {}\n\n"
                "(Requested by: {})".format(drawing_id, drawing_no, self.username)
            )

    def _populate_treeview(self, page):
        if not self.current_tree:
            return

        self.current_tree.delete(*self.current_tree.get_children())

        start = (page - 1) * self.rows_per_page
        end = min(start + self.rows_per_page, len(self.all_drawings))
        page_data = self.all_drawings[start:end]

        for row in page_data:
            iid = str(row.get('id', 'unknown'))
            self.current_tree.insert("", "end", iid=iid, values=(
                row.get('id', ''),
                row.get('drawing_no', ''),
                row.get('title', ''),
                row.get('latest_revision') or "—",
                row.get('approve_date') or "—",
                row.get('current_status', ''),
                "[Request]"
            ))

        # Update records showing label
        if self.records_label:
            showing_from = start + 1
            showing_to = end
            total = len(self.all_drawings)
            self.records_label.config(text="Showing {} to {} of {} records".format(showing_from, showing_to, total))

    def _update_pagination_controls(self):
        total_pages = math.ceil(len(self.all_drawings) / self.rows_per_page) if self.all_drawings else 1

        self.page_label.config(text="Page {} of {}".format(self.current_page, total_pages))

        self.prev_button.config(state="normal" if self.current_page > 1 else "disabled")
        self.next_button.config(state="normal" if self.current_page < total_pages else "disabled")

    def _prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self._populate_treeview(self.current_page)
            self._update_pagination_controls()

    def _next_page(self):
        total_pages = math.ceil(len(self.all_drawings) / self.rows_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self._populate_treeview(self.current_page)
            self._update_pagination_controls()

    def _show_page(self, page_name):
        if hasattr(self, 'active_label') and self.active_label:
            self.active_label.configure(style="Sidebar.TLabel")

        self.active_label = self.menu_labels.get(page_name)
        if self.active_label:
            self.active_label.configure(style="Sidebar.Active.TLabel")

        if self.current_frame:
            self.current_frame.pack_forget()

        if page_name not in self.pages:
            frame = tk.Frame(self.content, bg="#f0f2f5")
            ttk.Label(frame, text=page_name, style="Title.TLabel").pack(anchor="w", pady=(10, 20))

            if page_name == "Drawing Requests":
                controls = tk.Frame(frame, bg="#f0f2f5")
                controls.pack(fill="x", pady=(0, 12))

                ttk.Button(controls,
                           text="New Drawing Request",
                           style="Accent.TButton",
                           command=lambda: messagebox.showinfo("Action", "New request form")).pack(side="left")

                search_frame = tk.Frame(controls, bg="#f0f2f5")
                search_frame.pack(side="right", padx=5)

                ttk.Label(search_frame,
                          text="Search:",
                          font=("Helvetica", 11),
                          background="#f0f2f5").pack(side="left", padx=(0, 8))

                self.search_var = tk.StringVar()
                search_entry = ttk.Entry(search_frame,
                                         textvariable=self.search_var,
                                         font=("Helvetica", 11),
                                         width=30)
                search_entry.pack(side="left", ipady=3)
                search_entry.focus()

                self.current_tree = None
                self.all_drawings = []

                def filter_drawings(event=None):
                    if not self.current_tree:
                        return
                    query = self.search_var.get().strip().lower()
                    self.current_tree.delete(*self.current_tree.get_children())

                    filtered = []
                    for row in self.all_drawings:
                        searchable = " ".join(str(v).lower() for v in [
                            row.get('drawing_no', ''),
                            row.get('title', ''),
                            row.get('latest_revision', ''),
                            row.get('current_status', '')
                        ])
                        if not query or query in searchable:
                            filtered.append(row)

                    self.current_page = 1
                    self._populate_treeview(self.current_page)
                    self._update_pagination_controls()

                search_entry.bind("<KeyRelease>", filter_drawings)

                table_frame = tk.Frame(frame, bg="#f0f2f5")
                table_frame.pack(fill="both", expand=True)

                scrollbar = ttk.Scrollbar(table_frame,
                                          orient="vertical",
                                          style="Modern.Vertical.TScrollbar")
                scrollbar.pack(side="right", fill="y")

                columns = ("id", "drawing_no", "title", "revision", "approve_date", "status", "action")
                tree = ttk.Treeview(table_frame,
                                    columns=columns,
                                    show="headings",
                                    style="Modern.Treeview",
                                    yscrollcommand=scrollbar.set)
                scrollbar.config(command=tree.yview)

                tree.heading("id", text="ID")
                tree.heading("drawing_no", text="Drawing No.")
                tree.heading("title", text="Title")
                tree.heading("revision", text="Rev.")
                tree.heading("approve_date", text="Approve Date")
                tree.heading("status", text="Status")
                tree.heading("action", text="Action")

                tree.column("id", width=60, anchor="center")
                tree.column("drawing_no", width=140, anchor="w")
                tree.column("title", width=260, anchor="w")
                tree.column("revision", width=70, anchor="center")
                tree.column("approve_date", width=110, anchor="center")
                tree.column("status", width=130, anchor="center")
                tree.column("action", width=100, anchor="center")

                def on_motion(event):
                    col = tree.identify_column(event.x)
                    if col == "#7":
                        tree.configure(cursor="hand2")
                    else:
                        tree.configure(cursor="")

                tree.bind("<Motion>", on_motion)

                def on_click(event):
                    region = tree.identify("region", event.x, event.y)
                    if region != "cell":
                        return

                    column = tree.identify_column(event.x)
                    iid = tree.identify_row(event.y)

                    if not iid or column != "#7":
                        return

                    values = tree.item(iid, "values")
                    if values and values[6].strip() == "[Request]":
                        drawing_id = values[0]
                        drawing_no = values[1]
                        self._request_drawing(drawing_id, drawing_no)

                tree.bind("<Button-1>", on_click)

                tree.pack(fill="both", expand=True)

                self.current_tree = tree

                # ── Pagination + records info ────────────────────────────────────
                pagination_frame = tk.Frame(frame, bg="#f0f2f5")
                pagination_frame.pack(fill="x", pady=(5, 0))

                # Left side - Previous / Page info / Next
                nav_frame = tk.Frame(pagination_frame, bg="#f0f2f5")
                nav_frame.pack(side="left")

                self.prev_button = ttk.Button(nav_frame, text="Previous", style="Accent.TButton", command=self._prev_page)
                self.prev_button.pack(side="left", padx=(0, 8))

                self.page_label = ttk.Label(nav_frame, text="Page 1 of 1", font=("Helvetica", 11))
                self.page_label.pack(side="left", padx=8)

                self.next_button = ttk.Button(nav_frame, text="Next", style="Accent.TButton", command=self._next_page)
                self.next_button.pack(side="left", padx=(8, 0))

                # Right side - Showing records info
                self.records_label = ttk.Label(pagination_frame, text="Showing 0 to 0 of 0 records", font=("Helvetica", 11))
                self.records_label.pack(side="right")

                # Load data and show first page
                self.all_drawings = self._load_drawings_data()
                self.current_page = 1
                self._populate_treeview(self.current_page)
                self._update_pagination_controls()

            else:
                ttk.Label(frame,
                          text=page_name + " page (placeholder)",
                          style="Placeholder.TLabel").pack(pady=80)

            self.pages[page_name] = frame

        self.current_frame = self.pages[page_name]
        self.current_frame.pack(fill="both", expand=True)


# ── Start the application ────────────────────────────────────────────────
show_login_window()