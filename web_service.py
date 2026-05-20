import storage
import os
from flask import Flask, jsonify, request, render_template_string, send_file
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app) 

# 隱藏 Flask 預設的繁雜小黑窗連線日誌，只顯示嚴重錯誤
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# =====================================================
# 🌐 網頁 HTML 前端：新增修改時可清除/取消提醒時間之功能
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
        
        /* 📸 相片牆網格樣式 */
        .trip-photos { margin-top: 15px; border-top: 1px dashed #e3e6f0; padding-top: 12px; }
        .photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-top: 8px; }
        .photo-item { background: #f8f9fa; border: 1px solid #e3e6f0; padding: 8px; border-radius: 8px; display: flex; flex-direction: column; box-shadow: 0 2px 4px rgba(0,0,0,0.03); position: relative; }
        .photo-wrapper { width: 100%; height: 130px; display: flex; align-items: center; justify-content: center; background: #eaecf4; border-radius: 6px; overflow: hidden; margin-bottom: 6px; }
        .photo-item img { max-width: 100%; max-height: 100%; object-fit: cover; display: block; transition: transform 0.2s; }
        .photo-item img:hover { transform: scale(1.05); }
        .photo-desc-text { font-size: 0.85em; color: #333; font-weight: bold; line-height: 1.3; margin-bottom: 8px; word-break: break-all; }
        
        /* 相片內部的微型控制鈕 */
        .photo-actions { display: flex; gap: 4px; margin-top: auto; border-top: 1px solid #eaecf4; padding-top: 6px; justify-content: flex-end; }
        .btn-photo-mini { font-size: 0.75em; padding: 3px 6px; border-radius: 4px; font-weight: normal; }

        /* 控制按鈕區塊樣式 */
        .action-container { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; border-top: 1px solid #f1f3f9; padding-top: 10px; }
        .btn-danger { background-color: #e74a3b; }
        .btn-danger:hover { background-color: #be2617; }
        .btn-success { background-color: #1cc88a; }
        .btn-success:hover { background-color: #13855c; }
        .btn-group { display: flex; gap: 5px; }

        /* 一頁式彈窗樣式 (Modal UI) */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
        .modal-content { background-color: white; padding: 25px; border-radius: 12px; width: 90%; max-width: 500px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .modal-header { font-size: 1.3em; font-weight: bold; color: #4e73df; margin-bottom: 15px; border-bottom: 1px solid #e3e6f0; padding-bottom: 10px; }
        .modal-buttons { display: flex; gap: 10px; justify-content: flex-end; margin-top: 15px; }
        
        /* 橫向排列輸入框與清除鈕 */
        .time-input-container { display: flex; gap: 8px; align-items: center; }
    </style>
</head>
<body>
    <div class="container">
        <h1>📅 TIMETRO 行事曆助手</h1>
        
        <h2>✨ 新增行程欄位</h2>
        <form id="addTripForm">
            <label style="font-weight: bold; font-size: 0.9em; color: #4e73df; margin-bottom: -5px;">📅 選擇日期</label>
            <input type="date" id="date" required>
            
            <label style="font-weight: bold; font-size: 0.9em; color: #4e73df; margin-bottom: -5px;">⏰ 設置提醒時間 (選填)</label>
            <div class="time-input-container">
                <input type="time" id="time" style="flex: 1;">
                <button type="button" onclick="document.getElementById('time').value=''" style="background-color: #858796; padding: 10px; font-size: 0.9em;">清除不提醒</button>
            </div>
            
            <label style="font-weight: bold; font-size: 0.9em; color: #4e73df; margin-bottom: -5px;">✨ 行程內容</label>
            <input type="text" id="content" placeholder="請輸入行程內容" required>
            
            <label style="font-weight: bold; font-size: 0.9em; color: #4e73df; margin-bottom: -5px;">💡 備註事項</label>
            <textarea id="note" placeholder="備註事項 (選填)"></textarea>
            
            <button type="submit" style="margin-top: 5px;">儲存行程</button>
        </form>

        <h2>🔍 行程搜尋與列表</h2>
        <div class="search-box">
            <input type="text" id="searchInput" placeholder="輸入關鍵字搜尋行程..." style="flex: 1;">
            <button id="searchBtn">搜尋</button>
            <button id="clearBtn" style="background-color: #858796;">清除</button>
        </div>

        <ul id="tripList"></ul>
    </div>

    <div id="editModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">📝 一次修改所有行程欄位</div>
            <form id="editTripForm" style="margin-bottom: 0; background: none; border: none; padding: 0;">
                <input type="hidden" id="editOldDate">
                <input type="hidden" id="editOldTime">
                <input type="hidden" id="editOldContent">

                <label style="font-weight: bold; font-size: 0.9em; color: #5a5c69;">📅 日期 (必須為 YYYY-MM-DD)</label>
                <input type="text" id="editDate" placeholder="YYYY-MM-DD" required>
                
                <label style="font-weight: bold; font-size: 0.9em; color: #5a5c69;">⏰ 設置提醒時間 (為空則代表不提醒)</label>
                <div class="time-input-container" style="margin-bottom: 10px;">
                    <input type="time" id="editTime" style="flex: 1;">
                    <button type="button" onclick="document.getElementById('editTime').value=''" style="background-color: #e74a3b; padding: 9px; font-size: 0.85em;">❌ 取消設置</button>
                </div>
                
                <label style="font-weight: bold; font-size: 0.9em; color: #5a5c69;">✨ 行程內容</label>
                <input type="text" id="editContent" required>
                
                <label style="font-weight: bold; font-size: 0.9em; color: #5a5c69;">💡 備註事項</label>
                <textarea id="editNote" placeholder="選填"></textarea>
                
                <div class="modal-buttons">
                    <button type="button" onclick="closeEditModal()" style="background-color: #858796;">取消</button>
                    <button type="submit" class="btn-success">儲存修改</button>
                </div>
            </form>
        </div>
    </div>

    <div id="photoEditModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">🖼️ 更改相片與文字解說</div>
            <form id="photoEditForm" style="margin-bottom: 0; background: none; border: none; padding: 0;">
                <input type="hidden" id="photoTripString">
                <input type="hidden" id="photoIndex">

                <label style="font-weight: bold; font-size: 0.9em; color: #5a5c69;">📂 照片檔案路徑 / 圖片網址</label>
                <input type="text" id="photoEditPath" required>
                
                <label style="font-weight: bold; font-size: 0.9em; color: #5a5c69;">💬 文字解說</label>
                <input type="text" id="photoEditDesc" placeholder="輸入解說">
                
                <div class="modal-buttons">
                    <button type="button" onclick="closePhotoEditModal()" style="background-color: #858796;">取消</button>
                    <button type="submit" class="btn-success">儲存更改</button>
                </div>
            </form>
        </div>
    </div>

    <script>
        const BASE_URL = window.location.origin + "/api"; 

        const addTripForm = document.getElementById('addTripForm');
        const tripList = document.getElementById('tripList');
        const searchInput = document.getElementById('searchInput');
        const searchBtn = document.getElementById('searchBtn');
        const clearBtn = document.getElementById('clearBtn');
        
        const editModal = document.getElementById('editModal');
        const editTripForm = document.getElementById('editTripForm');
        
        const photoEditModal = document.getElementById('photoEditModal');
        const photoEditForm = document.getElementById('photoEditForm');
        
        let allTasks = [];

        document.addEventListener('DOMContentLoaded', () => {
            fetchTasks();
            startReminderClock();
        });

        function fetchTasks() {
            fetch(`${BASE_URL}/tasks`)
                .then(res => res.json())
                .then(data => { 
                    allTasks = data; 
                    displayTrips(); 
                })
                .catch(err => console.error("同步失敗:", err));
        }

        addTripForm.addEventListener('submit', function (event) {
            event.preventDefault();
            const taskData = {
                date: document.getElementById('date').value,
                time: document.getElementById('time').value.trim(),
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
            if (targetTrip.photos && targetTrip.photos.length >= 10) {
                alert(`❌ 無法新增！【${targetTrip.content}】相片解說已達 10 筆上限！`);
                return;
            }
            const photoPath = prompt(`📸 請輸入要為【${targetTrip.content}】新增的照片檔案路徑：\\n(例如：C:\\\\images\\\\pic.jpg 或 圖片網址)`);
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
            .then(data => {
                if (data.status === "success") {
                    alert("📸 照片與文字解說已成功紀錄！");
                    fetchTasks();
                } else {
                    alert("❌ 錯誤：" + data.message);
                }
            })
            .catch(err => alert("❌ 連線錯誤：" + err));
        }

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
                        fetchTasks(); 
                    } else {
                        alert("❌ 刪除失敗：" + data.message);
                    }
                })
                .catch(err => alert("❌ 連線錯誤：" + err));
            }
        }

        function editTrip(taskString) {
            const targetTrip = JSON.parse(decodeURIComponent(taskString));
            
            document.getElementById('editOldDate').value = targetTrip.date;
            document.getElementById('editOldTime').value = targetTrip.time;
            document.getElementById('editOldContent').value = targetTrip.content;
            
            document.getElementById('editDate').value = targetTrip.date;
            document.getElementById('editTime').value = targetTrip.time || "";
            document.getElementById('editContent').value = targetTrip.content;
            document.getElementById('editNote').value = targetTrip.note || "";
            
            editModal.style.display = 'flex';
        }

        function closeEditModal() {
            editModal.style.display = 'none';
        }

        editTripForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const inputDate = document.getElementById('editDate').value.trim();
            const inputTime = document.getElementById('editTime').value.trim();
            const inputContent = document.getElementById('editContent').value.trim();
            const inputNote = document.getElementById('editNote').value.trim();

            const datePattern = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
            if (!datePattern.test(inputDate)) {
                alert("❌ 日期格式錯誤！\\n請務必符合 YYYY-MM-DD 格式（例如：2026-05-20）");
                return;
            }

            fetch(`${BASE_URL}/web-edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    old_date: document.getElementById('editOldDate').value,
                    old_time: document.getElementById('editOldTime').value,
                    old_content: document.getElementById('editOldContent').value,
                    new_date: inputDate,
                    new_time: inputTime, // 傳回可能已被清空的時間字串
                    new_content: inputContent,
                    new_note: inputNote
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    alert("📝 行程內容已成功更新！");
                    closeEditModal();
                    fetchTasks();
                } else {
                    alert("❌ 修改失敗：" + data.message);
                }
            });
        });

        function openPhotoEditModalDirectly(taskStr, index, path, desc) {
            document.getElementById('photoTripString').value = taskStr;
            document.getElementById('photoIndex').value = index;
            document.getElementById('photoEditPath').value = path;
            document.getElementById('photoEditDesc').value = desc;
            photoEditModal.style.display = 'flex';
        }

        function closePhotoEditModal() {
            photoEditModal.style.display = 'none';
        }

        photoEditForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const targetTrip = JSON.parse(decodeURIComponent(document.getElementById('photoTripString').value));
            const pIndex = document.getElementById('photoIndex').value;
            const newPath = document.getElementById('photoEditPath').value.trim();
            const newDesc = document.getElementById('photoEditDesc').value.trim();

            fetch(`${BASE_URL}/web-photo-update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: targetTrip.date,
                    time: targetTrip.time,
                    content: targetTrip.content,
                    photo_index: parseInt(pIndex),
                    new_path: newPath,
                    new_desc: newDesc
                })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === "success") {
                    alert("🖼️ 相片與解說已成功更新！");
                    closePhotoEditModal();
                    fetchTasks();
                } else {
                    alert("❌ 更新失敗：" + data.message);
                }
            });
        });

        function fireDeleteSinglePhoto(taskStr, index) {
            const targetTrip = JSON.parse(decodeURIComponent(taskStr));
            if(confirm("⚠️ 確定要移除這張相片與其文字解說嗎？")) {
                fetch(`${BASE_URL}/web-photo-delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        date: targetTrip.date,
                        time: targetTrip.time,
                        content: targetTrip.content,
                        photo_index: parseInt(index)
                    })
                })
                .then(res => res.json())
                .then(data => {
                    if(data.status === "success") {
                        alert("🗑️ 相片已成功移除！");
                        fetchTasks();
                    } else {
                        alert("❌ 移除失敗：" + data.message);
                    }
                });
            }
        }

        function getSortedAndFilteredTrips() {
            let result = [...allTasks];
            result.sort((a, b) => {
                const timeA = a.time || "23:59";
                const timeB = b.time || "23:59";
                return new Date(`${a.date} ${timeA}`) - new Date(`${b.date} ${timeB}`);
            });
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
                    // 🌟 如果根本沒有設置提醒時間（為空字串），直接跳過不提醒
                    if (!task.time || task.time.trim() === "") return;

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

        function displayTrips() {
            tripList.innerHTML = "";
            const sortedTrips = getSortedAndFilteredTrips(); 
            
            if (sortedTrips.length === 0) {
                tripList.innerHTML = `<li class="no-result">沒有找到任何行程記錄 📭</li>`;
                return;
            }
            
            sortedTrips.forEach((trip, displayIndex) => {
                const serializedTrip = encodeURIComponent(JSON.stringify(trip));
                const currentPhotoCount = trip.photos ? trip.photos.length : 0;

                const li = document.createElement('li');
                li.className = 'trip-item';
                
                // 🌟 優化時間欄位顯示：如果被清空沒設置，改貼心提示「未設置提醒」
                const timeDisplay = (trip.time && trip.time.trim() !== "") ? `⏰ 提醒時間: ${trip.time}` : `⏰ 未設置提醒`;

                const noteHTML = trip.note ? `<div class="trip-item-note">💡 備註: ${trip.note}</div>` : '';
                li.innerHTML = `
                    <div class="trip-item-header">
                        <span>📅 ${trip.date} &nbsp;&nbsp; ${timeDisplay}</span>
                        <span class="trip-id-badge">順序編號: ${displayIndex}</span>
                    </div>
                    <div class="trip-item-content">${trip.content}</div>
                    ${noteHTML}
                    <div class="photos-mount-point"></div>
                    <div class="action-container">
                        <div class="btn-group">
                            <button class="btn-success btn-edit-trip" style="font-size:0.85em; padding:5px 10px;">✏️ 修改行程</button>
                            <button class="btn-danger btn-delete-trip" style="font-size:0.85em; padding:5px 10px;">🗑️ 刪除</button>
                        </div>
                        <button class="btn-add-photo" style="font-size:0.85em; padding:5px 10px;">➕ 新增相片與文字解說 (${currentPhotoCount}/10)</button>
                    </div>
                `;

                li.querySelector('.btn-edit-trip').onclick = () => editTrip(serializedTrip);
                li.querySelector('.btn-delete-trip').onclick = () => deleteTrip(serializedTrip);
                li.querySelector('.btn-add-photo').onclick = () => addPhotoToTaskDirectly(serializedTrip);

                if (trip.photos && trip.photos.length > 0) {
                    const mountPoint = li.querySelector('.photos-mount-point');
                    
                    const photosContainer = document.createElement('div');
                    photosContainer.className = 'trip-photos';
                    photosContainer.innerHTML = `<div style="font-size:0.85em; font-weight:bold; color:#4e73df;">📸 附隨相片牆 (${currentPhotoCount}/10 筆)：</div>`;
                    
                    const photoGrid = document.createElement('div');
                    photoGrid.className = 'photo-grid';

                    trip.photos.forEach((p, pIdx) => {
                        const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                        let pDesc = (typeof p === 'object' && p !== null && p.desc) ? p.desc : (trip.photo_notes && trip.photo_notes[pIdx] ? trip.photo_notes[pIdx] : "無解說");
                        
                        let imgSrc = pPath;
                        if (!pPath.startsWith('http://') && !pPath.startsWith('https://')) {
                            imgSrc = `${window.location.origin}/api/view-photo?path=${encodeURIComponent(pPath)}`;
                        }

                        const photoItem = document.createElement('div');
                        photoItem.className = 'photo-item';
                        
                        photoItem.innerHTML = `
                            <div class="photo-wrapper">
                                <img src="${imgSrc}" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200'; this.style.opacity='0.5';">
                            </div>
                            <div class="photo-desc-text">💬 <span class="txt-span"></span></div>
                            <div class="photo-actions">
                                <button type="button" class="btn-success btn-photo-mini inner-edit-btn">✏️ 更改</button>
                                <button type="button" class="btn-danger btn-photo-mini inner-del-btn">🗑️</button>
                            </div>
                        `;

                        photoItem.querySelector('.txt-span').textContent = pDesc;

                        photoItem.querySelector('.inner-edit-btn').onclick = function() {
                            openPhotoEditModalDirectly(serializedTrip, pIdx, pPath, pDesc);
                        };
                        photoItem.querySelector('.inner-del-btn').onclick = function() {
                            fireDeleteSinglePhoto(serializedTrip, pIdx);
                        };

                        photoGrid.appendChild(photoItem);
                    });

                    photosContainer.appendChild(photoGrid);
                    mountPoint.appendChild(photosContainer);
                }

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

@app.route('/api/view-photo', methods=['GET'])
def view_photo():
    file_path = request.args.get('path', '').strip()
    if not file_path:
        return "Missing path", 400
    file_path = file_path.strip('"').strip("'")
    if os.path.exists(file_path) and os.path.isfile(file_path):
        try: return send_file(file_path)
        except Exception as e: return f"Error: {str(e)}", 500
    else: return "Not found", 404

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
            "time": str(data.get("time", "")).strip(), # 儲存空字串代表未設置時間
            "content": str(data.get("content", "")).strip(),
            "note": str(data.get("note", "")).strip(),
            "photos": [], "photo_notes": [], "reminded": False
        }
        tasks.append(new_task)
        storage.save_data(tasks)
        return jsonify({"status": "success"}), 201
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route('/api/web-delete', methods=['POST'])
def delete_task():
    try:
        data = request.json or {}
        target_date = str(data.get("date", "")).strip()
        target_time = str(data.get("time", "")).strip()
        target_content = str(data.get("content", "")).strip()
        
        tasks = storage.load_data()
        updated_tasks = [t for t in tasks if not (str(t.get("date", "")).strip() == target_date and str(t.get("time", "")).strip() == target_time and str(t.get("content", "")).strip() == target_content)]
        storage.save_data(updated_tasks)
        return jsonify({"status": "success"}), 200
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/web-edit', methods=['POST'])
def edit_task():
    try:
        data = request.json or {}
        old_date = str(data.get("old_date", "")).strip()
        old_time = str(data.get("old_time", "")).strip()
        old_content = str(data.get("old_content", "")).strip()
        
        tasks = storage.load_data()
        for task in tasks:
            if (str(task.get("date", "")).strip() == old_date and str(task.get("time", "")).strip() == old_time and str(task.get("content", "")).strip() == old_content):
                task["date"] = str(data.get("new_date", task.get("date", ""))).strip()
                task["time"] = str(data.get("new_time", "")).strip() # 完美更新空字串或新設定的時間
                task["content"] = str(data.get("new_content", task.get("content", ""))).strip()
                task["note"] = str(data.get("new_note", task.get("note", ""))).strip()
                task["reminded"] = False 
                break
        storage.save_data(tasks)
        return jsonify({"status": "success"}), 200
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/web-photo', methods=['POST'])
def add_photo():
    try:
        data = request.json or {}
        target_date = str(data.get("date", "")).strip()
        target_time = str(data.get("time", "")).strip()
        target_content = str(data.get("content", "")).strip()
        
        tasks = storage.load_data()
        for task in tasks:
            if (str(task.get("date", "")).strip() == target_date and str(task.get("time", "")).strip() == target_time and str(task.get("content", "")).strip() == target_content):
                if "photos" not in task: task["photos"] = []
                if "photo_notes" not in task: task["photo_notes"] = []
                if len(task["photos"]) >= 10: return jsonify({"status": "error", "message": "已達10筆上限"}), 200
                
                task["photos"].append(str(data.get("path", "")).strip())
                task["photo_notes"].append(str(data.get("desc", "無解說")).strip())
                break
        storage.save_data(tasks)
        return jsonify({"status": "success"}), 200
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/api/web-photo-update', methods=['POST'])
def update_photo():
    try:
        data = request.json or {}
        t_date = str(data.get("date", "")).strip()
        t_time = str(data.get("time", "")).strip()
        t_content = str(data.get("content", "")).strip()
        p_index = data.get("photo_index")
        
        tasks = storage.load_data()
        for task in tasks:
            if (str(task.get("date", "")).strip() == t_date and str(task.get("time", "")).strip() == t_time and str(task.get("content", "")).strip() == t_content):
                if 0 <= p_index < len(task.get("photos", [])):
                    task["photos"][p_index] = str(data.get("new_path", "")).strip()
                    task["photo_notes"][p_index] = str(data.get("new_desc", "無解說")).strip()
                    break
        storage.save_data(tasks)
        return jsonify({"status": "success"}), 200
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/web-photo-delete', methods=['POST'])
def delete_photo():
    try:
        data = request.json or {}
        t_date = str(data.get("date", "")).strip()
        t_time = str(data.get("time", "")).strip()
        t_content = str(data.get("content", "")).strip()
        p_index = data.get("photo_index")
        
        tasks = storage.load_data()
        for task in tasks:
            if (str(task.get("date", "")).strip() == t_date and str(task.get("time", "")).strip() == t_time and str(task.get("content", "")).strip() == t_content):
                if 0 <= p_index < len(task.get("photos", [])):
                    task["photos"].pop(p_index)
                    task["photo_notes"].pop(p_index)
                    break
        storage.save_data(tasks)
        return jsonify({"status": "success"}), 200
    except Exception as e: return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/web-remind', methods=['POST'])
def web_remind():
    try:
        data = request.json or {}
        tasks = storage.load_data()
        for task in tasks:
            if (str(task.get("date", "")) == data.get("date") and str(task.get("time", "")) == data.get("time") and str(task.get("content", "")) == data.get("content")):
                task["reminded"] = True
                storage.save_data(tasks)
                break
        return jsonify({"status": "success"}), 200
    except Exception: return jsonify({"status": "success"}), 200

if __name__ == '__main__':
    print("=====================================================")
    print("🌐 TIMETRO 自由清除提醒時間完全修復版啟動！")
    print("🔗 請開啟瀏覽器前往：http://127.0.0.1:5000")
    print("=====================================================")
    app.run(host='127.0.0.1', port=5000, debug=False)