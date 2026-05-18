const API_URL = "http://127.0.0.1:5000/api/tasks";

// ====== 1. 元素綁定 ======
const tripForm = document.querySelector('form');
const tripList = document.getElementById('tripList');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const clearBtn = document.getElementById('clearBtn');

// 全域變數：儲存從後端抓下來的所有行程
let allTasks = []; 

// ====== 2. 初始化動作 ======
document.addEventListener('DOMContentLoaded', () => {
    fetchTasks();         // 從 Python 後端抓取資料
    startReminderClock(); // 啟動前端計時提醒鬧鐘
});

// ====== 3. 功能函式 ======

// 【從後端撈取所有行程】
function fetchTasks() {
    fetch(API_URL)
        .then(res => {
            if (!res.ok) throw new Error('無法取得後端資料');
            return res.json();
        })
        .then(data => {
            allTasks = data; // 更新全域陣列
            displayTrips();  // 渲染到網頁畫面上
        })
        .catch(err => console.error("連線到 Python 後端失敗:", err));
}

// 【向後端發送新增行程】
tripForm.addEventListener('submit', function (event) {
    event.preventDefault(); // 阻止表單預設跳頁行為

    // 抓取網頁上輸入的值
    const taskData = {
        date: document.getElementById('date').value,
        time: document.getElementById('time').value,
        content: document.getElementById('content').value,
        note: document.getElementById('note').value
    };

    // 發送 POST 請求給 Python Flask
    fetch(API_URL, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json' 
        },
        body: JSON.stringify(taskData)
    })
    .then(res => {
        if (!res.ok) throw new Error('伺服器回應錯誤');
        return res.json();
    })
    .then(data => {
        alert(`🎉 行程新增成功！\n內容：${taskData.content}`);
        tripForm.reset(); // 清空輸入框
        fetchTasks();     // 🌟 核心：立刻重新撈取後端最新資料，刷新網頁下方的列表
    })
    .catch(err => {
        console.error("新增失敗:", err);
        alert("新增失敗，請確認你的 Python 後端程式是否有正常啟動！");
    });
});

// ====== 4. 前端即時提醒功能 ======
function startReminderClock() {
    // 每 10 秒自動比對一次時間
    setInterval(() => {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const date = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        
        const currentTimeString = `${year}-${month}-${date} ${hours}:${minutes}`;

        allTasks.forEach(task => {
            const taskTimeString = `${task.date} ${task.time}`;

            // 如果時間到了，且在本次網頁開啟期間內尚未在前端提醒過
            if (currentTimeString >= taskTimeString && !task.remindedByJS) {
                task.remindedByJS = true; // 標記為已提醒，避免重複跳視窗
                alert(`🔔 【TIMETRO 提醒通知】\n行程：${task.content}\n時間到了，該開始囉！`);
            }
        });
    }, 10000); 
}

// ====== 5. 畫面渲染與查詢功能 ======
function displayTrips(keyword = "") {
    tripList.innerHTML = ""; // 先清空舊列表
    let filteredTrips = [...allTasks];

    // 依時間由近到遠排序
    filteredTrips.sort((a, b) => new Date(`${a.date} ${a.time}`) - new Date(`${b.date} ${b.time}`));

    // 如果有輸入關鍵字，過濾內容與備註
    if (keyword !== "") {
        filteredTrips = filteredTrips.filter(t => 
            (t.content && t.content.toLowerCase().includes(keyword.toLowerCase())) || 
            (t.note && t.note.toLowerCase().includes(keyword.toLowerCase()))
        );
    }

    if (filteredTrips.length === 0) {
        tripList.innerHTML = `<li class="no-result">沒有找到任何行程記錄 📭</li>`;
        return;
    }

    // 將資料轉為 HTML 元件並塞入網頁
    filteredTrips.forEach(trip => {
        const noteHTML = trip.note ? `<div class="trip-item-note">💡 備註: ${trip.note}</div>` : '';
        const li = document.createElement('li');
        li.className = 'trip-item';
        li.innerHTML = `
            <div class="trip-item-header">
                <span>📅 ${trip.date}</span>
                <span>⏰ ${trip.time}</span>
            </div>
            <div class="trip-item-content">${trip.content}</div>
            ${noteHTML}
        `;
        tripList.appendChild(li);
    });
}

// 查詢與清除按鈕的監聽
searchBtn.addEventListener('click', () => displayTrips(searchInput.value.trim()));
clearBtn.addEventListener('click', () => { searchInput.value = ''; displayTrips(); });