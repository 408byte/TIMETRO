// ====== 1. 元素綁定 ======
const tripForm = document.querySelector('form');
const tripList = document.getElementById('tripList');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const clearBtn = document.getElementById('clearBtn');

// ====== 2. 初始化動作 ======
// 當網頁一打開，自動把之前存好的行程顯示出來
document.addEventListener('DOMContentLoaded', () => {
    displayTrips();
});

// ====== 3. 監聽事件 ======

// 監聽「新增行程」表單送出
tripForm.addEventListener('submit', function (event) {
    event.preventDefault();

    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;
    const content = document.getElementById('content').value;
    const note = document.getElementById('note').value;

    const newTrip = {
        id: Date.now(),
        date: date,
        time: time,
        content: content,
        note: note
    };

    saveTripToLocalStorage(newTrip);
    tripForm.reset(); 
    
    // 新增成功後，立刻重新整理下方的列表顯示
    displayTrips();
});

// 監聽「搜尋」按鈕點擊
searchBtn.addEventListener('click', () => {
    const keyword = searchInput.value.trim();
    displayTrips(keyword); // 傳入關鍵字進行過濾
});

// 監聽輸入框按下 Enter 鍵也能搜尋
searchInput.addEventListener('keypress', (event) => {
    if (event.key === 'Enter') {
        const keyword = searchInput.value.trim();
        displayTrips(keyword);
    }
});

// 監聽「清除關鍵字」按鈕
clearBtn.addEventListener('click', () => {
    searchInput.value = ''; // 清空輸入框
    displayTrips(); // 顯示全部行程
});


// ====== 4. 功能函式 (Functions) ======

// 【儲存資料】
function saveTripToLocalStorage(trip) {
    let trips = JSON.parse(localStorage.getItem('myTrips')) || [];
    trips.push(trip);
    localStorage.setItem('myTrips', JSON.stringify(trips));
}

// 【顯示與查詢行程】
// 參數 keyword 預設是空字串，代表顯示全部。如果有傳入字串，就會進行過濾。
function displayTrips(keyword = "") {
    // 先清空目前畫面上顯示的列表，避免重複疊加
    tripList.innerHTML = "";

    // 從 LocalStorage 撈出所有行程
    let trips = JSON.parse(localStorage.getItem('myTrips')) || [];

    // 依照日期與時間排序（讓接近的行程排在前面）
    trips.sort((a, b) => new Date(`${a.date} ${a.time}`) - new Date(`${b.date} ${b.time}`));

    // 如果有輸入關鍵字，就進行過濾（搜尋「行程內容」或「備註」）
    if (keyword !== "") {
        trips = trips.filter(trip => 
            trip.content.toLowerCase().includes(keyword.toLowerCase()) || 
            trip.note.toLowerCase().includes(keyword.toLowerCase())
        );
    }

    // 如果完全沒有行程（或搜尋不到結果）
    if (trips.length === 0) {
        tripList.innerHTML = `<li class="no-result">沒有找到任何行程記錄 📭</li>`;
        return;
    }

    // 將篩選後的每一筆行程，組合好 HTML 渲染到網頁上
    trips.forEach(trip => {
        // 檢查有沒有備註，有才顯示備註區塊
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