import os
import shutil
import json
import base64
import datetime
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import requests
from PIL import Image, ImageTk
from tkinterdnd2 import DND_FILES, TkinterDnD

class CyberPunkApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        self.title("NEXUS DATALINK // TERMINAL V2.0")
        self.geometry("1100x850")
        self.configure(bg="#05080d")
        self.base_path = r"E:\X"
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)
        
        self.colors = {
            "bg": "#05080d",
            "panel": "#0a101c",
            "fg": "#00f0ff", 
            "fg_alt": "#ff003c", 
            "input": "#0f1826",
            "border": "#1c2b45",
            "text": "#e0e0e0"
        }
        self.fonts = {
            "ui": ("Consolas", 10),
            "header": ("Consolas", 14, "bold"),
            "mono": ("Courier New", 10)
        }
        
        self.file_queue = []
        self.setup_interface()
        self.log_system("SYSTEM INITIALIZED. WAITING FOR INPUT...")

    def setup_interface(self):
        main_frame = tk.Frame(self, bg=self.colors["bg"])
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        header_frame = tk.Frame(main_frame, bg=self.colors["panel"], highlightbackground=self.colors["fg"], highlightthickness=1)
        header_frame.pack(fill="x", pady=(0, 10))
        tk.Label(header_frame, text=":: NEURAL LINK DATA PROCESSOR ::", bg=self.colors["panel"], fg=self.colors["fg"], font=self.fonts["header"]).pack(pady=5)

        data_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        data_frame.pack(fill="x", pady=5)

        self.inputs = {}
        fields = [
            ("LINK_URL", "link"), ("COMMENTS", "comments"), 
            ("REPOSTS", "reposts"), ("LIKES", "likes"), 
            ("BOOKMARKS", "bookmarks"), ("VIEWS", "views"),
            ("POST_TIME", "post_time"), ("REC_TIME", "record_time")
        ]

        for i, (label_text, key) in enumerate(fields):
            f = tk.Frame(data_frame, bg=self.colors["bg"])
            f.grid(row=i//4, column=i%4, padx=5, pady=5, sticky="ew")
            tk.Label(f, text=label_text, bg=self.colors["bg"], fg=self.colors["fg_alt"], font=self.fonts["ui"], anchor="w").pack(fill="x")
            e = tk.Entry(f, bg=self.colors["input"], fg=self.colors["text"], insertbackground="white", relief="flat", font=self.fonts["mono"])
            e.config(highlightbackground=self.colors["border"], highlightthickness=1)
            e.pack(fill="x", ipady=3)
            self.inputs[key] = e
            data_frame.grid_columnconfigure(i%4, weight=1)

        self.inputs["record_time"].insert(0, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        content_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        content_frame.pack(fill="both", expand=True, pady=10)

        left_panel = tk.Frame(content_frame, bg=self.colors["panel"], highlightthickness=1, highlightbackground=self.colors["border"])
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        tk.Label(left_panel, text=">> TEXT INPUT STREAM", bg=self.colors["panel"], fg=self.colors["fg"], anchor="w").pack(fill="x", padx=5, pady=2)
        self.text_area = tk.Text(left_panel, bg=self.colors["input"], fg="white", insertbackground="white", relief="flat", font=self.fonts["mono"], height=10)
        self.text_area.pack(fill="both", expand=True, padx=5, pady=5)

        right_panel = tk.Frame(content_frame, bg=self.colors["panel"], highlightthickness=1, highlightbackground=self.colors["border"])
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))

        tk.Label(right_panel, text=">> ASSET UPLOAD (DRAG & DROP)", bg=self.colors["panel"], fg=self.colors["fg"], anchor="w").pack(fill="x", padx=5, pady=2)
        self.file_listbox = tk.Listbox(right_panel, bg=self.colors["input"], fg=self.colors["fg"], selectbackground=self.colors["fg_alt"], relief="flat", font=self.fonts["mono"])
        self.file_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind('<<Drop>>', self.on_drop)
        
        btn_box = tk.Frame(right_panel, bg=self.colors["panel"])
        btn_box.pack(fill="x", padx=5, pady=5)
        self.mk_btn(btn_box, "[BROWSE]", self.browse_files, self.colors["border"]).pack(side="left", fill="x", expand=True, padx=2)
        self.mk_btn(btn_box, "[CLEAR]", self.clear_files, self.colors["border"]).pack(side="left", fill="x", expand=True, padx=2)

        action_frame = tk.Frame(main_frame, bg=self.colors["bg"])
        action_frame.pack(fill="x", pady=10)
        
        self.mk_btn(action_frame, ">> EXECUTE: SAVE DATA <<", self.save_data, self.colors["fg"]).pack(side="left", fill="x", expand=True, padx=5)
        self.mk_btn(action_frame, ">> EXECUTE: AI GENERATION <<", self.run_ai, self.colors["fg_alt"]).pack(side="right", fill="x", expand=True, padx=5)

        log_frame = tk.Frame(main_frame, bg=self.colors["panel"], highlightthickness=1, highlightbackground=self.colors["fg"])
        log_frame.pack(fill="x", pady=(10, 0))
        tk.Label(log_frame, text=":: SYSTEM LOG ::", bg=self.colors["panel"], fg=self.colors["fg"], font=("Consolas", 8)).pack(anchor="w", padx=5)
        self.log_area = tk.Text(log_frame, height=8, bg="black", fg="#00ff00", font=("Consolas", 9), state="disabled", relief="flat")
        self.log_area.pack(fill="x", padx=5, pady=5)

    def mk_btn(self, parent, text, cmd, color):
        return tk.Button(parent, text=text, command=cmd, bg=color, fg="black", font=("Consolas", 10, "bold"), activebackground="white", relief="flat")

    def log_system(self, msg):
        self.log_area.config(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_area.insert("end", f"[{ts}] {msg}\n")
        self.log_area.see("end")
        self.log_area.config(state="disabled")

    def on_drop(self, event):
        files = self.tk.splitlist(event.data)
        for f in files:
            if f not in self.file_queue:
                self.file_queue.append(f)
                self.file_listbox.insert("end", os.path.basename(f))
        self.log_system(f"FILES QUEUED: {len(files)} NEW ASSETS")

    def browse_files(self):
        files = filedialog.askopenfilenames()
        for f in files:
            if f not in self.file_queue:
                self.file_queue.append(f)
                self.file_listbox.insert("end", os.path.basename(f))

    def clear_files(self):
        self.file_queue = []
        self.file_listbox.delete(0, "end")
        self.log_system("FILE QUEUE CLEARED")

    def get_assets(self):
        imgs = []
        txt_content = ""
        for f in self.file_queue:
            ext = os.path.splitext(f)[1].lower()
            if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.webp']:
                imgs.append(f)
            elif ext == '.txt':
                try:
                    with open(f, 'r', encoding='utf-8') as tf:
                        txt_content += tf.read() + "\n"
                except:
                    pass
        return imgs, txt_content

    def save_data(self):
        data = {k: v.get().strip() for k, v in self.inputs.items()}
        
        missing = [k for k, v in data.items() if not v]
        if missing:
            messagebox.showerror("ACCESS DENIED", f"MISSING FIELDS: {', '.join(missing)}")
            return

        try:
            link = data['link']
            if '?' in link: link = link.split('?')[0]
            post_id = link.rstrip('/').split('/')[-1]
            if not post_id or not post_id.isdigit():
                post_id = str(int(datetime.datetime.now().timestamp()))
        except:
            messagebox.showerror("ERROR", "INVALID LINK FORMAT")
            return

        manual_text = self.text_area.get("1.0", "end").strip()
        imgs, file_text = self.get_assets()
        final_text = (manual_text + "\n" + file_text).strip()
        
        if not final_text and not imgs:
             messagebox.showerror("ERROR", "NO CONTENT TO SAVE (TEXT OR IMAGES REQUIRED)")
             return
        
        if len(imgs) > 4:
            messagebox.showerror("ERROR", "IMAGE LIMIT EXCEEDED (MAX 4)")
            return

        save_dir = os.path.join(self.base_path, post_id)
        if os.path.exists(save_dir):
            if not messagebox.askyesno("CONFLICT", f"ID {post_id} EXISTS. OVERWRITE?"):
                return
            try: shutil.rmtree(save_dir)
            except: pass
        
        try:
            os.makedirs(save_dir, exist_ok=True)
            
            file_map = {
                "文案.txt": final_text,
                "评论.txt": data['comments'],
                "转发.txt": data['reposts'],
                "点赞.txt": data['likes'],
                "收藏.txt": data['bookmarks'],
                "浏览量.txt": data['views'],
                "帖子发布时间.txt": data['post_time'],
                "数据记录时间.txt": data['record_time']
            }

            for name, content in file_map.items():
                if content:
                    with open(os.path.join(save_dir, name), 'w', encoding='utf-8') as f:
                        f.write(str(content))
            
            for idx, img_path in enumerate(imgs):
                ext = os.path.splitext(img_path)[1]
                dest = os.path.join(save_dir, f"{idx+1}{ext}")
                shutil.copy2(img_path, dest)

            self.log_system(f"DATA ARCHIVED SUCCESSFULLY: {post_id}")
            self.clear_files()
            self.text_area.delete("1.0", "end")
            messagebox.showinfo("SUCCESS", "DATA SECURELY STORED")

        except Exception as e:
            self.log_system(f"WRITE ERROR: {str(e)}")
            messagebox.showerror("CRITICAL ERROR", str(e))

    def run_ai(self):
        threading.Thread(target=self._ai_worker, daemon=True).start()

    def _ai_worker(self):
        self.log_system("INITIATING AI UPLINK...")
        
        manual_text = self.text_area.get("1.0", "end").strip()
        imgs, file_text = self.get_assets()
        current_text = (manual_text + "\n" + file_text).strip()
        
        if not current_text and not imgs:
            self.log_system("ABORT: NO INPUT DATA FOR INFERENCE")
            return

        history_prompt = ""
        try:
            all_dirs = [os.path.join(self.base_path, d) for d in os.listdir(self.base_path)]
            valid_dirs = [d for d in all_dirs if os.path.isdir(d)]
            valid_dirs.sort(key=os.path.getmtime, reverse=True)
            
            history_data = []
            for d in valid_dirs[:5]:
                try:
                    with open(os.path.join(d, "文案.txt"), 'r', encoding='utf-8') as f: t = f.read().strip()[:100]
                    with open(os.path.join(d, "浏览量.txt"), 'r', encoding='utf-8') as f: v = f.read().strip()
                    history_data.append(f"- Prev Post: '{t}' | Views: {v}")
                except: continue
            
            if history_data:
                history_prompt = "ANALYSIS OF ARCHIVED HIGH-PERFORMANCE DATA:\n" + "\n".join(history_data)
        except Exception as e:
            self.log_system(f"HISTORY RETRIEVAL FAILED: {e}")

        prompt = f"""
        SYSTEM INSTRUCTION: You are an advanced social media analytics AI.
        TASK: Generate a viral post caption and predict view count.
        
        CONTEXT:
        Current Time: {datetime.datetime.now()}
        {history_prompt}
        
        INPUT DATA:
        Text Segment: {current_text}
        Image Count: {len(imgs)}
        
        REQUIREMENT:
        1. Analyze the input images (if any) and text.
        2. Write a compelling, sci-fi or modern style caption.
        3. Estimate a realistic view count based on the 'Archived Data' trends.
        """

        payload = {
            "model": "minicpm-v",
            "prompt": prompt,
            "stream": False
        }

        if imgs:
            b64_imgs = []
            for ip in imgs:
                try:
                    with open(ip, "rb") as ifile:
                        b64_imgs.append(base64.b64encode(ifile.read()).decode('utf-8'))
                except: pass
            payload["images"] = b64_imgs

        try:
            self.log_system("SENDING PACKET TO NEURAL ENGINE (LOCALHOST:11434)...")
            response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
            
            if response.status_code == 200:
                res_json = response.json()
                result_text = res_json.get("response", "NO DATA RECEIVED")
                
                self.log_system("INFERENCE COMPLETE. INCOMING TRANSMISSION:")
                self.text_area.delete("1.0", "end")
                self.text_area.insert("end", f"--- AI GENERATED CONTENT ---\n{result_text}\n----------------------------\n")
                
                if current_text:
                    self.text_area.insert("end", f"\n[ORIGINAL INPUT]\n{current_text}")
            else:
                self.log_system(f"CONNECTION ERROR: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_system(f"FATAL ERROR IN AI THREAD: {str(e)}")

if __name__ == "__main__":
    app = CyberPunkApp()
    app.mainloop()
