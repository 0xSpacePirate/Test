import logging
from logger_setup import setup_global_logging
setup_global_logging()

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog
import threading
import queue
# Import from all our modules
from document_processor import process_and_ingest_documents
from search_engine import perform_search as perform_semantic_search
from keyword_search_engine import create_db as create_keyword_db, search_sqlite as perform_keyword_search
from key_manager import save_credentials, load_credentials


class ApiKeyWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Set OpenAI Credentials")
        self.geometry("450x150")
        self.transient(parent)
        self.grab_set()

        self.credentials_saved = False

        tk.Label(self, text="Enter your OpenAI API Key (starts with 'sk-'):").pack(pady=(10, 0))
        self.key_entry = tk.Entry(self, width=60, show="*")
        self.key_entry.pack(padx=10)

        tk.Label(self, text="Enter your OpenAI Project ID (starts with 'proj_'):").pack(pady=(10, 0))
        self.project_id_entry = tk.Entry(self, width=60)
        self.project_id_entry.pack(padx=10)

        save_button = tk.Button(self, text="Save Credentials", command=self.save_and_close)
        save_button.pack(pady=10)

    def save_and_close(self):
        api_key = self.key_entry.get().strip()
        project_id = self.project_id_entry.get().strip()

        if api_key.startswith("sk-") and project_id.startswith("proj_"):
            save_credentials(api_key, project_id)
            self.credentials_saved = True
            self.destroy()
        else:
            logging.error("User entered invalid credentials.")
            messagebox.showerror("Invalid Credentials",
                                 "Please ensure your API Key starts with 'sk-' and your Project ID starts with 'proj_'.",
                                 parent=self)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal Document Search")
        self.geometry("800x700")

        self.source_directory = None
        self.gui_queue = queue.Queue()

        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        settings_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Set API Credentials...", command=self.open_api_key_window)

        dir_frame = tk.Frame(self)
        dir_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        self.dir_label = tk.Label(dir_frame, text="Document Folder: (None Selected)")
        self.dir_label.pack(side=tk.LEFT, padx=(0, 5))
        self.browse_button = tk.Button(dir_frame, text="Browse...", command=self.select_directory)
        self.browse_button.pack(side=tk.LEFT)
        self.index_button = tk.Button(dir_frame, text="Index New Files", command=self.start_indexing_thread,
                                      state=tk.DISABLED)
        self.index_button.pack(side=tk.LEFT, padx=5)

        main_frame = tk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        semantic_frame = tk.Frame(main_frame, relief=tk.GROOVE, borderwidth=2, padx=5, pady=5)
        semantic_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(semantic_frame, text="Semantic Search (finds by meaning):").pack(anchor=tk.W)
        self.semantic_search_entry = tk.Entry(semantic_frame, width=70)
        self.semantic_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.semantic_search_entry.bind("<Return>", self.start_semantic_search_thread)
        self.semantic_search_button = tk.Button(semantic_frame, text="Search",
                                                command=self.start_semantic_search_thread)
        self.semantic_search_button.pack(side=tk.LEFT, padx=(5, 0))

        keyword_frame = tk.Frame(main_frame, relief=tk.GROOVE, borderwidth=2, padx=5, pady=5)
        keyword_frame.pack(fill=tk.X)
        tk.Label(keyword_frame, text="Keyword Search (finds exact words/phrases):").pack(anchor=tk.W)
        self.keyword_search_entry = tk.Entry(keyword_frame, width=70)
        self.keyword_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.keyword_search_entry.bind("<Return>", self.start_keyword_search_thread)
        self.keyword_search_button = tk.Button(keyword_frame, text="Search", command=self.start_keyword_search_thread)
        self.keyword_search_button.pack(side=tk.LEFT, padx=(5, 0))

        results_frame = tk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.results_text = scrolledtext.ScrolledText(results_frame, wrap=tk.WORD, state='disabled',
                                                      font=("TkDefaultFont", 10))
        self.results_text.pack(fill=tk.BOTH, expand=True)
        self.configure_tags()

        self.status_bar = tk.Label(self, text="Welcome! Please set your API credentials via the Settings menu.", bd=1,
                                   relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.after(100, self.process_queue)
        self.after(150, self.initial_setup)

    def open_api_key_window(self):
        api_window = ApiKeyWindow(self)
        self.wait_window(api_window)

        if api_window.credentials_saved:
            messagebox.showinfo("Credentials Saved",
                                "Credentials have been saved successfully. You can now use the Indexing and Semantic Search features.")
            self.check_api_key_and_toggle_buttons()

    def configure_tags(self):
        self.results_text.tag_configure("header", font=("TkDefaultFont", 12, "bold", "underline"))
        self.results_text.tag_configure("source_label", font=("TkDefaultFont", 10, "italic"))
        self.results_text.tag_configure("source_path", font=("TkDefaultFont", 10, "bold"))
        self.results_text.tag_configure("highlighted_chunk", background="#E0FFE0")
        self.results_text.tag_configure("keyword_result", font=("TkDefaultFont", 11))

    def select_directory(self):
        path = filedialog.askdirectory(title="Select Folder Containing .doc or .docx Files")
        if path:
            self.source_directory = path
            self.dir_label.config(text=f"Document Folder: {self.source_directory}")
            self.check_api_key_and_toggle_buttons()
            self.update_status(f"Directory selected. Ready to index files.")
            logging.info(f"User selected directory: {path}")

    def initial_setup(self):
        create_keyword_db()
        self.check_api_key_and_toggle_buttons()

    def check_api_key_and_toggle_buttons(self):
        api_key, project_id = load_credentials()
        if api_key and project_id:
            self.semantic_search_button.config(state=tk.NORMAL)
            if self.source_directory:
                self.index_button.config(state=tk.NORMAL)
            self.update_status("Ready.")
        else:
            logging.error("API credentials not found. Semantic features disabled.")
            self.semantic_search_button.config(state=tk.DISABLED)
            self.index_button.config(state=tk.DISABLED)
            self.update_status("API Credentials not set. Please use the Settings menu.")

    def process_queue(self):
        try:
            while True:
                msg_type, data = self.gui_queue.get_nowait()
                if msg_type == "status":
                    self.update_status(data)
                elif msg_type == "semantic_results":
                    self.display_semantic_results(data)
                elif msg_type == "keyword_results":
                    self.display_keyword_results(data)
                elif msg_type == "enable_buttons":
                    self.toggle_buttons(True)
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def toggle_buttons(self, enabled):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.keyword_search_button.config(state=state)
        self.browse_button.config(state=state)
        if enabled:
            self.check_api_key_and_toggle_buttons()
        else:
            self.semantic_search_button.config(state=tk.DISABLED)
            self.index_button.config(state=tk.DISABLED)

    def update_status(self, text):
        self.status_bar.config(text=text)
        self.update_idletasks()

    def clear_results(self):
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', tk.END)
        self.results_text.config(state='disabled')

    def start_indexing_thread(self):
        if not self.source_directory:
            messagebox.showwarning("Directory Not Set", "Please select a directory first.")
            return
        self.toggle_buttons(False)
        self.update_status("Starting unified indexing process...")
        threading.Thread(target=self.run_indexing, daemon=True, name="IndexingThread").start()

    def run_indexing(self):
        def status_callback(text):
            self.gui_queue.put(("status", text))

        try:
            process_and_ingest_documents(status_callback, self.source_directory)
        except Exception as e:
            logging.error("An exception occurred in the indexing thread.", exc_info=True)
            status_callback(f"An unexpected error during indexing: {e}")
        finally:
            self.gui_queue.put(("enable_buttons", True))

    def start_semantic_search_thread(self, event=None):
        query = self.semantic_search_entry.get()
        if not query.strip(): return
        self.toggle_buttons(False)
        self.update_status("Performing semantic search...")
        self.clear_results()
        threading.Thread(target=self.run_semantic_search, args=(query,), daemon=True, name="SemanticSearchThread").start()

    def run_semantic_search(self, query):
        def status_callback(text):
            self.gui_queue.put(("status", text))

        try:
            results = perform_semantic_search(query, status_callback)
            self.gui_queue.put(("semantic_results", results))
        except Exception as e:
            logging.error("An exception occurred in the semantic search thread.", exc_info=True)
            status_callback(f"Error during semantic search: {e}")
        finally:
            self.gui_queue.put(("enable_buttons", True))


    def start_keyword_search_thread(self, event=None):
        query = self.keyword_search_entry.get()
        if not query.strip(): return
        self.toggle_buttons(False)
        self.update_status("Performing keyword search...")
        self.clear_results()
        threading.Thread(target=self.run_keyword_search, args=(query,), daemon=True, name="KeywordSearchThread").start()

    def run_keyword_search(self, query):
        try:
            results = perform_keyword_search(query)
            self.gui_queue.put(("keyword_results", results))
        except Exception as e:
            logging.error("An exception occurred in the keyword search thread.", exc_info=True)
            self.gui_queue.put(("status", f"Error during keyword search: {e}"))
        finally:
            self.gui_queue.put(("enable_buttons", True))


    def display_semantic_results(self, results):
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', tk.END)
        if not results:
            self.results_text.insert(tk.END, "No relevant documents found for semantic search.")
        else:
            num_matches_str = f"Found {len(results)} relevant chunks (Semantic Search)\n\n"
            self.results_text.insert(tk.END, num_matches_str, "header")
            for i, doc in enumerate(results):
                source_path = doc.metadata.get('source', 'Unknown')
                self.results_text.insert(tk.END, f"Source File: ", "source_label")
                self.results_text.insert(tk.END, f"{source_path}\n", "source_path")
                self.results_text.insert(tk.END, f"Matching Chunk:\n", "source_label")
                self.results_text.insert(tk.END, f"{doc.page_content}\n", "highlighted_chunk")
                if i < len(results) - 1:
                    self.results_text.insert(tk.END, "\n" + "-" * 80 + "\n\n")
        self.results_text.config(state='disabled')

    def display_keyword_results(self, results):
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', tk.END)
        if not results:
            self.results_text.insert(tk.END, "No documents found containing that keyword/phrase.")
        else:
            num_matches_str = f"Found {len(results)} files (Keyword Search)\n\n"
            self.results_text.insert(tk.END, num_matches_str, "header")
            for i, path in enumerate(results):
                self.results_text.insert(tk.END, f"{i + 1}. {path}\n", "keyword_result")
        self.results_text.config(state='disabled')


if __name__ == "__main__":
    try:
        app = App()
        app.mainloop()
    except Exception:
        logging.critical("A fatal error occurred in the main application loop.", exc_info=True)
        messagebox.showerror("Fatal Error", "A critical error occurred. Please check the log file for details.")