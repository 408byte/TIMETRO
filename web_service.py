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
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>TIMETRO 行事曆助手 — 完全版</title>
    <style>
        /* 🌍 全域初始化：強制所有元素寬度計算包含 Padding，防止滿版時爆出右邊邊界 */
        * { box-sizing: border-box; }

        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background-color: #f4f6f9; 
            color: #333; 
            margin: 0; 
            padding: 0; 
            width: 100%;
            height: 100vh;
            overflow: hidden;
        }

        /* 🚀 寬幅滿版核心：拿掉 800px 限制，寬度貼緊 100%，並設定一個舒適的左右極限留白 */
        .container { 
            display: flex;
            width: 100%; 
            height: 100vh;
            margin: 0;
            padding: 0;
            background: #fff;
        }

        h1, h2 { color: #4e73df; }
        
        /* 讓輸入表單自動拉滿外框 */
        form { display: grid; gap: 10px; margin-bottom: 25px; background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e3e6f0; width: 100%; }
        input, textarea, button { padding: 10px; border: 1px solid #d1d3e2; border-radius: 6px; font-size: 1em; width: 100%; }
        
        /* 搜尋按鈕與清除按鈕不隨便拉成滿版，保持精緻的寬度 */
        .search-box input { flex: 1; width: auto; }
        .search-box button { width: auto; }
        
        button { background-color: #4e73df; color: white; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #2e59d9; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; width: 100%; }
        #tripList { padding: 0; width: 100%; }
        
        .trip-item { background: #fff; border: 1px solid #e3e6f0; padding: 15px; margin-bottom: 12px; border-radius: 8px; list-style: none; box-shadow: 0 2px 4px rgba(0,0,0,0.02); width: 100%; }
        .trip-item-header { display: flex; justify-content: space-between; align-items: center; color: #4e73df; font-weight: bold; }
        .trip-id-badge { background-color: #5a5c69; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.8em; width: auto; }
        .trip-item-content { font-weight: bold; font-size: 1.1em; margin-top: 8px; color: #2e2f37; }
        .trip-item-note { color: #6e707e; font-size: 0.9em; margin-top: 4px; }
        #reviewList { display: block; padding: 0; list-style: none; margin-top: 0; width: 100%; }
        
        /* 📅 響應式行事曆網格：確保在寬螢幕和窄螢幕上都能自適應 */
        .review-calendar { display: grid; gap: 10px; width: 100%; overflow-x: auto; }
        .calendar-weekdays { display: grid; grid-template-columns: repeat(7, 1fr); text-align: center; font-weight: bold; color: #4e73df; margin-bottom: 6px; min-width: 700px; }
        .calendar-days { display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; min-width: 700px; }
        
        .calendar-day { min-height: 120px; background: #f9fbff; border: none; border-radius: 12px; padding: 10px; box-shadow: none; display: flex; flex-direction: column; justify-content: flex-start; }
        .calendar-day.empty { background: transparent; border: none; box-shadow: none; }
        .day-row { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; margin-bottom: 8px; }
        .day-number { font-size: 0.9em; font-weight: bold; color: #4e73df; }
        .day-event-title { background: rgba(78, 115, 223, 0.12); color: #1f2f79; border-radius: 999px; padding: 4px 8px; font-size: 0.82em; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 100%; }
        .day-event-title:hover { background: rgba(78, 115, 223, 0.18); }
        .day-event-note { color: #6e707e; font-size: 0.8em; line-height: 1.2; margin-top: 4px; }
        .day-photos-selection { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; margin-top: 8px; }
        .photo-toggle { display: block; position: relative; border-radius: 8px; overflow: hidden; border: 1px solid rgba(78, 115, 223, 0.18); }
        .photo-toggle input { position: absolute; top: 6px; left: 6px; z-index: 2; width: 16px; height: 16px; accent-color: #4e73df; }
        .photo-toggle img { display: block; width: 100%; height: 60px; object-fit: cover; }
        .photo-toggle.checked { box-shadow: 0 0 0 2px rgba(78, 115, 223, 0.28); }
        .day-event-photos { margin-top: 8px; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 4px; }
        .day-event-photos img { width: 100%; height: 60px; object-fit: cover; border-radius: 6px; }
        .photo-limit-note { color: #6e707e; font-size: 0.75em; margin-top: 4px; }
        .calendar-note { color: #4e73df; font-size: 0.9em; margin-top: 6px; }
        
        /* 📸 相片牆網格樣式：用 repeat(auto-fit) 讓卡片寬度在 180px 到滿版之間自動調配 */
        .trip-photos { margin-top: 15px; border-top: 1px dashed #e3e6f0; padding-top: 12px; width: 100%; }
        .review-photos { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 12px; width: 100%; }
        .photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-top: 8px; width: 100%; }
        .photo-item { background: #f8f9fa; border: 1px solid #e3e6f0; padding: 8px; border-radius: 8px; display: flex; flex-direction: column; box-shadow: 0 2px 4px rgba(0,0,0,0.03); position: relative; }
        .photo-item img { width: 100%; height: 180px; object-fit: cover; display: block; border-radius: 6px; transition: transform 0.2s; }
        .photo-item img:hover { transform: scale(1.05); }
        .photo-grid-desc-text { font-size: 0.85em; color: #333; font-weight: bold; line-height: 1.3; margin-bottom: 8px; word-break: break-all; }
        
        /* 相片內部的微型控制鈕 */
        .photo-actions { display: flex; gap: 4px; margin-top: auto; border-top: 1px solid #eaecf4; padding-top: 6px; justify-content: flex-end; }
        .btn-photo-mini { font-size: 0.75em; padding: 3px 6px; border-radius: 4px; font-weight: normal; width: auto; }

        /* 控制按鈕區塊樣式 */
        .action-container { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; border-top: 1px solid #f1f3f9; padding-top: 10px; width: 100%; }
        .btn-danger { background-color: #e74a3b; width: auto; }
        .btn-danger:hover { background-color: #be2617; }
        .btn-success { background-color: #1cc88a; width: auto; }
        .btn-success:hover { background-color: #13855c; }
        .btn-group { display: flex; gap: 5px; width: auto; }

        /* 一頁式彈窗樣式 (Modal UI) */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
        .modal-content { background-color: white; padding: 25px; border-radius: 12px; width: 90%; max-width: 500px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .modal-header { font-size: 1.3em; font-weight: bold; color: #4e73df; margin-bottom: 15px; border-bottom: 1px solid #e3e6f0; padding-bottom: 10px; }
        .modal-buttons { display: flex; gap: 10px; justify-content: flex-end; margin-top: 15px; }
        .modal-buttons button { width: auto; }
        
        /* 橫向排列輸入框與清除鈕 */
        .time-input-container { display: flex; gap: 8px; align-items: center; width: 100%; }
        .time-input-container input { flex: 1; }
        .time-input-container button { width: auto; white-space: nowrap; }

        /* ⭕ 新增左側欄樣式：佔 35% 寬度，負責行程編輯與查詢，內部可獨立滾動 */
        .left-panel {
            width: 35%;
            height: 100%;
            padding: 24px;
            box-sizing: border-box;
            background-color: #ffffff;
            border-right: 2px solid #e3e6f0;
            overflow-y: auto; 
        }
        
        /* ⭕ 新增右側欄樣式：佔 65% 寬度，負責月度回顧區，預留給月曆與拍立得 */
        .right-panel {
            width: 65%;
            height: 100%;
            padding: 24px;
            box-sizing: border-box;
            background-color: #f8fafc; /* 微調為溫和的灰藍色背景，突顯回顧展質感 */
            overflow-y: auto;
        }

        /* ⭕ 強制修改與刪除按鈕：改為上下排列、置中、且文字絕不換行 */
        .trip-item button, 
        .left-panel button {
            display: flex;
            flex-direction: column;   /* 關鍵：讓圖標在上，文字在下 */
            align-items: center;      /* 水平置中 */
            justify-content: center;  /* 垂直置中 */
            padding: 6px 10px;        /* 給按鈕舒適的內邊距 */
            font-size: 0.85em;        /* 微調字體大小，更精緻 */
            white-space: nowrap;      /* 關鍵：強制文字絕對不換行！ */
            word-break: keep-all;     /* 配合 nowrap，防止中文字元被切斷 */
            min-width: 65px;          /* 設定一個足夠撐開四個字的最小寬度 */
            height: auto;             /* 高度隨內容自動撐開 */
        }

        /* 如果你的按鈕裡面有包圖標（例如 📝 或 🗑️），讓圖標與文字保有一點點間距 */
        .trip-item button i,
        .trip-item button span {
            margin-bottom: 2px;
        }

        /* ⭕ 確保按鈕列的 Flex 容器不會壓扁裡面的按鈕 */
        .btn-group, 
        .action-container { 
            display: flex; 
            gap: 8px;                 /* 按鈕之間的間距 */
            align-items: stretch;     /* 讓綠色和紅色按鈕高度對齐一致 */
            width: 100%; 
        }
    </style>
</head>
<body>
    <div class="container">
        
        <div class="left-panel">
            <h1>📅 TIMETRO 行事曆助手</h1>
            <div style="padding: 10px; margin-bottom: 12px; background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; border-radius: 6px;">
                目前頁面由 <strong>web_service.py</strong> 提供，請使用 <code>http://127.0.0.1:5001</code> 開啟。
            </div>
            
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
        
        <div class="right-panel">
            <h2>💖 當月行程與相片日記回顧</h2>
            
            <div class="search-box">
                <input type="month" id="reviewMonthInput" style="flex: 1;">
                <button type="button" id="reviewBtn" style="background-color: #1cc88a;">生成月度回顧展</button>
                <button type="button" id="downloadReviewBtn" style="background-color: #f6c23e; color: #000;" disabled>下載回顧</button>
                <select id="downloadFormatSelect" style="border-radius:6px; padding:0 8px; width:90px;">
                    <option value="png">PNG</option>
                    <option value="jpg">JPG</option>
                </select>
            </div>
            <div id="reviewList"></div>
        </div>

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
        let currentReviewMonth = '';
        const today = new Date();

        document.addEventListener('DOMContentLoaded', () => {
            const reviewMonthInput = document.getElementById('reviewMonthInput');
            const reviewBtn = document.getElementById('reviewBtn');
            const downloadReviewBtn = document.getElementById('downloadReviewBtn');
            const downloadFormatSelect = document.getElementById('downloadFormatSelect');
            const reviewList = document.getElementById('reviewList');

            console.log('web_service.py page loaded');
            console.log('review elements', {reviewMonthInput, reviewBtn, reviewList});
            if (!reviewMonthInput || !reviewBtn || !reviewList) {
                document.body.insertAdjacentHTML('afterbegin', '<div style="padding:12px;background:#d63384;color:#fff;font-weight:bold;">DEBUG: 這是 web_service.py 頁面，或 review 元素尚未載入。請確認是從 web_service.py 提供的 http://127.0.0.1:5001 進入。</div>');
            } else {
                reviewMonthInput.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
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
                                reviewList.innerHTML = `<div class="no-result">找不到該月份的任何行程紀錄。</div>`;
                                downloadReviewBtn.disabled = true;
                                currentReviewMonth = '';
                                return;
                            }

                            const tripsByDay = {};
                            data.forEach(trip => {
                                const day = parseInt(trip.date.split('-')[2], 10);
                                if (!tripsByDay[day]) tripsByDay[day] = [];
                                tripsByDay[day].push(trip);
                            });

                            const [year, month] = selectedMonth.split('-').map(num => parseInt(num, 10));
                            const firstDayOfMonth = new Date(year, month - 1, 1);
                            const totalDays = new Date(year, month, 0).getDate();
                            const startWeekday = firstDayOfMonth.getDay();
                            const weekdays = ['日', '一', '二', '三', '四', '五', '六'];

                            const calendarHTML = [];
                            calendarHTML.push('<div class="review-calendar">');
                            calendarHTML.push('<div class="calendar-weekdays">');
                            weekdays.forEach(dayName => calendarHTML.push(`<div>${dayName}</div>`));
                            calendarHTML.push('</div>');
                            calendarHTML.push('<div class="calendar-days">');

                            for (let blank = 0; blank < startWeekday; blank++) {
                                calendarHTML.push('<div class="calendar-day empty"></div>');
                            }

                            for (let day = 1; day <= totalDays; day++) {
                                const dayTrips = tripsByDay[day] || [];
                                calendarHTML.push('<div class="calendar-day">');
                                calendarHTML.push('<div class="day-row">');
                                calendarHTML.push(`<div class="day-number">${day}</div>`);
                                if (dayTrips.length > 0) {
                                    dayTrips.forEach(trip => {
                                        calendarHTML.push(`<div class="day-event-title">${trip.content}</div>`);
                                    });
                                }
                                calendarHTML.push('</div>');

                                if (dayTrips.length > 0) {
                                    const notes = dayTrips.filter(trip => trip.note).map(trip => `<div class="day-event-note">${trip.note}</div>`).join('');
                                    if (notes) {
                                        calendarHTML.push(notes);
                                    }

                                    const allPhotos = dayTrips.flatMap(trip => trip.photos || []);
                                    if (allPhotos.length > 0) {
                                        const photoSelectors = allPhotos.map((p, idx) => {
                                            const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                                            const src = /^https?:\/\//.test(pPath) || /^\/\//.test(pPath) || pPath.startsWith('data:')
                                                ? pPath
                                                : `${BASE_URL}/view-photo?path=${encodeURIComponent(pPath)}`;
                                            return `<label class="photo-toggle checked" data-day="${day}" data-photo-index="${idx}">` +
                                                `<input type="checkbox" checked data-day="${day}" data-photo-index="${idx}">` +
                                                `<img src="${src}" alt="回顧圖" onerror="this.style.display='none';">` +
                                                `</label>`;
                                        }).join('');
                                        const visiblePhotos = allPhotos.slice(0, 6).map((p, idx) => {
                                            const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                                            const src = /^https?:\/\//.test(pPath) || /^\/\//.test(pPath) || pPath.startsWith('data:')
                                                ? pPath
                                                : `${BASE_URL}/view-photo?path=${encodeURIComponent(pPath)}`;
                                            return `<img src="${src}" alt="回顧圖" data-day="${day}" data-photo-index="${idx}" onerror="this.style.display='none';">`;
                                        }).join('');
                                        calendarHTML.push(`<div class="day-photos-selection">${photoSelectors}</div>`);
                                        calendarHTML.push(`<div class="photo-limit-note">最多顯示 6 張圖片，取消勾選可隱藏。</div>`);
                                        calendarHTML.push(`<div class="day-event-photos" data-day="${day}">${visiblePhotos}</div>`);
                                    }
                                }
                                calendarHTML.push('</div>');
                            }

                            calendarHTML.push('</div>');
                            calendarHTML.push('</div>');
                            reviewList.innerHTML = calendarHTML.join('');
                            downloadReviewBtn.disabled = false;
                            currentReviewMonth = selectedMonth;
                        })
                        .catch(err => alert("讀取回顧失敗：" + err));
                });

                downloadReviewBtn.addEventListener('click', () => {
                    if (!currentReviewMonth || !reviewList.innerHTML.trim()) {
                        alert('請先生成月度回顧，再下載。');
                        return;
                    }
                    downloadReviewImage(downloadFormatSelect.value || 'png');
                });

                reviewList.addEventListener('change', (event) => {
                    const target = event.target;
                    if (!target.matches('input[data-day][data-photo-index]')) return;
                    const day = target.dataset.day;
                    updateDayPhotoGrid(day);
                });

                function updateDayPhotoGrid(day) {
                    const dayContainer = reviewList.querySelector(`.day-event-photos[data-day="${day}"]`);
                    if (!dayContainer) return;
                    const checkedInputs = Array.from(reviewList.querySelectorAll(`input[data-day="${day}"]:checked`));
                    const selectedPhotos = checkedInputs.slice(0, 6).map(input => {
                        const idx = parseInt(input.dataset.photoIndex, 10);
                        const label = input.closest('.photo-toggle');
                        return label ? label.querySelector('img') : null;
                    }).filter(Boolean);

                    dayContainer.innerHTML = selectedPhotos.map(img => `<img src="${img.src}" alt="回顧圖" onerror="this.style.display='none';">`).join('');
                    Array.from(reviewList.querySelectorAll(`.photo-toggle[data-day="${day}"]`)).forEach(label => {
                        const input = label.querySelector('input');
                        label.classList.toggle('checked', input.checked);
                    });
                }

                function downloadReviewImage(format) {
                    if (typeof html2canvas !== 'function') {
                        alert('無法載入 html2canvas，請確認網路連線或稍後再試。');
                        return;
                    }

                    const exportContainer = reviewList.cloneNode(true);
                    exportContainer.querySelectorAll('.day-photos-selection, .photo-limit-note').forEach(el => el.remove());

                    const wrapper = document.createElement('div');
                    wrapper.style.position = 'fixed';
                    wrapper.style.left = '-9999px';
                    wrapper.style.top = '-9999px';
                    wrapper.style.opacity = '0';
                    wrapper.appendChild(exportContainer);
                    document.body.appendChild(wrapper);

                    const originalDayCells = Array.from(reviewList.querySelectorAll('.calendar-day'));
                    if (originalDayCells.length > 0) {
                        let busiestIndex = 0;
                        let maxCount = -1;
                        originalDayCells.forEach((cell, idx) => {
                            const cnt = cell.querySelectorAll('.day-event-title, .day-event-note, .day-event-photos img').length;
                            if (cnt > maxCount) {
                                maxCount = cnt;
                                busiestIndex = idx;
                            }
                        });

                        const exportCells = Array.from(exportContainer.querySelectorAll('.calendar-day'));
                        const busiestExportCell = exportCells[busiestIndex] || exportCells[0];
                        const monthMaxHeight = Math.ceil(busiestExportCell.scrollHeight || busiestExportCell.getBoundingClientRect().height || 120);

                        exportCells.forEach(cell => {
                            cell.style.height = `${monthMaxHeight}px`;
                            cell.style.minHeight = 'auto';
                            cell.style.flex = '0 0 auto';
                            cell.style.overflow = 'visible';
                            cell.style.boxSizing = 'border-box';
                        });

                        const exportWeekdays = exportContainer.querySelector('.calendar-weekdays');
                        const exportDays = exportContainer.querySelector('.calendar-days');
                        if (exportWeekdays) exportWeekdays.style.gridTemplateColumns = 'repeat(7, 1fr)';
                        if (exportDays) exportDays.style.gridTemplateColumns = 'repeat(7, 1fr)';
                    }

                    const originalText = downloadReviewBtn.textContent;
                    downloadReviewBtn.disabled = true;
                    downloadReviewBtn.textContent = '準備中...';

                    html2canvas(exportContainer, { backgroundColor: '#f4f6f9', scale: 2 })
                        .then(canvas => {
                            const mime = format === 'jpg' ? 'image/jpeg' : 'image/png';
                            const dataUrl = canvas.toDataURL(mime, 0.95);
                            const link = document.createElement('a');
                            link.href = dataUrl;
                            link.download = `TIMETRO_${currentReviewMonth}_回顧.${format}`;
                            document.body.appendChild(link);
                            link.click();
                            document.body.removeChild(link);
                        })
                        .catch(err => alert('下載圖片失敗：' + err))
                        .finally(() => {
                            document.body.removeChild(wrapper);
                            downloadReviewBtn.disabled = false;
                            downloadReviewBtn.textContent = originalText;
                        });
                }
            }

            fetchTasks();
            startReminderClock();

            // ⭕ 自動生成當月回顧展
            console.log("🚀 系統初始化：自動調用當月月度回顧展");
            const autoReviewMonth = reviewMonthInput.value;
            if (autoReviewMonth) {
                // 延遲 500ms 確保 fetchTasks 已完成
                setTimeout(() => {
                    console.log(`📅 自動觸發回顧展：${autoReviewMonth}`);
                    reviewBtn.click();
                }, 500);
            }
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
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
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

if __name__ == '__main__':
    print("=====================================================")
    print("🌐 TIMETRO 自由清除提醒時間完全修復版啟動！")
    print("🔗 請開啟瀏覽器前往：http://127.0.0.1:5001")
    print("=====================================================")
    app.run(host='127.0.0.1', port=5001, debug=False)