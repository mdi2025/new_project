#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import hashlib
import json
import threading

try:
    import styles
except ImportError:
    # Fallback styles
    class DummyStyles:
        LIGHT = "#f8fafc"
        DARK = "#1e293b"
        PRIMARY = "#3b82f6"
        SECONDARY = "#64748b"
        DANGER = "#ef4444"
        SUCCESS = "#22c55e"
    styles = DummyStyles()

class UsersPage(ttk.Frame):
    def __init__(self, parent):
        ttk.Frame.__init__(self, parent, style="Card.TFrame", padding=25)
        self.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.users = []
        self.filtered = []
        self.page_size = 10
        self.current_page = 0
        
        # Column configuration: [ID, Username, Department, Permissions, Actions]
        self.col_widths = [50, 150, 150, 250, 150]
        self.row_widgets = []  # Cache for row widgets
        
        self._build_ui()
        self.after(100, self.refresh)

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=styles.LIGHT)
        header.pack(fill="x", pady=(0, 20))
        
        ttk.Label(header, text="User Management", style="Title.TLabel").pack(side="left")
        
        ttk.Button(header, text="+ Add User", style="Primary.TButton", 
                   command=self._show_add_user_dialog).pack(side="left", padx=20)
        
        ttk.Button(header, text="Refresh", style="Flat.TButton",
                   command=self.refresh).pack(side="left", padx=10)
        
        # Search
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(header, textvariable=self.search_var,
                                     font=("Segoe UI", 10), bd=0, relief="flat",
                                     width=25,
                                     highlightthickness=1, highlightbackground="#cbd5e1",
                                     highlightcolor=styles.PRIMARY,
                                     fg="#94a3b8")
        self.search_entry.pack(side="right", ipady=8)
        self.search_entry.insert(0, "Search users...")
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)
        self.search_var.trace("w", self._search_data)
        
        # ── Table Area (Matching DrawingRequestsPage) ───────────────────────────
        self.table_container = tk.Frame(self, bg="white", 
                                       highlightthickness=1, highlightbackground="#cbd5e1")
        self.table_container.pack(expand=True, fill="both")
        
        # Header (resizable columns using PanedWindow)
        self.header_paned = tk.PanedWindow(self.table_container, orient="horizontal",
                                          bg="#e2e8f0", bd=0, sashwidth=2, sashpad=0)
        self.header_paned.pack(fill="x")
        
        headers = ["ID", "Username", "Department", "Permissions", "Actions"]
        min_widths = [40, 100, 100, 150, 120]
        self.header_frames = []
        
        for i, h in enumerate(headers):
            f = tk.Frame(self.header_paned, bg="#f1f5f9", width=self.col_widths[i], height=40)
            f.pack_propagate(False)
            lbl = tk.Label(f, text=h, font=("Segoe UI", 10, "bold"),
                           bg="#f1f5f9", fg=styles.DARK)
            lbl.pack(expand=True, fill="both")
            self.header_paned.add(f, minsize=min_widths[i])
            self.header_frames.append(f)
            f.bind("<Configure>", lambda e: self._sync_columns())
            
        # Body
        self.body_frame = tk.Frame(self.table_container, bg="white")
        self.body_frame.pack(expand=True, fill="both")
        
        # ── FIXED Pagination (always at bottom) ──────────────────
        pager = tk.Frame(self, bg=styles.LIGHT, height=50)
        pager.pack(side="bottom", fill="x", pady=10, padx=10)
        pager.pack_propagate(False)
        
        nav_frame = tk.Frame(pager, bg=styles.LIGHT)
        nav_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Button(nav_frame, text="◀ Previous", style="Flat.TButton", command=self._prev_page).pack(side="left", padx=8)
        self.page_label = ttk.Label(nav_frame, text="Page 1 of 1", font=("Segoe UI", 10, "bold"))
        self.page_label.pack(side="left", padx=20)
        ttk.Button(nav_frame, text="Next ▶", style="Flat.TButton", command=self._next_page).pack(side="left", padx=8)
        
        self.records_label = tk.Label(pager, text="", font=("Segoe UI", 9), fg="#64748b", bg=styles.LIGHT)
        self.records_label.place(relx=1.0, rely=0.5, anchor="e", x=-10)

    def _sync_columns(self):
        for i, f in enumerate(self.header_frames):
            try:
                self.col_widths[i] = f.winfo_width()
            except:
                pass
        
        for row_dict in self.row_widgets:
            # Sync data cells
            for i, cell in enumerate(row_dict['cells']):
                try:
                    cell.config(width=self.col_widths[i])
                except:
                    pass
            # Sync action cell (last column)
            try:
                row_dict['action_cell'].config(width=self.col_widths[4])
            except:
                pass

    def refresh(self):
        # Fetch data in thread
        thread = threading.Thread(target=self._fetch_data_thread)
        thread.daemon = True
        thread.start()

    def _fetch_data_thread(self):
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from db_handler import db
            
            query = "SELECT id, admin_name, department, access_tokens FROM drawing_users ORDER BY id"
            data = db.fetch_all(query)
            
            # Post-process permissions
            for user in data:
                tokens = user.get('access_tokens', [])
                if isinstance(tokens, str):
                    try:
                        tokens = json.loads(tokens)
                    except:
                        tokens = []
                user['access_tokens'] = tokens
                
            self.after(0, lambda: self._on_data_ready(data))
        except Exception as e:
            print("Error fetching users: {}".format(e))
            self.after(0, lambda: self._on_data_ready([]))

    def _on_data_ready(self, data):
        self.users = data
        self._search_data() 

    def _search_data(self, *args):
        q = self.search_var.get().lower().strip()
        if q in ("", "search users..."):
            self.filtered = list(self.users)
        else:
            self.filtered = [
                u for u in self.users
                if q in str(u.get("id", "")).lower() or \
                   q in str(u.get("admin_name", "")).lower() or \
                   q in str(u.get("department", "")).lower()
            ]
        self.current_page = 0
        self._load_table()

    def _load_table(self):
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_data = self.filtered[start:end]
        
        for i in range(self.page_size):
            if i < len(page_data):
                user = page_data[i]
                bg = "white" if i % 2 == 0 else "#fbfcfd"
                
                if i >= len(self.row_widgets):
                    # Create new row
                    row_frame = tk.Frame(self.body_frame, bg="white")
                    row_frame.pack(fill="x")
                    
                    cells = []
                    labels = []
                    
                    # Data columns (ID, Username, Department, Permissions)
                    for j in range(4):
                        cell = tk.Frame(row_frame, bg="white", width=self.col_widths[j], height=45)
                        cell.pack_propagate(False)
                        cell.pack(side="left")
                        
                        lbl = tk.Label(cell, font=("Segoe UI", 10), fg="#334155", bg="white")
                        lbl.pack(expand=True, fill="both", padx=5)
                        
                        cells.append(cell)
                        labels.append(lbl)
                    
                    # Action Column
                    action_cell = tk.Frame(row_frame, bg="white", width=self.col_widths[4], height=45)
                    action_cell.pack_propagate(False)
                    action_cell.pack(side="left")
                    
                    btn_frame = tk.Frame(action_cell, bg="white")
                    btn_frame.place(relx=0.5, rely=0.5, anchor="center")
                    
                    # We create buttons but don't assign commands yet
                    edit_btn = ttk.Button(btn_frame, text="Edit", style="Action.TButton")
                    edit_btn.pack(side="left", padx=2)
                    
                    del_btn = ttk.Button(btn_frame, text="Delete", style="Danger.TButton")
                    del_btn.pack(side="left", padx=2)
                    
                    row_dict = {
                        'frame': row_frame,
                        'cells': cells,
                        'labels': labels,
                        'action_cell': action_cell,
                        'btn_frame': btn_frame,
                        'edit_btn': edit_btn,
                        'del_btn': del_btn
                    }
                    self.row_widgets.append(row_dict)
                    
                    row_frame.bind("<Enter>", lambda e, r=row_frame: self._on_row_enter(r))
                    
                else:
                    row_dict = self.row_widgets[i]
                    if not row_dict['frame'].winfo_viewable():
                        row_dict['frame'].pack(fill="x")

                # Update Row Content
                row_dict['frame'].configure(bg=bg)
                row_dict['frame'].bind("<Leave>", lambda e, r=row_dict['frame'], b=bg: self._on_row_leave(r, b))
                
                # Values
                perms = self._format_permissions(user.get('access_tokens', []))
                dept = user.get('department', '') or ''
                vals = [str(user['id']), user['admin_name'], dept, perms]
                
                for j, (lbl, cell, val) in enumerate(zip(row_dict['labels'], row_dict['cells'], vals)):
                    lbl.configure(text=val, bg=bg)
                    cell.configure(bg=bg, width=self.col_widths[j])
                
                # Update Action Column Backgrounds
                row_dict['action_cell'].configure(bg=bg, width=self.col_widths[4])
                row_dict['btn_frame'].configure(bg=bg)
                
                # Commands
                row_dict['edit_btn'].configure(command=lambda u=user: self._show_edit_user_dialog(u))
                row_dict['del_btn'].configure(command=lambda u=user: self._delete_user(u))

            elif i < len(self.row_widgets):
                # Hide unused rows
                self.row_widgets[i]['frame'].pack_forget()

        self._update_pagination()

    def _on_row_enter(self, row):
        highlight_bg = "#f1f5f9"
        row.configure(bg=highlight_bg)
        for child in row.winfo_children():
            child.configure(bg=highlight_bg)
            if isinstance(child, tk.Frame):
                for gc in child.winfo_children():
                    try:
                        gc.configure(bg=highlight_bg)
                    except:
                        pass

    def _on_row_leave(self, row, original_bg):
        row.configure(bg=original_bg)
        for child in row.winfo_children():
            child.configure(bg=original_bg)
            if isinstance(child, tk.Frame):
                for gc in child.winfo_children():
                    try:
                        gc.configure(bg=original_bg)
                    except:
                        pass

    def _format_permissions(self, tokens):
        perm_map = {
            1: "Req",
            2: "Issue",
            3: "Ret",
            4: "Rpt",
            5: "Users"
        }
        names = []
        if not isinstance(tokens, list):
            return ""
        for t in tokens:
            if t in perm_map:
                names.append(perm_map[t])
        return ", ".join(names)

    def _update_pagination(self):
        total = len(self.filtered)
        pages = max(1, (total + self.page_size - 1) // self.page_size)
        current = self.current_page + 1
        self.page_label.config(text="Page {} of {}".format(current, pages))
        
        start = self.current_page * self.page_size + 1 if total > 0 else 0
        end = min((self.current_page + 1) * self.page_size, total)
        self.records_label.config(text="Showing {}–{} of {} records".format(start, end, total))

    def _prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._load_table()

    def _next_page(self):
        if (self.current_page + 1) * self.page_size < len(self.filtered):
            self.current_page += 1
            self._load_table()

    def _clear_placeholder(self, e):
        if self.search_entry.get() == "Search users...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="#334155")

    def _restore_placeholder(self, e):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search users...")
            self.search_entry.config(fg="#94a3b8")

    # ─────────────────────────────────────────────────────────────────
    # Dialogs
    # ─────────────────────────────────────────────────────────────────

    def _show_add_user_dialog(self):
        self._user_dialog("Add New User")

    def _show_edit_user_dialog(self, user):
        self._user_dialog("Edit User", user)

    def _user_dialog(self, title, user=None):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.geometry("500x550")
        dlg.resizable(False, False)
        dlg.configure(bg="white")
        dlg.transient(self)
        dlg.grab_set()
        
        x = self.master.winfo_rootx() + (self.master.winfo_width() // 2) - 250
        y = self.master.winfo_rooty() + (self.master.winfo_height() // 2) - 275
        dlg.geometry("+{}+{}".format(x, y))

        ttk.Label(dlg, text=title, font=("Segoe UI", 14, "bold"), background="white").pack(pady=20)
        
        frm = tk.Frame(dlg, bg="white", padx=40)
        frm.pack(fill="both", expand=True)
        
        ttk.Label(frm, text="Username", background="white").pack(anchor="w")
        username_var = tk.StringVar(value=user['admin_name'] if user else "")
        tk.Entry(frm, textvariable=username_var, font=("Segoe UI", 10)).pack(fill="x", pady=(0, 15))
        
        ttk.Label(frm, text="Password " + ("(Leave blank to keep current)" if user else ""), background="white").pack(anchor="w")
        password_var = tk.StringVar()
        tk.Entry(frm, textvariable=password_var, show="*", font=("Segoe UI", 10)).pack(fill="x", pady=(0, 15))

        # Department
        ttk.Label(frm, text="Department", background="white").pack(anchor="w")
        dept_var = tk.StringVar(value=user.get('department', '') if user else "")
        tk.Entry(frm, textvariable=dept_var, font=("Segoe UI", 10)).pack(fill="x", pady=(0, 15))
        
        ttk.Label(frm, text="Permissions", background="white", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(5,5))
        
        # Scrollable Permissions Area
        perm_container = tk.Frame(frm, bg="white", highlightthickness=1, highlightbackground="#e2e8f0")
        perm_container.pack(fill="x", pady=(0, 15), ipady=5)
        
        canvas = tk.Canvas(perm_container, bg="white", height=150, highlightthickness=0)
        scrollbar = ttk.Scrollbar(perm_container, orient="vertical", command=canvas.yview)
        
        perm_frame = tk.Frame(canvas, bg="white")
        perm_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=perm_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse Wheel Support (Linux)
        def _on_mousewheel(event):
            if event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")
        
        canvas.bind("<Button-4>", _on_mousewheel)
        canvas.bind("<Button-5>", _on_mousewheel)
        
        def bind_tree(widget):
            widget.bind("<Button-4>", _on_mousewheel)
            widget.bind("<Button-5>", _on_mousewheel)
            for child in widget.winfo_children():
                bind_tree(child)
        
        bind_tree(perm_frame)
        
        perms_map = {
            1: "Drawing Requests",
            2: "Drawing Issuance",
            3: "Return",
            4: "Reports",
            5: "User Management"
        }
        
        perm_vars = {}
        current_perms = user['access_tokens'] if user else []
        
        for i, (pid, pname) in enumerate(sorted(perms_map.items())):
            var = tk.BooleanVar(value=pid in current_perms)
            perm_vars[pid] = var
            # Use grid for 2-column layout
            row = i // 2
            col = i % 2
            tk.Checkbutton(perm_frame, text=pname, variable=var, bg="white", 
                           activebackground="white").grid(row=row, column=col, sticky="w", padx=10, pady=2)
        
        def save():
            uname = username_var.get().strip()
            pwd = password_var.get().strip()
            dept = dept_var.get().strip()
            selected_perms = [pid for pid, var in perm_vars.items() if var.get()]
            
            if not uname:
                messagebox.showerror("Error", "Username is required", parent=dlg)
                return
                
            if not user and not pwd:
                messagebox.showerror("Error", "Password is required for new users", parent=dlg)
                return
            
            if user:
                self._update_user_db(user['id'], uname, pwd, dept, selected_perms, dlg)
            else:
                self._create_user_db(uname, pwd, dept, selected_perms, dlg)
        
        ttk.Button(dlg, text="Save User", style="Primary.TButton", 
                   command=save).pack(pady=20)

    def _create_user_db(self, username, password, department, perms, dlg):
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from db_handler import db
            
            chk = db.fetch_all("SELECT id FROM drawing_users WHERE admin_name=%s", (username,))
            if chk:
                messagebox.showerror("Error", "Username already exists", parent=dlg)
                return

            pwd_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
            perms_json = json.dumps(perms)
            
            query = "INSERT INTO drawing_users (admin_name, admin_pass, department, access_tokens) VALUES (%s, %s, %s, %s)"
            if db.execute_query(query, (username, pwd_hash, department, perms_json)):
                messagebox.showinfo("Success", "User created successfully", parent=dlg)
                dlg.destroy()
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to create user", parent=dlg)
                
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=dlg)

    def _update_user_db(self, uid, username, password, department, perms, dlg):
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from db_handler import db
            
            perms_json = json.dumps(perms)
            
            if password:
                pwd_hash = hashlib.md5(password.encode('utf-8')).hexdigest()
                query = "UPDATE drawing_users SET admin_name=%s, admin_pass=%s, department=%s, access_tokens=%s WHERE id=%s"
                params = (username, pwd_hash, department, perms_json, uid)
            else:
                query = "UPDATE drawing_users SET admin_name=%s, department=%s, access_tokens=%s WHERE id=%s"
                params = (username, department, perms_json, uid)
                
            if db.execute_query(query, params):
                messagebox.showinfo("Success", "User updated successfully", parent=dlg)
                dlg.destroy()
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to update user", parent=dlg)

        except Exception as e:
            messagebox.showerror("Error", str(e), parent=dlg)

    def _delete_user(self, user):
        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete user '{}'?".format(user['admin_name'])):
            return
            
        try:
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from db_handler import db
            
            if db.execute_query("DELETE FROM drawing_users WHERE id=%s", (user['id'],)):
                messagebox.showinfo("Success", "User deleted")
                self.refresh()
            else:
                messagebox.showerror("Error", "Failed to delete user")
        except Exception as e:
             messagebox.showerror("Error", str(e))
