#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import styles
import datetime

class DrawingRequestsPage(ttk.Frame):
    def __init__(self, parent, username="User"):
        ttk.Frame.__init__(self, parent, style="Card.TFrame", padding=25)
        self.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.username = username
        self.drawings = self._generate_data()
        self.page_size = 10
        self.current_page = 0
        self.filtered = list(self.drawings)
        
        # Column configuration: [Drawing ID, Revision, Status, Requested By, Action]
        self.col_widths = [150, 80, 100, 200, 120]
        self.row_widgets = []  # Cache for row widgets to prevent flickering
        
        self._build_ui()

    def _generate_data(self):
        try:
            # Import here to avoid path issues in Python 2.7 subpackages
            import sys
            import os
            sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
            from db_handler import db
            
            # Fetch data from drawings_master_bal
            # We assume column names like drawing_no, revision, status
            # and alias them to 'no', 'rev', 'status' for UI compatibility
            query = "SELECT drawing_no as no, latest_revision as rev, current_status as status FROM drawings_master_bal where current_status = 'Approved' LIMIT 11"
            data = db.fetch_all(query)
            
            if not data:
                print("No data found in drawings_master_bal or connection failed.")
                return []
            
            # Initialize requested_by for each item
            for item in data:
                item['requested_by'] = ""
                
            return data
        except Exception as e:
            print("Error connecting to database or fetching data: {}".format(e))
            return []

    def _build_ui(self):
        # Header container for Title and Search
        header = tk.Frame(self, bg=styles.LIGHT)
        header.pack(fill="x", pady=(0, 20))

        ttk.Label(header, text="Drawing Requisitions", style="Title.TLabel").pack(side="left")

        # Refresh button (New)
        ttk.Button(header, text="Refresh", style="Flat.TButton", 
                   command=self.refresh).pack(side="left", padx=20)

        # Search bar (Rightly aligned, compact)
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(header, textvariable=self.search_var, 
                                     font=("Segoe UI", 10), bd=0, relief="flat",
                                     width=25, # Horizontally small
                                     highlightthickness=1, highlightbackground="#cbd5e1",
                                     highlightcolor=styles.PRIMARY,
                                     fg="#94a3b8") # Start with placeholder color
        self.search_entry.pack(side="right", ipady=8) 
        self.search_entry.insert(0, "Search drawings...")
        
        self.search_entry.bind("<FocusIn>", self._clear_placeholder)
        self.search_entry.bind("<FocusOut>", self._restore_placeholder)
        self.search_var.trace("w", self._search_data)

        # Pagination controls (Pinned to bottom for visibility)
        pager = tk.Frame(self, bg=styles.LIGHT)
        pager.pack(side="bottom", fill="x", pady=15, padx=10)

        # Left spacer for centering
        left_spacer = tk.Frame(pager, bg=styles.LIGHT)
        left_spacer.pack(side="left", expand=True, fill="x")

        # Center: Navigation buttons
        nav_frame = tk.Frame(pager, bg=styles.LIGHT)
        nav_frame.pack(side="left")

        ttk.Button(nav_frame, text="◀ Previous", style="Flat.TButton",
                   command=self._prev_page).pack(side="left", padx=5)

        self.page_label = ttk.Label(nav_frame, text="Page 1 of 1", font=("Segoe UI", 10, "bold"))
        self.page_label.pack(side="left", padx=15)

        ttk.Button(nav_frame, text="Next ▶", style="Flat.TButton",
                   command=self._next_page).pack(side="left", padx=5)

        # Right side: Records info
        right_frame = tk.Frame(pager, bg=styles.LIGHT)
        right_frame.pack(side="left", expand=True, fill="x")
        
        self.records_label = tk.Label(right_frame, text="", font=("Segoe UI", 9), 
                                       fg="#64748b", bg=styles.LIGHT)
        self.records_label.pack(side="right")

        # Table Container
        self.table_container = tk.Frame(self, bg="white", highlightthickness=1, highlightbackground="#cbd5e1")
        self.table_container.pack(expand=True, fill="both")

        # Resizable Table Header (using PanedWindow)
        self.header_paned = tk.PanedWindow(self.table_container, orient="horizontal", 
                                          bg="#e2e8f0", bd=0, sashwidth=2, sashpad=0)
        self.header_paned.pack(fill="x")
        
        headers = ["Drawing ID", "Revision", "Status", "Requested By", "Action"]
        min_widths = [110, 70, 80, 150, 80] # Enforce min size to keep names readable
        self.header_frames = []
        
        for i, h in enumerate(headers):
            f = tk.Frame(self.header_paned, bg="#f1f5f9", width=self.col_widths[i], height=40)
            f.pack_propagate(False)
            lbl = tk.Label(f, text=h, font=("Segoe UI", 10, "bold"), 
                           bg="#f1f5f9", fg=styles.DARK)
            lbl.pack(expand=True, fill="both")
            self.header_paned.add(f, minsize=min_widths[i])
            self.header_frames.append(f)
            # Bind resize event to sync body
            f.bind("<Configure>", lambda e: self._sync_columns())

        # Table Body
        self.body_frame = tk.Frame(self.table_container, bg="white")
        self.body_frame.pack(expand=True, fill="both")

        self._load_table()

    def _sync_columns(self):
        # Update column widths based on header frame sizes
        for i, f in enumerate(self.header_frames):
            self.col_widths[i] = f.winfo_width()
            
        # Update all visible rows
        for row_dict in self.row_widgets:
            for i, cell in enumerate(row_dict['cells']):
                cell.config(width=self.col_widths[i])

    def _clear_placeholder(self, e):
        if self.search_entry.get() == "Search drawings...":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="#334155") # Switch to normal text color

    def _restore_placeholder(self, e):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Search drawings...")
            self.search_entry.config(fg="#94a3b8") # Switch back to placeholder color

    def _load_table(self):
        start = self.current_page * self.page_size
        end = start + self.page_size
        page_data = self.filtered[start:end]
        
        # Process data rows
        for i in range(self.page_size):
            if i < len(page_data):
                d = page_data[i]
                bg = "white" if i % 2 == 0 else "#fbfcfd"
                
                if i >= len(self.row_widgets):
                    row_frame = tk.Frame(self.body_frame, bg="white")
                    row_frame.pack(fill="x")
                    
                    cells = []
                    labels = []
                    # Create 4 data cells
                    for j in range(4):
                        cell = tk.Frame(row_frame, bg="white", width=self.col_widths[j], height=45)
                        cell.pack_propagate(False)
                        cell.pack(side="left")
                        
                        lbl = tk.Label(cell, font=("Segoe UI", 10), fg="#334155", bg="white")
                        lbl.pack(expand=True, fill="both", padx=5)
                        
                        cells.append(cell)
                        labels.append(lbl)
                    
                    # Action cell
                    action_cell = tk.Frame(row_frame, bg="white", width=self.col_widths[4], height=45)
                    action_cell.pack_propagate(False)
                    action_cell.pack(side="left")
                    
                    btn = ttk.Button(action_cell, text="Request", style="Action.TButton")
                    btn.pack(expand=True) # Center button
                    
                    cells.append(action_cell)
                    
                    row_dict = {
                        'frame': row_frame,
                        'cells': cells,
                        'labels': labels,
                        'action_cell': action_cell,
                        'button': btn
                    }
                    self.row_widgets.append(row_dict)
                    
                    
                    row_frame.bind("<Enter>", lambda e, r=row_frame: self._on_row_enter(r))
                    # Removed row click binding so only button triggers request

                else:
                    row_dict = self.row_widgets[i]
                    if not row_dict['frame'].winfo_viewable():
                        row_dict['frame'].pack(fill="x")
                
                # Update sizes and content
                row_dict['frame'].configure(bg=bg)
                row_dict['frame'].bind("<Leave>", lambda e, r=row_dict['frame'], b=bg: self._on_row_leave(r, b))
                
                status_val = str(d.get("status") or "N/A").upper()
                vals = [d.get("no", "N/A"), d.get("rev", "N/A"), status_val, d.get("requested_by", "")]
                
                for j, (lbl, cell, val) in enumerate(zip(row_dict['labels'], row_dict['cells'][:4], vals)):
                    lbl.configure(text=val, bg=bg)
                    cell.configure(width=self.col_widths[j], bg=bg)
                    if j == 3:
                        lbl.configure(fg="#4f46e5", font=("Segoe UI", 9, "italic"))
                
                row_dict['action_cell'].configure(width=self.col_widths[4], bg=bg)
                row_dict['button'].configure(command=lambda dn=d.get("no"), idx=i: self._handle_request(dn, idx))
            
            elif i < len(self.row_widgets):
                self.row_widgets[i]['frame'].pack_forget()

        # Update pagination labels
        total_records = len(self.filtered)
        total_pages = max(1, (total_records + self.page_size - 1) // self.page_size)
        current = self.current_page + 1
        
        # Calculate record range being displayed
        start_record = start + 1 if total_records > 0 else 0
        end_record = min(end, total_records)
        
        self.page_label.config(text="Page {} of {}".format(current, total_pages))
        self.records_label.config(text="Showing {} - {} of {} records".format(
            start_record, end_record, total_records))

    def _handle_request(self, drawing_no, row_idx=None):
        # Confirmation dialog
        confirm = messagebox.askyesno("Confirm Request", 
                                      "Are you sure you want to request this drawing with the drawing no {}?".format(drawing_no))
        if not confirm:
            return

        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
        status_text = "{} at {}".format(self.username, now)
        
        for d in self.drawings:
            if d.get("no") == drawing_no:
                d['requested_by'] = status_text
                break
        
        if row_idx is not None and row_idx < len(self.row_widgets):
            self.row_widgets[row_idx]['labels'][3].configure(text=status_text)
            
        messagebox.showinfo("Request", "Request submitted for {}".format(drawing_no))

    def refresh(self):
        """Re-fetch data from database to ensure freshness."""
        self.drawings = self._generate_data()
        self.filtered = list(self.drawings) # Reset filtered view on refresh
        self.current_page = 0
        self._load_table()

    def _handle_row_click(self, row_dict):
        drawing_no = row_dict['labels'][0].cget("text")
        start = self.current_page * self.page_size
        page_data = self.filtered[start:start+self.page_size]
        
        row_idx = None
        for i, d in enumerate(page_data):
            if d.get("no") == drawing_no:
                row_idx = i
                break
        
        self._handle_request(drawing_no, row_idx)

    def _on_row_enter(self, row):
        highlight_bg = "#f1f5f9"
        try:
            row.configure(bg=highlight_bg)
            for child in row.winfo_children():
                try:
                    child.configure(bg=highlight_bg)
                    # Handle nested children (labels inside cells)
                    if isinstance(child, tk.Frame):
                        for gc in child.winfo_children():
                            try:
                                gc.configure(bg=highlight_bg)
                            except: pass
                except: pass
        except: pass

    def _on_row_leave(self, row, original_bg):
        try:
            row.configure(bg=original_bg)
            for child in row.winfo_children():
                try:
                    child.configure(bg=original_bg)
                    if isinstance(child, tk.Frame):
                        for gc in child.winfo_children():
                            try:
                                gc.configure(bg=original_bg)
                            except: pass
                except: pass
        except: pass

    def _search_data(self, *args):
        q = self.search_var.get().lower()
        if q == "search drawings..." or not q:
            self.filtered = list(self.drawings)
        else:
            self.filtered = [
                d for d in self.drawings
                if q in str(d.get("no", "")).lower()
                or q in str(d.get("rev", "")).lower()
                or q in str(d.get("status", "")).lower()
                or q in str(d.get("requested_by", "")).lower()
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
