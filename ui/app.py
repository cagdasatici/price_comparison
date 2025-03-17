import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import threading
import time
import webbrowser
from difflib import SequenceMatcher
import re

from scrapers.store_scrapers import StoreScrapers
from utils.price_utils import extract_price, validate_price, string_similarity

class PriceComparisonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Price Comparison Tool")
        self.root.geometry("1200x800")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Initialize store scrapers
        self.store_scrapers = StoreScrapers()
        
        # Create main container with gradient background
        main_container = ctk.CTkFrame(root, fg_color="#1A1A2E")
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header section with logo and title
        header_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Logo and title container
        logo_title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        logo_title_frame.pack(fill=tk.X)
        
        # Logo
        logo_label = ctk.CTkLabel(
            logo_title_frame,
            text="💰",
            font=('Helvetica', 48),
            text_color='#00FF7F'
        )
        logo_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Title
        title_label = ctk.CTkLabel(
            logo_title_frame, 
            text="Price Comparison Tool",
            font=('Helvetica', 28, 'bold'),
            text_color='#FFFFFF'
        )
        title_label.pack(side=tk.LEFT)
        
        # Search section
        search_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        search_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Search container
        search_container = ctk.CTkFrame(
            search_frame, 
            fg_color="#2A2A4A",
            corner_radius=20,
            border_width=2,
            border_color="#3A3A6A"
        )
        search_container.pack(fill=tk.X, padx=20)
        
        # Search box
        self.product_entry = ctk.CTkEntry(
            search_container,
            width=800,
            height=60,
            font=('Helvetica', 16),
            placeholder_text="Enter product name (e.g., PS5 console disc edition)",
            fg_color="#3A3A6A",
            border_width=0,
            corner_radius=15
        )
        self.product_entry.pack(side=tk.LEFT, padx=25, pady=15, fill=tk.X, expand=True)
        
        # Bind Enter key to search
        self.product_entry.bind('<Return>', lambda event: self.start_search())
        
        # Search button
        self.search_button = ctk.CTkButton(
            search_container,
            text="Search",
            command=self.toggle_search,
            width=140,
            height=60,
            font=('Helvetica', 18, 'bold'),
            fg_color="#4A90E2",
            hover_color="#357ABD",
            corner_radius=15,
            text_color="#FFFFFF"
        )
        self.search_button.pack(side=tk.RIGHT, padx=25, pady=15)
        
        # Status bar frame
        status_frame = ctk.CTkFrame(
            main_container, 
            fg_color="#2A2A4A",
            corner_radius=20,
            border_width=2,
            border_color="#3A3A6A"
        )
        status_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            status_frame, 
            width=1160, 
            height=15,
            corner_radius=10,
            progress_color="#4A90E2"
        )
        self.progress_bar.pack(pady=5)
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="Ready to search",
            font=('Helvetica', 14, 'bold'),
            text_color='#FFFFFF'
        )
        self.status_label.pack(pady=2)
        
        # Store status labels
        self.store_status_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        self.store_status_frame.pack(fill=tk.X, padx=25, pady=2)
        
        self.store_status_labels = {}
        stores = self.store_scrapers.get_store_list()
        
        # Create a grid layout for store statuses (5 columns)
        for i, store in enumerate(stores):
            label = ctk.CTkLabel(
                self.store_status_frame,
                text=f"{store}: Waiting",
                font=('Helvetica', 10),
                text_color='#888888',
                width=200
            )
            row = i // 5
            col = i % 5
            label.grid(row=row, column=col, padx=5, pady=2, sticky='w')
            self.store_status_labels[store] = label
        
        # Loading animation
        self.loading_dots = 0
        self.loading_label = ctk.CTkLabel(
            status_frame,
            text="",
            font=('Helvetica', 16),
            text_color='#4A90E2'
        )
        self.loading_label.pack(pady=5)
        
        # Results section
        results_frame = ctk.CTkFrame(
            main_container, 
            fg_color="#2A2A4A",
            corner_radius=20,
            border_width=2,
            border_color="#3A3A6A"
        )
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        # Create Treeview for results
        self.tree = ttk.Treeview(
            results_frame,
            columns=('Store', 'Price', 'Title', 'Description', 'Link'),
            show='headings',
            height=20,
            style='Custom.Treeview'
        )

        # Configure columns
        self.tree.heading('Store', text='Store', anchor='w')
        self.tree.heading('Price', text='Price', anchor='w')
        self.tree.heading('Title', text='Title', anchor='w')
        self.tree.heading('Description', text='Description', anchor='w')
        self.tree.heading('Link', text='Link', anchor='w')

        # Set column widths
        self.tree.column('Store', width=150, anchor='w')
        self.tree.column('Price', width=150, anchor='w')
        self.tree.column('Title', width=400, anchor='w')
        self.tree.column('Description', width=300, anchor='w')
        self.tree.column('Link', width=0, stretch=False)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack the tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=15)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=15)

        # Bind double-click event to open link
        self.tree.bind('<Double-1>', self.open_link)
        
        # Configure styles
        self.configure_styles()
        
        # Search thread
        self.search_thread = None
        self.is_searching = False

    def configure_styles(self):
        style = ttk.Style()
        
        # Configure the treeview headings
        style.configure(
            "Custom.Treeview.Heading",
            background="#2A2A4A",
            foreground="#4A90E2",
            relief="flat",
            font=('Helvetica', 14, 'bold'),
            padding=10,
            borderwidth=0
        )
        
        # Configure the treeview style
        style.configure(
            "Custom.Treeview",
            background="#2A2A4A",
            foreground="#FFFFFF",
            rowheight=50,
            fieldbackground="#2A2A4A",
            font=('Helvetica', 14),
            borderwidth=0
        )
        
        # Configure the treeview selected row
        style.map('Custom.Treeview',
            background=[('selected', '#4A90E2')],
            foreground=[('selected', '#FFFFFF')]
        )
        
        # Configure the treeview heading hover effect
        style.map('Custom.Treeview.Heading',
            background=[('active', '#3A3A6A')],
            foreground=[('active', '#4A90E2')]
        )
        
        # Force the header background color
        style.layout("Custom.Treeview", [
            ('Custom.Treeview.treearea', {'sticky': 'nswe'}),
            ('Custom.Treeview.heading', {'sticky': 'nswe'})
        ])
        
        # Set the header background color explicitly
        style.configure("Custom.Treeview.Heading", background="#2A2A4A")

    def open_link(self, event):
        item = self.tree.selection()[0]
        link = self.tree.item(item)['values'][4]
        if link:
            webbrowser.open(link)

    def find_best_price(self, results):
        if not results:
            return None
            
        best_price = float('inf')
        best_result = None
        
        for result in results:
            if result and result.get('price'):
                try:
                    price = float(re.sub(r'[^\d.]', '', result['price']))
                    if price < best_price:
                        best_price = price
                        best_result = result
                except (ValueError, TypeError):
                    continue
                    
        return best_result

    def update_status(self, message, progress=None):
        self.status_label.configure(
            text=message,
            font=('Helvetica', 16, 'bold'),
            text_color='#FFFFFF'
        )
        
        if progress is not None:
            progress = max(0, min(1, progress))
            self.progress_bar.set(progress)
            
            if progress < 0.3:
                self.progress_bar.configure(progress_color="#FF6B6B")
            elif progress < 0.7:
                self.progress_bar.configure(progress_color="#FFA500")
            else:
                self.progress_bar.configure(progress_color="#4A90E2")
        
        self.root.update_idletasks()
        self.root.update()

    def update_loading_animation(self):
        if self.is_searching:
            self.loading_dots = (self.loading_dots + 1) % 4
            self.loading_label.configure(text="." * self.loading_dots)
            self.root.after(500, self.update_loading_animation)

    def update_store_status(self, store, status, color='#888888'):
        if store in self.store_status_labels:
            self.store_status_labels[store].configure(
                text=f"{store}: {status}",
                text_color=color,
                font=('Helvetica', 10)
            )
            
            if status == "Found":
                self.store_status_labels[store].configure(
                    fg_color="#1A3D1A",
                    text_color="#4A90E2"
                )
            elif status == "Not found":
                self.store_status_labels[store].configure(
                    fg_color="#3D1A1A",
                    text_color="#FF6B6B"
                )
            elif status == "Searching...":
                self.store_status_labels[store].configure(
                    fg_color="#1A1A3D",
                    text_color="#4A90E2"
                )
            else:
                self.store_status_labels[store].configure(
                    fg_color="transparent",
                    text_color="#888888"
                )
            
            self.root.update_idletasks()
            self.root.update()

    def toggle_search(self):
        if self.is_searching:
            self.stop_search()
        else:
            self.start_search()

    def stop_search(self):
        self.is_searching = False
        self.search_button.configure(
            text="Search",
            fg_color="#4A90E2",
            hover_color="#357ABD"
        )
        self.update_status("Search stopped", 0)
        self.loading_label.configure(text="")
        self.root.after(2000, lambda: self.update_status("Ready to search", 0))

    def start_search(self):
        if self.is_searching:
            return
            
        self.is_searching = True
        self.search_button.configure(
            text="Stop",
            fg_color="#FF6B6B",
            hover_color="#FF5252"
        )
        self.update_status("Starting search...", 0)
        self.update_loading_animation()
        
        # Clear previous results
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Start search in a separate thread
        self.search_thread = threading.Thread(target=self.search_prices)
        self.search_thread.daemon = True
        self.search_thread.start()

    def search_prices(self):
        try:
            product = self.product_entry.get()
            if not product:
                self.finish_search()
                return
                
            # Reset store statuses
            for store in self.store_status_labels:
                self.update_store_status(store, "Waiting")
                
            # Search on all websites
            results = []
            total_stores = len(self.store_status_labels)
            current_store = 0
            
            # Get search functions from store scrapers
            search_functions = self.store_scrapers.get_search_functions()
            
            # Search each store
            for store, search_func in search_functions.items():
                if not self.is_searching:
                    break
                    
                progress = current_store / total_stores
                self.update_status(f"Searching {store}...", progress)
                self.update_store_status(store, "Searching...", '#4A90E2')
                
                try:
                    result = search_func(product)
                    if result and result.get('link'):
                        results.append(result)
                        self.update_store_status(store, "Found", '#4A90E2')
                        self.insert_result(result)
                    else:
                        self.update_store_status(store, "Not found", '#FF6B6B')
                except Exception as e:
                    print(f"{store} error: {str(e)}")
                    self.update_store_status(store, "Error", '#FF6B6B')
                
                current_store += 1
                
                self.root.update_idletasks()
                self.root.update()
                time.sleep(0.1)
            
            if self.is_searching:
                self.finish_search()
            else:
                self.finish_search()
        except Exception as e:
            print(f"Search error: {str(e)}")
            self.finish_search()

    def finish_search(self):
        try:
            self.is_searching = False
            self.search_button.configure(
                text="Search",
                fg_color="#4A90E2",
                hover_color="#357ABD"
            )
            self.update_status("Search completed", 1)
            self.loading_label.configure(text="")
            self.root.after(2000, lambda: self.update_status("Ready to search", 0))
        except Exception as e:
            print(f"Error finishing search: {str(e)}")
            self.is_searching = False
            self.search_button.configure(
                text="Search",
                fg_color="#4A90E2",
                hover_color="#357ABD"
            )
            self.update_status("Search completed", 1)

    def insert_result(self, result):
        current_items = self.tree.get_children()
        current_results = []
        
        for item in current_items:
            values = self.tree.item(item)['values']
            current_results.append({
                'store': values[0],
                'price': values[1],
                'title': values[2],
                'description': values[3],
                'link': values[4]
            })
        
        current_results.append(result)
        best_result = self.find_best_price(current_results)
        
        for item in current_items:
            self.tree.delete(item)
            
        for res in current_results:
            tags = ('best_price',) if res == best_result else ()
            self.tree.insert(
                '',
                tk.END,
                values=(
                    res['store'],
                    res['price'],
                    res['title'],
                    res['description'][:100] + '...' if res['description'] else '',
                    res['link']
                ),
                tags=tags
            )
        
        self.tree.tag_configure('best_price', foreground='#4A90E2') 