import storage
import os
from flask import Flask, jsonify, request, render_template_string, send_file
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app) # 雖然同源了，但保留防呆

# 隱藏 Flask 預設的日誌
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# =====================================================
# 🌐 網頁 HTML 前端：直接融入 Python 內建，徹底解決網頁開啟檔案的安全性阻擋
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
        #tripList, #reviewList { padding: 0; }
        .trip-item, .review-item { background: #fff; border: 1px solid #e3e6f0; padding: 15px; margin-bottom: 12px; border-radius: 8px; list-style: none; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
        .trip-item-header, .review-item-header { display: flex; justify-content: space-between; align-items: center; color: #4e73df; font-weight: bold; }
        .trip-id-badge { background-color: #5a5c69; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; }
        .trip-item-content, .review-item-content { font-weight: bold; font-size: 1.1em; margin-top: 8px; color: #2e2f37; }
        .trip-item-note, .review-item-note { color: #6e707e; font-size: 0.9em; margin-top: 4px; }
        .trip-photos, .review-photos { margin-top: 10px; border-top: 1px dashed #e3e6f0; padding-top: 8px; }
        .photo-item { background: #f8f9fa; border: 1px solid #e3e6f0; padding: 8px; margin-top: 5px; border-radius: 4px; }
        .photo-item img { max-width: 100%; max-height: 120px; display: block; margin-bottom: 5px; }
        .no-result { list-style: none; color: #858796; padding: 10px; background: #f8f9fa; border-radius: 6px; text-align: center; }
        .review-section { background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e3e6f0; margin-top: 25px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 TIMETRO 行事曆助手</h1>
        
        <h2>✨ 新增修改時可清除/取消提醒時間之功能</h2>
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

        <div class="review-section">
            <h2>💖 當月行程與相片日記回顧</h2>
            <div class="search-box">
                <input type="month" id="reviewMonthInput" style="flex: 1;">
                <button id="reviewBtn" style="background-color: #1cc88a;">生成月度回顧展</button>
            </div>
            <ul id="reviewList"></ul>
        </div>
    </div>

    <script>
        const BASE_URL = window.location.origin + "/api"; 

        const addTripForm = document.getElementById('addTripForm');
        const tripList = document.getElementById('tripList');
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        const clearBtn = document.getElementById('clearBtn');
        
        // 🌟 月度回顧前端元件
        const reviewMonthInput = document.getElementById('reviewMonthInput');
        const reviewBtn = document.getElementById('reviewBtn');
        const reviewList = document.getElementById('reviewList');
        
        let allTasks = [];

        // 預設將回顧月份設為當前月份
        const today = new Date();
        reviewMonthInput.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;

        document.addEventListener('DOMContentLoaded', () => {
            fetchTasks();
            startReminderClock();
        });

        function fetchTasks() {
            fetch(`${BASE_URL}/tasks`)
                .then(res => res.json())
                .then(data => { allTasks = data; displayTrips(); })
                .catch(err => console.error("同步失敗:", err));
        }

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
                fetchTasks();
            });
        });

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

        function getSortedAndFilteredTrips() {
            let result = [...allTasks];
            result.sort((a, b) => new Date(`${a.date} ${a.time}`) - new Date(`${b.date} ${b.time}`));
            const keyword = searchInput.value.trim();
            if (keyword !== "") {
                result = result.filter(t => 
                    (t.content && t.content.toLowerCase().includes(keyword.toLowerCase())) || 
                    (t.note && t.note.toLowerCase().includes(keyword.toLowerCase()))
                );
            }
            return result;
        }

        function startReminderClock() {
            setInterval(() => {
                const now = new Date();
                const current = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
                allTasks.forEach(task => {
                    if (task.date && task.time && `${task.date} ${task.time}` <= current && !task.reminded) {
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

        function displayTrips() {
            tripList.innerHTML = "";
            const sortedTrips = getSortedAndFilteredTrips();
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
                        <span class="trip-id-badge">行程編號: ${displayIndex}</span>
                    </div>
                    <div class="trip-item-content">${trip.content}</div>
                    ${noteHTML}
                    ${photosHTML}
                    <div style="text-align:right; margin-top:10px;">
                        <button onclick="addPhotoToTaskDirectly('${serializedTrip}')" style="font-size:0.85em; padding:5px 10px;">➕ 新增相片與文字解說</button>
                    </div>`;
                tripList.appendChild(li);
            });
        }
        
        // 🌟 月度回顧前端渲染邏輯
        reviewBtn.addEventListener('click', () => {
            const selectedMonth = reviewMonthInput.value; 
            if (!selectedMonth) {
                alert("請選擇月份！");
                return;
            }
            
            fetch(`${BASE_URL}/monthly-review?month=${selectedMonth}`)
                .then(res => res.json())
                .then(data => {
                    reviewList.innerHTML = "";
                    if (data.length === 0) {
                        reviewList.innerHTML = `<li class="no-result">找不到該月份的任何行程紀錄。</li>`;
                        return;
                    }
                    data.forEach(trip => {
                        const noteHTML = trip.note ? `<div class="review-item-note">💡 備註: ${trip.note}</div>` : '';
                        let photosHTML = '';
                        if (trip.photos && trip.photos.length > 0) {
                            photosHTML = `<div class="review-photos"><div style="font-size:0.85em; font-weight:bold; color:#4e73df;">📸 當月相片回顧：</div>`;
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
                        const li = document.createElement('li');
                        li.className = 'review-item';
                        li.innerHTML = `
                            <div class="review-item-header">
                                <span>📅 ${trip.date} ⏰ ${trip.time}</span>
                            </div>
                            <div class="review-item-content">${trip.content}</div>
                            ${noteHTML}
                            ${photosHTML}`;
                        reviewList.appendChild(li);
                    });
                })
                .catch(err => alert("讀取回顧失敗：" + err));
        });

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

# 🌟 每月生活回顧 API 接口
@app.route('/api/monthly-review', methods=['GET'])
def get_monthly_review():
    try:
        target_month = request.args.get('month', '').strip() 
        clean_target = target_month.replace("-", "") 
        
        tasks = storage.load_data()
        filtered_tasks = []
        
        for task in tasks:
            clean_date = str(task.get("date", "")).replace("-", "") 
            if clean_date.startswith(clean_target):
                filtered_tasks.append(task)
                
        return jsonify(filtered_tasks), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
    print("🌐 TIMETRO 網頁一體化伺服器已成功啟動！")
    print("🔗 請開啟瀏覽器並輸入網址前往：http://127.0.0.1:5000")
    print("=====================================================")
    app.run(host='127.0.0.1', port=5000, debug=False)