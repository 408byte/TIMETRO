const BASE_URL = "http://127.0.0.1:5000/api"; 

const addTripForm = document.getElementById('addTripForm');
const tripList = document.getElementById('tripList');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const clearBtn = document.getElementById('clearBtn');

let allTasks = []; 

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    fetchTasks();         
    startReminderClock(); 
    
    // 隱藏原本可能對不上 ID 的舊表單（如果它存在的話，避免畫面混亂）
    const oldPhotoForm = document.getElementById('addPhotoForm');
    if (oldPhotoForm) {
        oldPhotoForm.style.display = 'none';
    }
});

// 從後端讀取行程
function fetchTasks() {
    fetch(`${BASE_URL}/tasks`)
        .then(res => res.json())
        .then(data => {
            allTasks = data;
            displayTrips(); 
        })
        .catch(err => console.error("連線伺服器失敗:", err));
}

// 表單：網頁新增行程
if (addTripForm) {
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
        .then(res => {
            if(!res.ok) throw new Error("新增失敗");
            return res.json();
        })
        .then(() => {
            alert(`🎉 行程新增成功！`);
            addTripForm.reset(); 
            fetchTasks();     
        })
        .catch(err => {
            alert("❌ 新增行程失敗：連線不到 Python 伺服器，請確認 web_server.py 是否正在執行。");
        });
    });
}

// 🌟 換新方法：點擊卡片按鈕，直接為特定的行程物件新增相片（免去輸入編號與 HTML ID 衝突）
function addPhotoToTaskDirectly(taskString) {
    // 解碼傳進來的卡片資料
    const targetTrip = JSON.parse(decodeURIComponent(taskString));
    
    // 彈出視窗請使用者輸入
    const photoPath = prompt(`📸 請輸入要為【${targetTrip.content}】新增的照片檔案路徑：`);
    if (photoPath === null) return; // 使用者按取消
    
    if (photoPath.trim() === "") {
        alert("❌ 照片路徑不可為空！");
        return;
    }

    const photoDesc = prompt("💬 請輸入這張照片的文字解說（選填）：", "無解說");
    
    // 封裝特徵
    const payload = {
        date: targetTrip.date,
        time: targetTrip.time,
        content: targetTrip.content,
        path: photoPath.trim(),
        desc: photoDesc ? photoDesc.trim() : "無解說"
    };

    // 發送請求
    fetch(`${BASE_URL}/web-photo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (!res.ok) throw new Error("伺服器回應錯誤");
        return res.json();
    })
    .then(data => {
        alert("📸 照片與文字解說已成功紀錄！");
        fetchTasks(); // 重新整理網頁畫面
    })
    .catch(err => {
        console.error(err);
        alert("❌ 新增照片失敗：連線不到後端，請確認 web_server.py 是否有正常開啟。");
    });
}

// 排序功能
function getSortedAndFilteredTrips() {
    let result = [...allTasks];
    result.sort((a, b) => new Date(`${a.date} ${a.time}`) - new Date(`${b.date} ${b.time}`));

    const keyword = searchInput ? searchInput.value.trim() : "";
    if (keyword !== "") {
        result = result.filter(t => 
            (t.content && t.content.toLowerCase().includes(keyword.toLowerCase())) || 
            (t.note && t.note.toLowerCase().includes(keyword.toLowerCase()))
        );
    }
    return result;
}

// 提醒功能
function startReminderClock() {
    setInterval(() => {
        const now = new Date();
        const currentTimeString = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')} ${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

        allTasks.forEach(task => {
            const taskTimeString = `${task.date} ${task.time}`;
            if (currentTimeString >= taskTimeString && !task.reminded) {
                task.reminded = true; 
                alert(`🔔 【TIMETRO 提醒通知】\n行程：${task.content}\n時間到了！`);
                
                fetch(`${BASE_URL}/web-remind`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ date: task.date, time: task.time, content: task.content })
                }).then(() => fetchTasks()).catch(err => console.error(err));
            }
        });
    }, 10000); 
}

// 渲染畫面
function displayTrips() {
    if (!tripList) return;
    tripList.innerHTML = ""; 
    const sortedTrips = getSortedAndFilteredTrips();

    if (sortedTrips.length === 0) {
        tripList.innerHTML = `<li class="no-result">沒有找到任何行程記錄 📭</li>`;
        return;
    }

    sortedTrips.forEach((trip, displayIndex) => {
        const noteHTML = trip.note ? `<div class="trip-item-note" style="color:#6e707e; font-size:0.9em; margin-top:4px;">💡 備註: ${trip.note}</div>` : '';
        
        let photosHTML = '';
        if (trip.photos && trip.photos.length > 0) {
            photosHTML = `<div class="trip-photos" style="margin-top:10px; border-top:1px dashed #e3e6f0; padding-top:8px;"><div class="photo-title" style="font-size:0.85em; font-weight:bold; color:#4e73df;">📸 附隨相片牆 (${trip.photos.length} 張)：</div><div class="photo-grid">`;
            trip.photos.forEach((p, pIdx) => {
                const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                let pDesc = "無解說";
                if (typeof p === 'object' && p !== null && p.desc) {
                    pDesc = p.desc;
                } else if (trip.photo_notes && trip.photo_notes[pIdx]) {
                    pDesc = trip.photo_notes[pIdx];
                }
                photosHTML += `
                    <div class="photo-item" style="background:#f8f9fa; border:1px solid #e3e6f0; padding:8px; margin-top:5px; border-radius:4px;">
                        <img src="${pPath}" alt="行程照片" style="max-width:100%; max-height:120px; display:block; margin-bottom:5px;" onerror="this.style.display='none';">
                        <span style="font-size:0.85em; color:#6c757d; display:block; word-break:break-all;">📂 路徑: ${pPath}</span>
                        <span style="font-size:0.85em; color:#333; display:block; font-weight:bold;">💬 解說: ${pDesc}</span>
                    </div>
                `;
            });
            photosHTML += `</div></div>`;
        }

        // 把當前行程資料安全的編碼，作為按鈕點擊時傳遞的參數
        const serializedTrip = encodeURIComponent(JSON.stringify(trip));

        const li = document.createElement('li');
        li.className = 'trip-item';
        li.style = "background:#white; border:1px solid #e3e6f0; padding:15px; margin-bottom:12px; border-radius:8px; list-style:none; box-shadow:0 2px 4px rgba(0,0,0,0.02);";
        li.innerHTML = `
            <div class="trip-item-header" style="display:flex; justify-content:space-between; align-items:center;">
                <span style="color:#4e73df; font-weight:bold;">📅 ${trip.date} ⏰ ${trip.time}</span>
                <span class="trip-id-badge" style="background-color:#5a5c69; color:white; padding:2px 6px; border-radius:4px; font-size:0.8em;">行程編號: ${displayIndex}</span>
            </div>
            <div class="trip-item-content" style="font-weight:bold; font-size:1.1em; margin-top:8px; color:#2e2f37;">${trip.content}</div>
            ${noteHTML}
            ${photosHTML}
            
            <div style="text-align:right; margin-top:10px;">
                <button onclick="addPhotoToTaskDirectly('${serializedTrip}')" style="background-color:#4e73df; color:white; border:none; padding:5px 10px; border-radius:4px; cursor:pointer; font-size:0.85em; font-weight:bold;">
                    ➕ 新增相片與文字解說
                </button>
            </div>
        `;
        tripList.appendChild(li);
    });
}

if(searchBtn) searchBtn.addEventListener('click', displayTrips);
if(clearBtn) clearBtn.addEventListener('click', () => { if(searchInput) searchInput.value = ''; displayTrips(); });