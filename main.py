import os
import base64
import datetime
import threading
import webbrowser
import re
import requests
from flask import Flask, request, jsonify, Response

app = Flask(__name__)
BASE_PATH = r"E:\\X"
if not os.path.exists(BASE_PATH):
    try:
        os.makedirs(BASE_PATH)
    except:
        pass

def build_history():
    history_prompt = ""
    try:
        all_dirs = [os.path.join(BASE_PATH, d) for d in os.listdir(BASE_PATH)]
        valid_dirs = [d for d in all_dirs if os.path.isdir(d)]
        valid_dirs.sort(key=os.path.getmtime, reverse=True)
        history_data = []
        for d in valid_dirs[:5]:
            try:
                with open(os.path.join(d, "文案.txt"), "r", encoding="utf-8") as f:
                    t = f.read().strip()[:100]
                with open(os.path.join(d, "浏览量.txt"), "r", encoding="utf-8") as f:
                    v = f.read().strip()
                history_data.append(f"- 历史帖子: '{t}' | 浏览量: {v}")
            except:
                continue
        if history_data:
            history_prompt = "已归档高表现帖子:\n" + "\n".join(history_data)
    except Exception as e:
        history_prompt = f"历史读取失败: {e}"
    return history_prompt

def save_text_file(path, content):
    if content:
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(content))

def normalize_post_id(link):
    m = re.search(r"/status/(\d+)", link)
    if m:
        return m.group(1)
    return None

def allowed_to_save(payload, files):
    base_required = all(payload.get(k) for k in ["link", "comments", "reposts", "likes", "bookmarks", "views", "post_time", "record_time"])
    if not base_required:
        return False
    text_present = bool(payload.get("text", "").strip())
    img_count = len(files)
    if img_count > 4:
        return False
    if text_present:
        return True
    return img_count >= 1

@app.route("/")
def index():
    # 修正点：移除CSS/JS中多余的双花括号，使用replace代替format，避免JS模板字符串冲突
    html = """
    <!DOCTYPE html>
    <html lang='zh-CN'>
    <head>
    <meta charset='UTF-8'>
    <title>星核终端 · 生成与存档</title>
    <style>
    body { margin:0; font-family:'Microsoft Yahei', 'Consolas', monospace; background:radial-gradient(circle at 20% 20%, rgba(0,255,255,0.1), transparent 25%), radial-gradient(circle at 80% 0%, rgba(255,0,80,0.15), transparent 25%), #04070d; color:#e8f7ff; }
    .grid { display:grid; grid-template-columns:1.3fr 1fr; gap:16px; padding:20px; }
    .panel { background:linear-gradient(135deg, rgba(10,16,28,0.9), rgba(20,32,52,0.9)); border:1px solid #1f3a5b; box-shadow:0 0 18px rgba(0,255,255,0.1); border-radius:10px; padding:16px; }
    h1 { margin:0 0 12px; letter-spacing:2px; color:#6cfaff; text-shadow:0 0 8px #00e7ff; }
    label { display:block; margin-bottom:6px; color:#9ad9ff; font-size:13px; }
    input, textarea { width:100%; background:#0b1320; border:1px solid #1f3a5b; color:#e8f7ff; padding:10px; border-radius:6px; outline:none; font-family:'Consolas', monospace; }
    input:focus, textarea:focus { border-color:#00f0ff; box-shadow:0 0 8px rgba(0,240,255,0.4); }
    .flex { display:flex; gap:10px; flex-wrap:wrap; }
    .btn { flex:1; background:linear-gradient(90deg, #00e7ff, #0088ff); border:none; color:#04101c; padding:12px; border-radius:8px; cursor:pointer; font-weight:bold; letter-spacing:1px; box-shadow:0 0 12px rgba(0,231,255,0.5); transition:transform 0.15s, box-shadow 0.15s; }
    .btn:hover { transform:translateY(-1px); box-shadow:0 0 18px rgba(108,250,255,0.8); }
    .btn.alt { background:linear-gradient(90deg, #ff3f8e, #a100ff); color:#fff; box-shadow:0 0 14px rgba(255,63,142,0.6); }
    .label-row { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
    .dropzone { margin-top:10px; padding:14px; border:1px dashed #00e7ff; border-radius:8px; text-align:center; color:#7fe9ff; background:rgba(0,231,255,0.08); transition:all 0.2s; }
    .dropzone.active { background:rgba(0,231,255,0.18); border-color:#ff3f8e; color:#fff; }
    .pill { padding:8px 10px; background:rgba(0,0,0,0.35); border:1px solid #1f3a5b; border-radius:6px; display:flex; align-items:center; gap:8px; font-size:12px; color:#bfe9ff; }
    .pill span { color:#ff5fb7; cursor:pointer; }
    .log { background:#03060b; border:1px solid #1f3a5b; border-radius:8px; padding:10px; height:160px; overflow:auto; font-size:12px; color:#6cfaff; box-shadow:inset 0 0 10px rgba(0,231,255,0.12); }
    .neon-bar { width:100%; height:4px; background:linear-gradient(90deg, rgba(0,231,255,0.8), rgba(255,0,120,0.8), rgba(0,231,255,0.8)); margin:12px 0; box-shadow:0 0 12px rgba(0,231,255,0.4); border-radius:5px; animation:flow 4s linear infinite; }
    @keyframes flow { 0% { background-position:0 0; } 100% { background-position:200% 0; } }
    </style>
    </head>
    <body>
    <div class='grid'>
        <div class='panel'>
            <h1>星核终端 · 创作指令</h1>
            <label>输入文案</label>
            <textarea id='text' rows='10' placeholder='输入或等待AI生成的文案...'></textarea>
            <div class='dropzone' id='dropzone'>拖拽图片到这里，或点击选择文件</div>
            <input type='file' id='fileInput' multiple accept='image/*,text/plain' style='display:none'>
            <div class='flex' style='margin-top:10px;' id='fileList'></div>
            <div class='neon-bar'></div>
            <div class='flex'>
                <button class='btn alt' onclick='runGenerate()'>AI 生成</button>
                <button class='btn' onclick='runSave()'>存档保存</button>
                <button class='btn' style='background:linear-gradient(90deg,#1f2937,#0f172a); color:#7fe9ff; box-shadow:none;' onclick='clearAll()'>清除输入</button>
            </div>
        </div>
        <div class='panel'>
            <h1>数据填写 · 必填</h1>
            <div class='label-row'>
                <div><label>帖子链接</label><input id='link' placeholder='https://x.com/Username/status/*********'></div>
                <div><label>评论</label><input id='comments' placeholder='数字'></div>
                <div><label>转发</label><input id='reposts' placeholder='数字'></div>
                <div><label>点赞</label><input id='likes' placeholder='数字'></div>
                <div><label>收藏</label><input id='bookmarks' placeholder='数字'></div>
                <div><label>浏览量</label><input id='views' placeholder='数字'></div>
                <div><label>帖子发布时间</label><input id='post_time' placeholder='上午12:52 · 2025年12月1日'></div>
                <div><label>数据记录时间</label><input id='record_time' value='__TIME_PLACEHOLDER__'></div>
            </div>
            <div class='neon-bar'></div>
            <div class='log' id='log'></div>
        </div>
    </div>
    <script>
    const dropzone=document.getElementById('dropzone');
    const fileInput=document.getElementById('fileInput');
    const fileList=document.getElementById('fileList');
    const logBox=document.getElementById('log');
    let selectedFiles=[];
    function log(msg){const time=new Date().toLocaleTimeString('zh-CN',{hour12:false});logBox.innerHTML=`<div>[${time}] ${msg}</div>`+logBox.innerHTML;}
    function renderFiles(){fileList.innerHTML='';selectedFiles.forEach((f,i)=>{const pill=document.createElement('div');pill.className='pill';pill.innerHTML=`<span onclick="removeFile(${i})">✕</span><div>${f.name}</div>`;fileList.appendChild(pill);});}
    function removeFile(idx){selectedFiles.splice(idx,1);renderFiles();}
    dropzone.addEventListener('click',()=>fileInput.click());
    fileInput.addEventListener('change',e=>{selectedFiles=[...selectedFiles,...Array.from(e.target.files)].slice(0,4);renderFiles();});
    dropzone.addEventListener('dragover',e=>{e.preventDefault();dropzone.classList.add('active');});
    dropzone.addEventListener('dragleave',()=>dropzone.classList.remove('active'));
    dropzone.addEventListener('drop',e=>{e.preventDefault();dropzone.classList.remove('active');selectedFiles=[...selectedFiles,...Array.from(e.dataTransfer.files)].slice(0,4);renderFiles();});
    function clearAll(){document.getElementById('text').value='';selectedFiles=[];renderFiles();log('已清空输入');}
    async function runGenerate(){log('正在发送到本地模型...');const fd=new FormData();fd.append('text',document.getElementById('text').value);selectedFiles.forEach(f=>fd.append('files',f));try{const res=await fetch('/api/generate',{method:'POST',body:fd});const data=await res.json();if(data.success){document.getElementById('text').value=data.content;log('AI 已返回结果');}else{log(data.message||'生成失败');}}catch(e){log('网络请求失败');}}
    async function runSave(){const fd=new FormData();['link','comments','reposts','likes','bookmarks','views','post_time','record_time','text'].forEach(id=>{fd.append(id,document.getElementById(id).value);});selectedFiles.forEach(f=>fd.append('files',f));try{const res=await fetch('/api/save',{method:'POST',body:fd});const data=await res.json();if(data.success){log('保存成功: '+data.post_id);clearAll();}else{log(data.message||'保存失败');}}catch(e){log('保存请求失败');}}
    </script>
    </body>
    </html>
    """
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    html = html.replace("__TIME_PLACEHOLDER__", now_str)
    return Response(html, mimetype="text/html")

@app.route("/api/generate", methods=["POST"])
def api_generate():
    text = request.form.get("text", "").strip()
    files = request.files.getlist("files")
    imgs = []
    for f in files:
        try:
            b64 = base64.b64encode(f.read()).decode("utf-8")
            imgs.append(b64)
            f.seek(0) # Reset file pointer for later saving if needed
        except:
            continue
    history_prompt = build_history()
    if not text and not imgs:
        return jsonify({"success": False, "message": "缺少生成素材"})
    prompt = f"系统: 你是社交媒体引流专家，以科幻风格输出。当前时间: {datetime.datetime.now()}\n历史数据:\n{history_prompt}\n输入文本:{text}\n图片数量:{len(imgs)}\n请给出有冲击力的中文文案，并预估浏览量。输出格式: 文案\n浏览量: 数字"
    payload = {"model": "minicpm-v", "prompt": prompt, "stream": False}
    if imgs:
        payload["images"] = imgs
    try:
        r = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        if r.status_code == 200:
            res = r.json()
            content = res.get("response", "")
            return jsonify({"success": True, "content": content})
        return jsonify({"success": False, "message": f"Ollama HTTP {r.status_code}"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Ollama连接失败: {str(e)}"})

@app.route("/api/save", methods=["POST"])
def api_save():
    payload = {k: request.form.get(k, "").strip() for k in ["link", "comments", "reposts", "likes", "bookmarks", "views", "post_time", "record_time", "text"]}
    files = request.files.getlist("files")
    if not allowed_to_save(payload, files):
        return jsonify({"success": False, "message": "必填项缺失，或素材不符合要求(需1-4张图或纯文案)"})
    post_id = normalize_post_id(payload["link"])
    if not post_id:
        return jsonify({"success": False, "message": "帖子链接无效，无法提取ID"})
    save_dir = os.path.join(BASE_PATH, post_id)
    try:
        os.makedirs(save_dir, exist_ok=True)
        save_text_file(os.path.join(save_dir, "文案.txt"), payload.get("text", ""))
        save_text_file(os.path.join(save_dir, "评论.txt"), payload.get("comments"))
        save_text_file(os.path.join(save_dir, "转发.txt"), payload.get("reposts"))
        save_text_file(os.path.join(save_dir, "点赞.txt"), payload.get("likes"))
        save_text_file(os.path.join(save_dir, "收藏.txt"), payload.get("bookmarks"))
        save_text_file(os.path.join(save_dir, "浏览量.txt"), payload.get("views"))
        save_text_file(os.path.join(save_dir, "帖子发布时间.txt"), payload.get("post_time"))
        save_text_file(os.path.join(save_dir, "数据记录时间.txt"), payload.get("record_time"))
        for idx, f in enumerate(files):
            # Safe way to handle multiple files: reset pointer just in case
            f.seek(0) 
            ext = os.path.splitext(f.filename)[1] or ".jpg"
            dest = os.path.join(save_dir, f"{idx+1}{ext}")
            f.save(dest)
        return jsonify({"success": True, "post_id": post_id})
    except Exception as e:
        return jsonify({"success": False, "message": f"写入文件失败: {str(e)}"})

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
