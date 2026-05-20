import storage
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app) # 保留防呆機制

# 隱藏 Flask 預設的繁雜小黑窗連線日誌，只顯示嚴重錯誤
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# =====================================================
# 🌐 網頁 HTML 前端：內建自動時間排序、修改、刪除、照片功能
# =====================================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>TIMETRO 行事曆助手 — 完全版</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        h1, h2 { color: #4e73df; }
        form { display: grid; gap: 10px; margin-bottom: 25px; background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e3e6f0; }
        input, textarea, button { padding: 10px; border: 1px solid #d1d3e2; border-radius: 6px; font-size: 1em; }
        button { background-color: #4e73df; color: white; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #2e59d9; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; }
        #tripList { padding: 0; }
        .trip-item { background: #fff; border: 1px solid #e3e6f0; padding: 15px; margin-bottom: 12px; border-radius: 8px; list-style: none; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .trip-item-header { display: flex; justify-content: space-between; align-items: center; color: #4e73df; font-weight: bold; }
        .trip-id-badge { background-color: #5a5c69; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; }
        .trip-item-content { font-weight: bold; font-size: 1.1em; margin-top: 8px; color: #2e2f37; }
        .trip-item-note { color: #6e707e; font-size: 0.9em; margin-top: 4px; }
        .trip-photos { margin-top: 10px; border-top: 1px dashed #e3e6f0; padding-top: 8px; }
        .photo-item { background: #f8f9fa; border: 1px solid #e3e6f0; padding: 8px; margin-top: 5px; border-radius: 4px; }
        .photo-item img { max-width: 100%; max-height: 120px; display: block; margin-bottom: 5px; }
        
        /* 控制按鈕區塊樣式 */
        .action-container { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; border-top: 1px solid #f1f3f9; padding-top: 10px; }
        .btn-danger { background-color: #e74a3b; }
        .btn-danger:hover { background-color: #be2617; }
        .btn-success { background-color: #1cc88a; }
        .btn-success:hover { background-color: #13855c; }
        .btn-group { display: flex; gap: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 TIMETRO 行事曆助手</h1>
        
        <h2>✨ 新增行程欄位</h2>
        <form id="addTripForm">
            <input type="date" id="date" required>
            <input type="time" id="time" required>
            <input type="text" id="content" placeholder="行程內容" required>
            <textarea id="note" placeholder="備註事項 (選填)"></textarea>
            <button type="submit">儲存行程</button>
        </form>

        <h2>🔍 行程搜尋與列表</h2>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="輸入關鍵字搜尋行程..." style="flex: 1;">
            <button id="searchBtn">搜尋</button>
            <button id="clearBtn" style="background-color: #858796;">清除</button>
        </div>

        <ul id="tripList"></ul>
    </div>

    <script>
        const BASE_URL = window.location.origin + "/api"; 

        const addTripForm = document.getElementById('addTripForm');
        const tripList = document.getElementById('tripList');
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        const clearBtn = document.getElementById('clearBtn');
        let allTasks = [];

        document.addEventListener('DOMContentLoaded', () => {
            fetchTasks();
            startReminderClock();
        });

        // 從後端撈取資料
        function fetchTasks() {
            fetch(`${BASE_URL}/tasks`)
                .then(res => res.json())
                .then(data => { 
                    allTasks = data; 
                    displayTrips(); // 抓到資料後，會自動在 displayTrips 呼叫排序邏輯
                })
                .catch(err => console.error("同步失敗:", err));
        }

        // 新增行程表單送出
        addTripForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const taskData = {
                date: document.getElementById('date').value,
                time: document.getElementById('time').value,
                content: document.getElementById('content').value,
                note: document.getElementById('note').value
            };

            fetch(`${BASE_URL}/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(taskData)
            })
            .then(res => res.json())
            .then(() => {
                alert("🎉 行程新增成功！");
                addTripForm.reset();
                fetchTasks(); // 重新整理，促使新行程依時間插隊排序
            });
        });

        // 🌟 點擊卡片按鈕直接綁定相片與解說
        function addPhotoToTaskDirectly(taskString) {
            const targetTrip = JSON.parse(decodeURIComponent(taskString));
            const photoPath = prompt(`📸 請輸入要為【${targetTrip.content}】新增的照片檔案路徑：`);
            if (!photoPath || photoPath.trim() === "") return;

            const photoDesc = prompt("💬 請輸入這張照片的文字解說（選填）：", "無解說");

            fetch(`${BASE_URL}/web-photo`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: targetTrip.date,
                    time: targetTrip.time,
                    content: targetTrip.content,
                    path: photoPath.trim(),
                    desc: photoDesc ? photoDesc.trim() : "無解說"
                })
            })
            .then(res => res.json())
            .then(() => {
                alert("📸 照片與文字解說已成功紀錄！");
                fetchTasks();
            })
            .catch(err => alert("❌ 錯誤：" + err));
        }

        // 🌟 刪除行程功能
        function deleteTrip(taskString) {
            const targetTrip = JSON.parse(decodeURIComponent(taskString));
            if (confirm(`⚠️ 確定要刪除行程【${targetTrip.content}】嗎？此動作無法復原！`)) {
                fetch(`${BASE_URL}/web-delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        date: targetTrip.date,
                        time: targetTrip.time,
                        content: targetTrip.content
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === "success") {
                        alert("🗑️ 行程已成功刪除！");
                        fetchTasks(); // 重新整理列表
                    } else {
                        alert("❌ 刪除失敗：" + data.message);
                    }
                })
                .catch(err => alert("❌ 連線錯誤：" + err));
            }
        }

        // 🌟 修改/編輯行程功能（核心修正點：修改後自動重新載入並依新時間排序）
        function editTrip(taskString) {
            const targetTrip = JSON.parse(decodeURIComponent(taskString));
            
            const newDate = prompt(`📅 修改日期 (格式: YYYY-MM-DD，原值: ${targetTrip.date})`, targetTrip.date);
            if (newDate === null) return; 
            
            const newTime = prompt(`⏰ 修改時間 (格式: HH:MM，原值: ${targetTrip.time})`, targetTrip.time);
            if (newTime === null) return;
            
            const newContent = prompt(`✨ 修改行程內容 (原值: ${targetTrip.content})`, targetTrip.content);
            if (newContent === null) return;
            if (newContent.trim() === "") {
                alert("❌ 行程內容不能為空！");
                return;
            }
            
            const newNote = prompt(`💡 修改備註事項 (原值: ${targetTrip.note || '無'})`, targetTrip.note || "");
            if (newNote === null) return;

            fetch(`${BASE_URL}/web-edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    old_date: targetTrip.date,
                    old_time: targetTrip.time,
                    old_content: targetTrip.content,
                    new_date: newDate.trim(),
                    new_time: newTime.trim(),
                    new_content: newContent.trim(),
                    new_note: newNote.trim()
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    alert("📝 行程內容已成功更新！");
                    fetchTasks(); // 🔥 重大關鍵：修改成功後，立刻向後端撈取新資料，自動觸發完美排序
                } else {
                    alert("❌ 修改失敗：" + data.message);
                }
            })
            .catch(err => alert("❌ 連線錯誤：" + err));
        }

        // 🌟 核心：排序與過濾處理邏輯
        function getSortedAndFilteredTrips() {
            let result = [...allTasks];
            
            // 🚀 【依照時間順序自動排列】：日期最早的排在最前，如果同一天，則時間最早的排在最前
            result.sort((a, b) => new Date(`${a.date} ${a.time}`) - new Date(`${b.date} ${b.time}`));
            
            // 關鍵字搜尋過濾
            const keyword = searchInput.value.trim();
            if (keyword !== "") {
                result = result.filter(t => 
                    (t.content && t.content.toLowerCase().includes(keyword.toLowerCase())) || 
                    (t.note && t.note.toLowerCase().includes(keyword.toLowerCase()))
                );
            }
            return result;
        }

        // 行事曆鬧鐘定時檢測
        function startReminderClock() {
            setInterval(() => {
                const now = new Date();
                const current = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
                allTasks.forEach(task => {
                    if (`${task.date} ${task.time}` <= current && !task.reminded) {
                        task.reminded = true;
                        alert(`🔔 【TIMETRO 提醒通知】\\n行程：${task.content}\\n時間到了！`);
                        fetch(`${BASE_URL}/web-remind`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ date: task.date, time: task.time, content: task.content })
                        }).then(() => fetchTasks());
                    }
                });
            }, 10000);
        }

        // 渲染畫面卡片
        function displayTrips() {
            tripList.innerHTML = "";
            const sortedTrips = getSortedAndFilteredTrips(); // 取得已經排序好的新陣列
            
            if (sortedTrips.length === 0) {
                tripList.innerHTML = `<li class="no-result">沒有找到任何行程記錄 📭</li>`;
                return;
            }
            
            sortedTrips.forEach((trip, displayIndex) => {
                const noteHTML = trip.note ? `<div class="trip-item-note">💡 備註: ${trip.note}</div>` : '';
                let photosHTML = '';
                if (trip.photos && trip.photos.length > 0) {
                    photosHTML = `<div class="trip-photos"><div style="font-size:0.85em; font-weight:bold; color:#4e73df;">📸 附隨相片牆 (${trip.photos.length} 張)：</div>`;
                    trip.photos.forEach((p, pIdx) => {
                        const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                        let pDesc = (typeof p === 'object' && p !== null && p.desc) ? p.desc : (trip.photo_notes && trip.photo_notes[pIdx] ? trip.photo_notes[pIdx] : "無解說");
                        photosHTML += `
                            <div class="photo-item">
                                <img src="${pPath}" onerror="this.style.display='none';">
                                <span style="font-size:0.85em; color:#6c757d; display:block; word-break:break-all;">📂 路徑: ${pPath}</span>
                                <span style="font-size:0.85em; color:#333; display:block; font-weight:bold;">💬 解說: ${pDesc}</span>
                            </div>`;
                    });
                    photosHTML += `</div>`;
                }
                const serializedTrip = encodeURIComponent(JSON.stringify(trip));
                const li = document.createElement('li');
                li.className = 'trip-item';
                li.innerHTML = `
                    <div class="trip-item-header">
                        <span>📅 ${trip.date} ⏰ ${trip.time}</span>
                        <span class="trip-id-badge">順序編號: ${displayIndex}</span>
                    </div>
                    <div class="trip-item-content">${trip.content}</div>
                    ${noteHTML}
                    ${photosHTML}
                    
                    <div class="action-container">
                        <div class="btn-group">
                            <button onclick="editTrip('${serializedTrip}')" class="btn-success" style="font-size:0.85em; padding:5px 10px;">✏️ 修改行程</button>
                            <button onclick="deleteTrip('${serializedTrip}')" class="btn-danger" style="font-size:0.85em; padding:5px 10px;">🗑️ 刪除</button>
                        </div>
                        <button onclick="addPhotoToTaskDirectly('${serializedTrip}')" style="font-size:0.85em; padding:5px 10px;">➕ 新增相片與解說</button>
                    </div>`;
                tripList.appendChild(li);
            });
        }
        searchBtn.addEventListener('click', displayTrips);
        clearBtn.addEventListener('click', () => { searchInput.value = ''; displayTrips(); });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    return jsonify(storage.load_data())

@app.route('/api/tasks', methods=['POST'])
def add_task():
    try:
        data = request.json
        tasks = storage.load_data()
        new_task = {
            "date": str(data.get("date", "")).strip(),
            "time": str(data.get("time", "")).strip(),
            "content": str(data.get("content", "")).strip(),
            "note": str(data.get("note", "")).strip(),
            "photos": [], "photo_notes": [], "reminded": False
        }
        tasks.append(new_task)
        storage.save_data(tasks)
        print(f"🌐 [網頁端] 成功新增行程: {new_task['content']}")
        return jsonify({"status": "success"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/web-delete', methods=['POST'])
def delete_task():
    try:
        data = request.json or {}
        target_date = str(data.get("date", "")).strip()
        target_time = str(data.get("time", "")).strip()
        target_content = str(data.get("content", "")).strip()
        
        tasks = storage.load_data()
        updated_tasks = []
        found = False
        
        for task in tasks:
            if (str(task.get("date", "")).strip() == target_date and 
                str(task.get("time", "")).strip() == target_time and 
                str(task.get("content", "")).strip() == target_content):
                found = True
                print(f"🌐 [網頁端] 成功刪除行程: {target_content}")
                continue 
            updated_tasks.append(task)
            
        if found:
            storage.save_data(updated_tasks)
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error", "message": "找不到指定的行程項目"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/web-edit', methods=['POST'])
def edit_task():
    try:
        data = request.json or {}
        old_date = str(data.get("old_date", "")).strip()
        old_time = str(data.get("old_time", "")).strip()
        old_content = str(data.get("old_content", "")).strip()
        
        tasks = storage.load_data()
        found = False
        
        for task in tasks:
            if (str(task.get("date", "")).strip() == old_date and 
                str(task.get("time", "")).strip() == old_time and 
                str(task.get("content", "")).strip() == old_content):
                
                task["date"] = str(data.get("new_date", task.get("date", ""))).strip()
                task["time"] = str(data.get("new_time", task.get("time", ""))).strip()
                task["content"] = str(data.get("new_content", task.get("content", ""))).strip()
                task["note"] = str(data.get("new_note", task.get("note", ""))).strip()
                task["reminded"] = False 
                
                found = True
                print(f"🌐 [網頁端] 成功修改行程: 由 [{old_content}] 改為 [{task['content']}]")
                break
                
        if found:
            storage.save_data(tasks)
            return jsonify({"status": "success"}), 200
        else:
            return jsonify({"status": "error", "message": "找不到對應的行程，修改失敗"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/web-photo', methods=['POST'])
def add_photo():
    try:
        data = request.json or {}
        target_date = str(data.get("date", "")).strip()
        target_time = str(data.get("time", "")).strip()
        target_content = str(data.get("content", "")).strip()
        
        tasks = storage.load_data()
        for task in tasks:
            if (str(task.get("date", "")).strip() == target_date and 
                str(task.get("time", "")).strip() == target_time and 
                str(task.get("content", "")).strip() == target_content):
                
                if "photos" not in task or not isinstance(task["photos"], list): task["photos"] = []
                if "photo_notes" not in task or not isinstance(task["photo_notes"], list): task["photo_notes"] = []
                
                task["photos"].append(str(data.get("path", "")).strip())
                task["photo_notes"].append(str(data.get("desc", "無解說")).strip())
                storage.save_data(tasks)
                print(f"🌐 [網頁端] 成功新增照片至 [{target_content}]")
                return jsonify({"status": "success"}), 200
        return jsonify({"status": "not_found"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/api/web-remind', methods=['POST'])
def web_remind():
    try:
        data = request.json or {}
        tasks = storage.load_data()
        for task in tasks:
            if (str(task.get("date", "")) == data.get("date") and 
                str(task.get("time", "")) == data.get("time") and 
                str(task.get("content", "")) == data.get("content")):
                task["reminded"] = True
                storage.save_data(tasks)
                break
        return jsonify({"status": "success"}), 200
    except Exception:
        return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    print("=====================================================")
    print("🌐 TIMETRO 網頁完全一體化伺服器已成功更新並啟動！")
    print("🔗 請開啟瀏覽器並輸入網址前往：http://127.0.0.1:5000")
    print("💡 提示：此版本已包含【全自動時間先後排序】功能")
    print("=====================================================")
    app.run(host='127.0.0.1', port=5000, debug=False)