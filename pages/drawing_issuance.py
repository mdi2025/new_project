import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime

# Fallback styles if styles module is missing
try:
    import styles
except ImportError:
    class DummyStyles:
        LIGHT = "#f8fafc"
        DARK  = "#1e293b"
        PRIMARY = "#3b82f6"
    styles = DummyStyles()

class DrawingIssuancePage(ttk.Frame):
    def __init__(self, parent, username="User"):
        ttk.Frame.__init__(self, parent, style="Card.TFrame", padding=25)
        self.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.username = username
        self.drawings = self._generate_static_data()
        self.page_size = 10
        self.current_page = 0
        self.filtered = list(self.drawings)
        
        # Column configuration: [Drawing ID, Revision, Status, Requested By, Actions]
        self.col_widths = [150, 80, 100, 200, 150]  # Wider for two buttons
        self.row_widgets = []
        
        self._build_ui()

    def _generate_static_data(self):
        """Returns static data for requested drawings."""
        base = [
            {"no": "MDI-DRW-101", "rev": "A.0", "status": "REQUESTED", "requested_by": "John Doe"},
            {"no": "MDI-DRW-105", "rev": "1.2", "status": "REQUESTED", "requested_by": "Jane Smith"},
            {"no": "ENG-2024-001", "rev": "0",   "status": "REQUESTED", "requested_by": "Robert Brown"},
            {"no": "ENG-2024-002", "rev": "0",   "status": "REQUESTED", "requested_by": "Sarah Wilson"},
            {"no": "ST-9982-X",    "rev": "B",   "status": "REQUESTED", "requested_by": "Michael Scott"},
        ]
        # Repeat to have enough rows for testing pagination
        return base * 8

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────
        header = tk.Frame(self, bg=styles.LIGHT)
        header.pack(fill="x", pady=(0, 20))

        ttk.Label(header, text="Drawing Issuance", style="Title.TLabel").pack(side="left")

        # Search
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(header, textvariable=self.search_var,
                                     font=("Segoe UI", 10), bd=0, relief="flat",
                                     width=25, highlightthickness=1,
                                     highlightbackground="#cbd5e1",
                                     highlightcolor=styles.PRIMARY)
        self.search_entry.pack(side="right", ipady=8)
        self.search_entry.insert(0, "Search requests...")
        
        self.search_entry.bind("<FocusIn>",   self._clear_placeholder)
        self.search_entry.bind("<FocusOut>",  self._restore_placeholder)
        self.search_var.trace("w", self._search_data)

        # ── FIXED Pagination (always at bottom) ──────────────────────────
        pager = tk.Frame(self, bg=styles.LIGHT, height=50)
        pager.pack(side="bottom", fill="x", pady=10, padx=10)
        pager.pack_propagate(False)   # prevents height collapse

        # Centered navigation
        nav_frame = tk.Frame(pager, bg=styles.LIGHT)
        nav_frame.place(relx=0.5, rely=0.5, anchor="center")

        ttk.Button(nav_frame, text="◀ Previous", style="Flat.TButton",
                   command=self._prev_page).pack(side="left", padx=8)

        self.page_label = ttk.Label(nav_frame, text="Page 1 of 1",
                                     font=("Segoe UI", 10, "bold"))
        self.page_label.pack(side="left", padx=20)

        ttk.Button(nav_frame, text="Next ▶", style="Flat.TButton",
                   command=self._next_page).pack(side="left", padx=8)

        # Records info (right aligned)
        self.records_label = tk.Label(pager, text="",
                                      font=("Segoe UI", 9), fg="#64748b",
                                      bg=styles.LIGHT)
        self.records_label.place(relx=1.0, rely=0.5, anchor="e", x=-10)

        # ── Table Area ───────────────────────────────────────────────────
        self.table_container = tk.Frame(self, bg="white",
                                        highlightthickness=1,
                                        highlightbackground="#cbd5e1")
        self.table_container.pack(expand=True, fill="both")

        # Resizable header
        self.header_paned = tk.PanedWindow(self.table_container, orient="horizontal",
                                           bg="#e2e8f0", bd=0, sashwidth=2, sashpad=0)
        self.header_paned.pack(fill="x")
        
        headers = ["Drawing ID", "Revision", "Status", "Requested By", "Actions"]
        min_widths = [110, 70, 80, 150, 140]
        self.header_frames = []
        
        for i, h in enumerate(headers):
            f = tk.Frame(self.header_paned, bg="#f1f5f9",
                         width=self.col_widths[i], height=40)
            f.pack_propagate(False)
            lbl = tk.Label(f, text=h, font=("Segoe UI", 10, "bold"),
                           bg="#f1f5f9", fg=styles.DARK)
            lbl.pack(expand=True, fill="both")
            self.header_paned.add(f, minsize=min_widths[i])
            self.header_frames.append(f)
            f.bind("<Configure>", lambda e: self._sync_columns())

        self.body_frame = tk.Frame(self.table_container, bg="white")
        self.body_frame.pack(expand=True, fill="both")

        self._load_table()

    def _sync_columns(self):
        for i, f in enumerate(self.header_frames):
            try:
                self.col_widths[i] = f.winfo_width()
            except:
                pass
        
        for row_dict in self.row_widgets:
            for i, cell in enumerate(row_dict['cells']):
                try:
                    cell.config(width=self.col_widths[i])
                except:
                    pass

    def _clear_placeholder(self, e):
        if self.search_entry.get() == "Search requests...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="#334155")

    def _restore_placeholder(self, e):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search requests...")
            self.search_entry.config(fg="#94a3b8")

    def _load_table(self):
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_data = self.filtered[start:end]
        
        for i in range(self.page_size):
            if i < len(page_data):
                d = page_data[i]
                bg = "white" if i % 2 == 0 else "#fbfcfd"
                
                if i >= len(self.row_widgets):
                    row_frame = tk.Frame(self.body_frame, bg="white")
                    row_frame.pack(fill="x")
                    
                    cells = []
                    labels = []
                    for j in range(4):
                        cell = tk.Frame(row_frame, bg="white",
                                        width=self.col_widths[j], height=45)
                        cell.pack_propagate(False)
                        cell.pack(side="left")
                        lbl = tk.Label(cell, font=("Segoe UI", 10),
                                       fg="#334155", bg="white")
                        lbl.pack(expand=True, fill="both", padx=5)
                        cells.append(cell)
                        labels.append(lbl)
                    
                    # Action cell - two buttons
                    action_cell = tk.Frame(row_frame, bg="white",
                                           width=self.col_widths[4], height=45)
                    action_cell.pack_propagate(False)
                    action_cell.pack(side="left")
                    
                    btn_frame = tk.Frame(action_cell, bg="white")
                    btn_frame.pack(expand=True)
                    
                    issue_btn = tk.Button(btn_frame, text="Issue", bg="#16a34a", fg="white",
                                          font=("Segoe UI", 9, "bold"), relief="flat", padx=8)
                    issue_btn.pack(side="left", padx=3)
                    
                    reject_btn = tk.Button(btn_frame, text="Reject", bg="#dc2626", fg="white",
                                           font=("Segoe UI", 9, "bold"), relief="flat", padx=8)
                    reject_btn.pack(side="left", padx=3)
                    
                    cells.append(action_cell)
                    
                    row_dict = {
                        'frame': row_frame,
                        'cells': cells,
                        'labels': labels,
                        'action_cell': action_cell,
                        'issue_btn': issue_btn,
                        'reject_btn': reject_btn,
                        'btn_frame': btn_frame
                    }
                    self.row_widgets.append(row_dict)
                
                else:
                    row_dict = self.row_widgets[i]
                    if not row_dict['frame'].winfo_viewable():
                        row_dict['frame'].pack(fill="x")
                
                row_dict['frame'].configure(bg=bg)
                vals = [d["no"], d["rev"], d["status"].upper(), d["requested_by"]]
                
                for j, (lbl, cell, val) in enumerate(zip(row_dict['labels'], row_dict['cells'][:4], vals)):
                    lbl.configure(text=val, bg=bg)
                    cell.configure(bg=bg)
                
                row_dict['action_cell'].configure(width=self.col_widths[4], bg=bg)
                row_dict['btn_frame'].configure(bg=bg)
                
                row_dict['issue_btn'].configure(command=lambda dn=d["no"]: self._handle_issue(dn))
                row_dict['reject_btn'].configure(command=lambda dn=d["no"]: self._handle_reject(dn))
            
            elif i < len(self.row_widgets):
                self.row_widgets[i]['frame'].pack_forget()

        # Update pagination info - Python 3.4 compatible (no f-strings)
        total_records = len(self.filtered)
        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
        current = self.current_page + 1
        
        start_record = start + 1 if total_records > 0 else 0
        end_record   = min(end, total_records)
        
        self.page_label.config(text="Page {} of {}".format(current, total_pages))
        self.records_label.config(text="Showing {}–{} of {} records".format(
            start_record, end_record, total_records))

    def _handle_issue(self, drawing_no):
        messagebox.showinfo("Issuance", "Drawing {} has been issued successfully.".format(drawing_no))
        self.drawings = [d for d in self.drawings if d["no"] != drawing_no]
        self.filtered = list(self.drawings)
        # Keep current page in valid range
        max_page = max(0, (len(self.filtered) - 1) // self.page_size)
        self.current_page = min(self.current_page, max_page)
        self._load_table()

    def _handle_reject(self, drawing_no):
        if messagebox.askyesno("Reject", "Are you sure you want to reject the request for {}?".format(drawing_no)):
            messagebox.showwarning("Rejected", "Request for {} rejected.".format(drawing_no))
            self.drawings = [d for d in self.drawings if d["no"] != drawing_no]
            self.filtered = list(self.drawings)
            max_page = max(0, (len(self.filtered) - 1) // self.page_size)
            self.current_page = min(self.current_page, max_page)
            self._load_table()

    def _search_data(self, *args):
        q = self.search_var.get().lower().strip()
        if q in ("", "search requests..."):
            self.filtered = list(self.drawings)
        else:
            self.filtered = [
                d for d in self.drawings
                if q in str(d["no"]).lower()
                or q in str(d["rev"]).lower()
                or q in str(d["status"]).lower()
                or q in str(d["requested_by"]).lower()
            ]
        self.current_page = 0
        self._load_table()

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._load_table()

    def _next_page(self):
        if (self.current_page + 1) * self.page_size < len(self.filtered):
            self.current_page += 1
            self._load_table()