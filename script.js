// 1. 綁定 HTML 的表單元素
const tripForm = document.querySelector('form');

// 2. 監聽表單的 submit（送出）事件
tripForm.addEventListener('submit', function (event) {
    // 阻擋表單預設的跳頁送出行為
    event.preventDefault();

    // 3. 取得使用者在表單輸入的值
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;
    const content = document.getElementById('content').value;
    const note = document.getElementById('note').value;

    // 4. 打包成一個行程物件 (Object)
    const newTrip = {
        id: Date.now(), // 用時間戳記當作唯一的 ID
        date: date,
        time: time,
        content: content,
        note: note
    };

    // 5. 儲存行程資料
    saveTripToLocalStorage(newTrip);

    // 6. 跳出成功訊息並清空表單
    alert(`🎉 行程新增成功！\n名稱：${content}\n時間：${date} ${time}`);
    tripForm.reset(); 
});

// 【儲存資料的函式】把行程存入瀏覽器的記憶體中
function saveTripToLocalStorage(trip) {
    // 檢查原本有沒有舊的行程紀錄，沒有就建立新陣列
    let trips = JSON.parse(localStorage.getItem('myTrips')) || [];
    
    // 把新的行程推入陣列
    trips.push(trip);
    
    // 轉成字串後存回 LocalStorage
    localStorage.setItem('myTrips', JSON.stringify(trips));
    
    // 在主控台（Console）列印出目前所有的行程，方便你檢查
    console.log("目前所有行程：", trips);
}