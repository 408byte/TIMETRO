import storage
import os
from flask import Flask, jsonify, request, render_template_string, send_file
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app) 

# =====================================================
# 🌐 網頁 HTML 前端：行程概覽恆常顯示，僅回顧牆點擊後出現
# =====================================================
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>TIMETRO 行事曆助手 — 完全版</title>
    <style>
        /* 🌍 全域初始化 */
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

        .container { 
            display: flex;
            width: 100%; 
            height: 100vh;
            margin: 0;
            padding: 0;
            background: #fff;
        }

        h1, h2 { color: #4e73df; margin-top: 0; }
        
        /* 表單與輸入框樣式 */
        form { display: grid; gap: 10px; margin-bottom: 25px; background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #e3e6f0; width: 100%; }
        input, textarea, button { padding: 10px; border: 1px solid #d1d3e2; border-radius: 6px; font-size: 1em; width: 100%; }
        
        button { background-color: #4e73df; color: white; border: none; cursor: pointer; font-weight: bold; }
        button:hover { background-color: #2e59d9; }
        .search-box { display: flex; gap: 10px; margin-bottom: 20px; width: 100%; }
        #tripList { padding: 0; width: 100%; }
        
        /* 左側列表行程樣式 */
        .trip-item { background: #fff; border: 1px solid #e3e6f0; padding: 15px; margin-bottom: 12px; border-radius: 8px; list-style: none; box-shadow: 0 2px 4px rgba(0,0,0,0.02); width: 100%; }
        .trip-item-header { display: flex; justify-content: space-between; align-items: center; color: #4e73df; font-weight: bold; }
        .trip-item-content { font-weight: bold; font-size: 1.1em; margin-top: 8px; color: #2e2f37; }
        .trip-item-note { color: #6e707e; font-size: 0.9em; margin-top: 4px; }
        
        /* 左側相片牆小網格樣式 */
        .trip-photos { margin-top: 15px; border-top: 1px dashed #e3e6f0; padding-top: 12px; width: 100%; }
        .photo-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(130px, 1fr)); gap: 10px; margin-top: 8px; width: 100%; }
        .photo-item { background: #f8f9fa; border: 1px solid #e3e6f0; padding: 8px; border-radius: 8px; display: flex; flex-direction: column; position: relative; }
        .photo-item img { width: 100%; height: 100px; object-fit: cover; display: block; border-radius: 6px; }
        .photo-grid-desc-text { font-size: 0.82em; color: #555; font-weight: bold; margin-bottom: 6px; word-break: break-all; }
        .photo-actions { display: flex; gap: 4px; margin-top: auto; border-top: 1px solid #eaecf4; padding-top: 6px; justify-content: flex-end; }
        .btn-photo-mini { font-size: 0.75em; padding: 3px 6px; border-radius: 4px; width: auto; }

        /* 行程控制鈕底座 */
        .action-container { display: flex; justify-content: space-between; align-items: center; margin-top: 12px; border-top: 1px solid #f1f3f9; padding-top: 10px; width: 100%; gap: 12px; }
        .btn-danger { background-color: #e74a3b; width: auto; }
        .btn-danger:hover { background-color: #be2617; }
        .btn-success { background-color: #1cc88a; width: auto; }
        .btn-success:hover { background-color: #13855c; }
        .btn-group { display: flex; gap: 8px; align-items: center; width: auto; flex-shrink: 0; }

        /* =====================================================
           📅 行程概覽 (Calendar Overview) - 保持恆常顯示
           ==================================================== */
        .calendar-section {
            background: #ffffff;
            border: 1px solid #e3e6f0;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.01);
            width: 100%;
        }
        .calendar-grid {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 6px;
            margin-top: 10px;
        }
        .calendar-weekday {
            text-align: center;
            font-weight: bold;
            font-size: 0.85em;
            color: #4e73df;
            padding: 5px 0;
            border-bottom: 2px solid #eaecf4;
        }
        .calendar-day {
            min-height: 75px;
            background: #f8f9fa;
            border: 1px solid #e3e6f0;
            border-radius: 6px;
            padding: 4px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        .calendar-day.other-month { opacity: 0.35; background: #e9ecef; }
        .calendar-day.today { background: #fff3cd; border-color: #f6c23e; }
        .calendar-day-num { font-size: 0.82em; font-weight: bold; color: #6e707e; margin-bottom: 3px; }
        .calendar-day.today .calendar-day-num { color: #b7791f; }
        .calendar-day-events {
            display: flex;
            flex-direction: column;
            gap: 2px;
            overflow-y: auto;
            max-height: 52px;
        }
        .calendar-event-dot {
            font-size: 0.72em;
            background: #4e73df;
            color: white;
            padding: 1px 4px;
            border-radius: 3px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .calendar-event-dot.has-photo { background: #1cc88a; }

        /* =====================================================
           📸 回顧展照片牆區塊 (預設隱藏)
           ===================================================== */
        #reviewList { 
            width: 100%; 
            margin-top: 10px; 
            display: none; /* 💡 預設隱藏，點選按鈕後才顯示 */
        }
        
        /* 日期大標題 */
        .review-date-heading {
            font-size: 1.2em;
            font-weight: bold;
            color: #2e59d9;
            background: #eaecf4;
            padding: 8px 16px;
            border-radius: 8px;
            margin-top: 25px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-left: 5px solid #4e73df;
            width: 100%;
        }
        .review-date-heading:first-child { margin-top: 5px; }

        /* 寬度排版 */
        .gallery-grid-row { 
            display: grid; 
            grid-template-columns: repeat(3, 1fr); 
            gap: 15px; 
            width: 100%; 
            padding: 5px 0;
        }
        @media (max-width: 950px) {
            .gallery-grid-row { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 650px) {
            .gallery-grid-row { grid-template-columns: 1fr; }
        }

        /* 每一組照片與手帳的卡片盒 */
        .diary-card-combo {
            display: flex;
            flex-direction: column;
            background: #ffffff;
            border-radius: 12px;
            padding: 12px;
            border: 1px solid #e3e6f0;
            box-shadow: 0 3px 8px rgba(0,0,0,0.03);
            gap: 10px;
            width: 100%;
            align-items: center;
            justify-content: flex-start;
        }

        /* 拍立得卡片框 */
        .polaroid-card {
            background: #ffffff;
            padding: 10px 10px 32px 10px; 
            border-radius: 4px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04);
            width: 100%;
            max-width: 240px;
            position: relative;
            flex-shrink: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            border: 1px solid #eeeeee;
        }
        .polaroid-card img {
            width: 100%;
            height: auto;
            max-height: 200px;
            object-fit: contain;
            background-color: #fafafa;
            border: 1px solid rgba(0, 0, 0, 0.03);
            display: block;
        }
        .polaroid-footer-text {
            position: absolute;
            bottom: 6px;
            left: 0;
            width: 100%;
            text-align: center;
            font-family: 'Courier New', Courier, monospace, 'PMingLiU';
            font-weight: bold;
            font-size: 0.78em;
            color: #6e707e;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            padding: 0 6px;
        }

        /* 📝 撕線手帳日記框 */
        .notebook-caption-box {
            width: 100%;
            background-color: #fffdf8; 
            border: 1px solid #e5ddc8;
            border-radius: 6px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.02);
            position: relative;
            padding: 10px 10px 10px 26px; 
            min-height: 80px;
            display: flex;
            flex-direction: column;
            background-image: linear-gradient(#e5ddc8 1px, transparent 1px);
            background-size: 100% 22px;
            line-height: 22px;
        }
        .notebook-caption-box::before {
            content: "";
            position: absolute;
            left: 15px;
            top: 0;
            width: 1.5px;
            height: 100%;
            background-color: #ff9b9b; 
            opacity: 0.6;
        }
        .notebook-title {
            font-size: 0.9em;
            font-weight: bold;
            color: #333;
            margin-bottom: 2px;
            line-height: 22px;
            border-bottom: 1.5px solid #4e73df;
            display: inline-block;
            width: fit-content;
        }
        .notebook-desc-text {
            font-size: 0.85em;
            color: #4a4a4a;
            font-weight: 500;
            word-break: break-all;
            white-space: pre-wrap;
            margin-top: 2px;
            line-height: 22px;
        }

        /* 其他彈窗與佈局結構 */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
        .modal-content { background-color: white; padding: 25px; border-radius: 12px; width: 90%; max-width: 500px; box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .modal-header { font-size: 1.3em; font-weight: bold; color: #4e73df; margin-bottom: 15px; border-bottom: 1px solid #e3e6f0; padding-bottom: 10px; }
        .modal-buttons { display: flex; gap: 10px; justify-content: flex-end; margin-top: 15px; }
        .modal-buttons button { width: auto; }
        
        .time-input-container { display: flex; gap: 8px; align-items: center; width: 100%; }
        .time-input-container input { flex: 1; }
        .time-input-container button { width: auto; white-space: nowrap; }

        .left-panel { width: 35%; height: 100%; padding: 24px; box-sizing: border-box; background-color: #ffffff; border-right: 2px solid #e3e6f0; overflow-y: auto; }
        .right-panel { width: 65%; height: 100%; padding: 24px; box-sizing: border-box; background-color: #f8fafc; overflow-y: auto; }

        .trip-item button, .left-panel button { 
            display: inline-flex; 
            align-items: center; 
            justify-content: center; 
            padding: 8px 16px; 
            font-size: 0.9em; 
            white-space: nowrap; 
            word-break: keep-all; 
            width: auto; 
            height: auto; 
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="left-panel">
            <h1>📅 TIMETRO 行事曆助手</h1>
            <div style="padding: 10px; margin-bottom: 12px; background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; border-radius: 6px; font-size:0.9em;">
                目前頁面由 <strong>web_service.py</strong> 提供，請使用 <a href="http://127.0.0.1:5001" target="_blank">http://127.0.0.1:5001</a> 開啟。
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
                <button type="button" id="downloadReviewBtn" style="background-color: #f6c23e; color: #000;" disabled>下載回顧展</button>
                <select id="downloadFormatSelect" style="border-radius:6px; padding:0 8px; width:90px;">
                    <option value="png">PNG</option>
                    <option value="jpg">JPG</option>
                </select>
            </div>

            <div class="calendar-section">
                <h3 id="calendarTitle" style="margin: 0 0 10px 0; color: #4e73df; font-size: 1.1em;">📊 行程概覽</h3>
                <div class="calendar-grid" id="calendarGrid"></div>
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
                
                <label style="font-weight: bold; font-size: 0.9em; color: #5a5c69;">⏰ 設置提醒時間</label>
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

        function getPhotoUrl(path) {
            if (/^https?:\/\//i.test(path) || /^\/\//.test(path) || path.startsWith('data:')) {
                return path;
            }
            return `${BASE_URL}/view-photo?path=${encodeURIComponent(path)}`;
        }

        document.addEventListener('DOMContentLoaded', () => {
            const reviewMonthInput = document.getElementById('reviewMonthInput');
            const reviewBtn = document.getElementById('reviewBtn');
            const downloadReviewBtn = document.getElementById('downloadReviewBtn');
            const reviewList = document.getElementById('reviewList');

            if (reviewMonthInput) {
                // 預設填入當前月份
                reviewMonthInput.value = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
                
                // 💡 當使用者切換月份選單時：
                reviewMonthInput.addEventListener('change', () => {
                    const selectedMonth = reviewMonthInput.value;
                    if (selectedMonth) {
                        // 1. 始終立刻渲染上方的「行程概覽」日曆格子
                        updateCalendarViewOnly(selectedMonth);
                    }
                    // 2. 只有下方的拍立得照片與日記方塊要隱藏起來
                    reviewList.style.display = 'none';
                    downloadReviewBtn.disabled = true;
                });

                // 💡 點擊「生成月度回顧展」按鈕
                reviewBtn.addEventListener('click', () => {
                    const selectedMonth = reviewMonthInput.value;
                    if (!selectedMonth) {
                        alert("請選擇月份！");
                        return;
                    }

                    fetch(`${BASE_URL}/monthly-review?month=${selectedMonth}`)
                        .then(res => res.json())
                        .then(data => {
                            // 同步確保最上方的行程概覽格子也是最新狀態
                            renderCalendarGrid(selectedMonth, data);

                            reviewList.innerHTML = "";
                            
                            // 篩選有照片的行程
                            const photoTrips = data.filter(trip => trip.photos && trip.photos.length > 0);
                            if (photoTrips.length === 0) {
                                reviewList.innerHTML = `<div style="text-align:center; padding:30px; color:#858796;">📸 該月行程中尚未新增任何相片解說日記喔！</div>`;
                                reviewList.style.display = 'block'; 
                                downloadReviewBtn.disabled = true;
                                currentReviewMonth = '';
                                return;
                            }

                            // 按日期分組
                            const groupedByDate = {};
                            photoTrips.forEach(trip => {
                                const d = trip.date;
                                if (!groupedByDate[d]) {
                                    groupedByDate[d] = [];
                                }
                                groupedByDate[d].push(trip);
                            });

                            const sortedDates = Object.keys(groupedByDate).sort();
                            const galleryHTML = [];
                            galleryHTML.push('<div id="captureContainer" style="padding:5px;">');

                            sortedDates.forEach(dateStr => {
                                galleryHTML.push(`<div class="review-date-heading">📅 ${dateStr}</div>`);
                                galleryHTML.push('<div class="gallery-grid-row">');

                                const tripsOnDate = groupedByDate[dateStr];
                                tripsOnDate.forEach(trip => {
                                    const timeDisplay = trip.time ? ` ⏰ ${trip.time}` : '';
                                    const footerTimeText = `${trip.date}${timeDisplay}`;

                                    trip.photos.forEach((p, idx) => {
                                        const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                                        const src = getPhotoUrl(pPath);
                                        
                                        let pDesc = "";
                                        if (trip.photo_notes && trip.photo_notes[idx]) {
                                            pDesc = trip.photo_notes[idx].trim();
                                        } else if (typeof p === 'object' && p !== null && p.desc) {
                                            pDesc = p.desc.trim();
                                        }

                                        galleryHTML.push('<div class="diary-card-combo">');
                                        
                                        galleryHTML.push('<div class="polaroid-card">');
                                        galleryHTML.push(`<img src="${src}" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=320'; this.style.opacity='0.4';">`);
                                        galleryHTML.push(`<div class="polaroid-footer-text">${footerTimeText}</div>`);
                                        galleryHTML.push('</div>');

                                        if (pDesc && pDesc !== "無解說" && pDesc !== "") {
                                            galleryHTML.push('<div class="notebook-caption-box">');
                                            galleryHTML.push(`<div class="notebook-title">✨ ${trip.content}</div>`);
                                            galleryHTML.push(`<div class="notebook-desc-text">${pDesc}</div>`);
                                            galleryHTML.push('</div>');
                                        }
                                        
                                        galleryHTML.push('</div>');
                                    });
                                });

                                galleryHTML.push('</div>'); 
                            });

                            galleryHTML.push('</div>'); 
                            reviewList.innerHTML = galleryHTML.join('');
                            
                            // 顯示照片展覽牆
                            reviewList.style.display = 'block'; 
                            downloadReviewBtn.disabled = false;
                            currentReviewMonth = selectedMonth;
                        })
                        .catch(err => alert("讀取回顧失敗：" + err));
                });

                downloadReviewBtn.addEventListener('click', () => {
                    if (!currentReviewMonth || !reviewList.innerHTML.trim()) {
                        alert('請先生成月度回顧展，再下載。');
                        return;
                    }
                    downloadReviewImage(downloadFormatSelect.value || 'png');
                });
            }

            // 初始同步載入
            fetchTasks();
            startReminderClock();
        });

        // 💡 專門用來單獨重新載入並渲染行程概覽格子的獨立函數
        function updateCalendarViewOnly(yearMonthStr) {
            fetch(`${BASE_URL}/monthly-review?month=${yearMonthStr}`)
                .then(res => res.json())
                .then(mdata => {
                    renderCalendarGrid(yearMonthStr, mdata);
                })
                .catch(err => console.error("日曆渲染失敗:", err));
        }

        function renderCalendarGrid(yearMonthStr, monthTasks) {
            const grid = document.getElementById('calendarGrid');
            const title = document.getElementById('calendarTitle');
            if (!grid) return;

            grid.innerHTML = "";
            const [year, month] = yearMonthStr.split('-').map(Number);
            title.textContent = `📊 行程概覽 (${year}年 ${month}月)`;

            const weekdays = ['日', '一', '二', '三', '四', '五', '六'];
            weekdays.forEach(w => {
                const div = document.createElement('div');
                div.className = 'calendar-weekday';
                div.textContent = w;
                grid.appendChild(div);
            });

            const firstDayIdx = new Date(year, month - 1, 1).getDay();
            const totalDays = new Date(year, month, 0).getDate();
            const prevMonthTotalDays = new Date(year, month - 1, 0).getDate();

            for (let i = firstDayIdx - 1; i >= 0; i--) {
                const dayNum = prevMonthTotalDays - i;
                const dayDiv = document.createElement('div');
                dayDiv.className = 'calendar-day other-month';
                dayDiv.innerHTML = `<div class="calendar-day-num">${dayNum}</div>`;
                grid.appendChild(dayDiv);
            }

            for (let d = 1; d <= totalDays; d++) {
                const currentLoopDateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
                const dayDiv = document.createElement('div');
                dayDiv.className = 'calendar-day';
                
                if (today.getFullYear() === year && (today.getMonth() + 1) === month && today.getDate() === d) {
                    dayDiv.classList.add('today');
                }

                dayDiv.innerHTML = `<div class="calendar-day-num">${d}</div><div class="calendar-day-events" id="cal-events-${currentLoopDateStr}"></div>`;
                grid.appendChild(dayDiv);

                const dayEventsContainer = dayDiv.querySelector('.calendar-day-events');
                const dayTasks = monthTasks.filter(t => t.date === currentLoopDateStr);
                dayTasks.forEach(t => {
                    const dot = document.createElement('div');
                    dot.className = 'calendar-event-dot';
                    if (t.photos && t.photos.length > 0) {
                        dot.classList.add('has-photo');
                    }
                    const tStr = t.time ? `[${t.time}] ` : '';
                    dot.textContent = `${tStr}${t.content}`;
                    dot.title = t.content;
                    dayEventsContainer.appendChild(dot);
                });
            }
        }

        function downloadReviewImage(format) {
            if (typeof html2canvas !== 'function') {
                const script = document.createElement('script');
                script.src = 'https://html2canvas.hertzen.com/dist/html2canvas.min.js';
                script.onload = () => downloadReviewImage(format);
                document.head.appendChild(script);
                return;
            }

            const targetElement = document.getElementById('captureContainer') || reviewList;
            const originalText = downloadReviewBtn.textContent;
            downloadReviewBtn.disabled = true;
            downloadReviewBtn.textContent = '圖片繪製中...';

            html2canvas(targetElement, { 
                backgroundColor: '#f8fafc', 
                scale: 2,
                useCORS: true 
            })
            .then(canvas => {
                const mime = format === 'jpg' ? 'image/jpeg' : 'image/png';
                const dataUrl = canvas.toDataURL(mime, 0.95);
                const link = document.createElement('a');
                link.href = dataUrl;
                link.download = `TIMETRO_${currentReviewMonth}_精美相片日記牆.${format}`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            })
            .catch(err => alert('下載回顧圖片失敗：' + err))
            .finally(() => {
                downloadReviewBtn.disabled = false;
                downloadReviewBtn.textContent = originalText;
            });
        }

        function fetchTasks() {
            fetch(`${BASE_URL}/tasks`)
                .then(res => res.json())
                .then(data => { 
                    allTasks = data; 
                    displayTrips(); 
                    
                    // 初始化讀取網頁時，立刻渲染預設月份的「行程概覽」日曆格子
                    const rmInput = document.getElementById('reviewMonthInput');
                    if (rmInput && rmInput.value) {
                        updateCalendarViewOnly(rmInput.value);
                    }
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
                
                // 行程異動後，自動刷新日曆概覽格子
                const rmInput = document.getElementById('reviewMonthInput');
                if (rmInput && rmInput.value) { updateCalendarViewOnly(rmInput.value); }

                const rList = document.getElementById('reviewList');
                if (rList && rList.style.display === 'block') {
                    document.getElementById('reviewBtn').click();
                }
            });
        });

        function addPhotoToTaskDirectly(taskString) {
            const targetTrip = JSON.parse(decodeURIComponent(taskString));
            if (targetTrip.photos && targetTrip.photos.length >= 10) {
                alert(`❌ 無法新增！【${targetTrip.content}】相片已達 10 筆上限！`);
                return;
            }
            const photoPath = prompt(`📸 請輸入為【${targetTrip.content}】新增的照片路徑：\n(例如：C:\\images\\pic.jpg 或 網址)`);
            if (!photoPath || photoPath.trim() === "") return;
            const photoDesc = prompt("💬 請輸入文字解說（若留空或填無解說，回顧展將不顯示日記方框）：", "");
            
            fetch(`${BASE_URL}/web-photo`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: targetTrip.date,
                    time: targetTrip.time,
                    content: targetTrip.content,
                    path: photoPath.trim(),
                    desc: photoDesc ? photoDesc.trim() : ""
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    alert("📸 照片與解說已成功紀錄！");
                    fetchTasks();
                    
                    const rmInput = document.getElementById('reviewMonthInput');
                    if (rmInput && rmInput.value) { updateCalendarViewOnly(rmInput.value); }

                    const rList = document.getElementById('reviewList');
                    if (rList && rList.style.display === 'block') {
                        document.getElementById('reviewBtn').click();
                    }
                } else { alert("❌ 錯誤：" + data.message); }
            })
            .catch(err => alert("❌ 連線錯誤：" + err));
        }

        function deleteTrip(taskString) {
            const targetTrip = JSON.parse(decodeURIComponent(taskString));
            if (confirm(`⚠️ 確定要刪除行程【${targetTrip.content}】嗎？`)) {
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
                        
                        const rmInput = document.getElementById('reviewMonthInput');
                        if (rmInput && rmInput.value) { updateCalendarViewOnly(rmInput.value); }

                        const rList = document.getElementById('reviewList');
                        if (rList && rList.style.display === 'block') {
                            document.getElementById('reviewBtn').click();
                        }
                    } else { alert("❌ 刪除失敗：" + data.message); }
                });
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

        function closeEditModal() { editModal.style.display = 'none'; }

        editTripForm.addEventListener('submit', function(event) {
            event.preventDefault();
            fetch(`${BASE_URL}/web-edit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    old_date: document.getElementById('editOldDate').value,
                    old_time: document.getElementById('editOldTime').value,
                    old_content: document.getElementById('editOldContent').value,
                    new_date: document.getElementById('editDate').value.trim(),
                    new_time: document.getElementById('editTime').value.trim(),
                    new_content: document.getElementById('editContent').value.trim(),
                    new_note: document.getElementById('editNote').value.trim()
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === "success") {
                    alert("📝 行程內容已成功更新！");
                    closeEditModal();
                    fetchTasks();
                    
                    const rmInput = document.getElementById('reviewMonthInput');
                    if (rmInput && rmInput.value) { updateCalendarViewOnly(rmInput.value); }

                    const rList = document.getElementById('reviewList');
                    if (rList && rList.style.display === 'block') {
                        document.getElementById('reviewBtn').click();
                    }
                }
            });
        });

        function openPhotoEditModalDirectly(taskStr, index, path, desc) {
            document.getElementById('photoTripString').value = taskStr;
            document.getElementById('photoIndex').value = index;
            document.getElementById('photoEditPath').value = path;
            document.getElementById('photoEditDesc').value = desc === "無解說" ? "" : desc;
            photoEditModal.style.display = 'flex';
        }

        function closePhotoEditModal() { photoEditModal.style.display = 'none'; }

        photoEditForm.addEventListener('submit', function(e) {
            e.preventDefault();
            fetch(`${BASE_URL}/web-photo-update`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: document.getElementById('photoTripString').value ? JSON.parse(decodeURIComponent(document.getElementById('photoTripString').value)).date : '',
                    time: JSON.parse(decodeURIComponent(document.getElementById('photoTripString').value)).time,
                    content: JSON.parse(decodeURIComponent(document.getElementById('photoTripString').value)).content,
                    photo_index: parseInt(document.getElementById('photoIndex').value),
                    new_path: document.getElementById('photoEditPath').value.trim(),
                    new_desc: document.getElementById('photoEditDesc').value.trim()
                })
            })
            .then(res => res.json())
            .then(data => {
                if(data.status === "success") {
                    alert("🖼️ 相片與解說已成功更新！");
                    closePhotoEditModal();
                    fetchTasks();
                    
                    const rmInput = document.getElementById('reviewMonthInput');
                    if (rmInput && rmInput.value) { updateCalendarViewOnly(rmInput.value); }

                    const rList = document.getElementById('reviewList');
                    if (rList && rList.style.display === 'block') {
                        document.getElementById('reviewBtn').click();
                    }
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
                        
                        const rmInput = document.getElementById('reviewMonthInput');
                        if (rmInput && rmInput.value) { updateCalendarViewOnly(rmInput.value); }

                        const rList = document.getElementById('reviewList');
                        if (rList && rList.style.display === 'block') {
                            document.getElementById('reviewBtn').click();
                        }
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
                    if (!task.time || task.time.trim() === "") return;
                    if (`${task.date} ${task.time}` <= current && !task.reminded) {
                        task.reminded = true;
                        alert(`🔔 【TIMETRO 提醒通知】\n行程：${task.content}\n時間到了！`);
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
                tripList.innerHTML = `<li style="text-align:center; padding:20px; color:#858796; list-style:none;">沒有找到任何行程記錄 📭</li>`;
                return;
            }
            sortedTrips.forEach((trip) => {
                const li = document.createElement('li');
                li.className = 'trip-item';
                
                let timeStr = trip.time ? `⏰ ${trip.time}` : '🔔 不設定提醒';
                let noteStr = trip.note ? `<div class="trip-item-note">💡 ${trip.note}</div>` : '';
                
                const serializedTrip = encodeURIComponent(JSON.stringify(trip));
                
                let photosHTML = "";
                if (trip.photos && trip.photos.length > 0) {
                    photosHTML += `<div class="trip-photos"><h5 style="margin:0 0 5px 0; color:#4e73df;">🖼️ 精選相片日記</h5><div class="photo-grid">`;
                    trip.photos.forEach((p, pIdx) => {
                        const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                        let pDesc = (trip.photo_notes && trip.photo_notes[pIdx]) ? trip.photo_notes[pIdx] : "無解說";
                        const imgSrc = getPhotoUrl(pPath);
                        const safePath = pPath.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
                        const safeDesc = pDesc.replace(/'/g, "\\'");

                        photosHTML += `
                            <div class="photo-item">
                                <div class="photo-grid-desc-text">💬 <span>${pDesc}</span></div>
                                <img src="${imgSrc}" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200'; this.style.opacity='0.5';">
                                <div class="photo-actions">
                                    <button type="button" class="btn-success btn-photo-mini" onclick="openPhotoEditModalDirectly('${serializedTrip}', ${pIdx}, '${safePath}', '${safeDesc}')">✏️ 更改</button>
                                    <button type="button" class="btn-danger btn-photo-mini" onclick="fireDeleteSinglePhoto('${serializedTrip}', ${pIdx})">🗑️</button>
                                </div>
                            </div>`;
                    });
                    photosHTML += `</div></div>`;
                }

                li.innerHTML = `
                    <div class="trip-item-header">
                        <span>📅 ${trip.date} &nbsp;&nbsp; ${timeStr}</span>
                    </div>
                    <div class="trip-item-content">${trip.content}</div>
                    ${noteStr}
                    ${photosHTML}
                    <div class="action-container">
                        <button class="btn-success" onclick="addPhotoToTaskDirectly('${serializedTrip}')">📸 新增相片解說</button>
                        <div class="btn-group">
                            <button class="btn-success" onclick="editTrip('${serializedTrip}')">📝 修改</button>
                            <button class="btn-danger" onclick="deleteTrip('${serializedTrip}')">🗑️ 刪除</button>
                        </div>
                    </div>
                `;
                tripList.appendChild(li);
            });
        }

        if (searchBtn) {
            searchBtn.addEventListener('click', displayTrips);
            clearBtn.addEventListener('click', () => { searchInput.value = ""; displayTrips(); });
            searchInput.addEventListener('keyup', (e) => { if (e.key === 'Enter') displayTrips(); });
        }
    </script>
</body>
</html>
"""

# =====================================================
# 🐍 Flask 後端核心路由
# =====================================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tasks', methods=['GET', 'POST'])
def handle_tasks():
    if request.method == 'POST':
        data = request.json or {}
        tasks = storage.load_data()
        tasks.append({
            "date": data.get("date"),
            "time": data.get("time", ""),
            "content": data.get("content"),
            "note": data.get("note", ""),
            "reminded": False,
            "photos": [],
            "photo_notes": []
        })
        storage.save_data(tasks)
        return jsonify({"status": "success"}), 200
    else:
        return jsonify(storage.load_data()), 200

@app.route('/api/web-delete', methods=['POST'])
def web_delete():
    data = request.json or {}
    tasks = storage.load_data()
    updated = [t for t in tasks if not (t.get("date") == data.get("date") and t.get("time") == data.get("time") and t.get("content") == data.get("content"))]
    storage.save_data(updated)
    return jsonify({"status": "success"}), 200

@app.route('/api/web-edit', methods=['POST'])
def web_edit():
    data = request.json or {}
    tasks = storage.load_data()
    for t in tasks:
        if t.get("date") == data.get("old_date") and t.get("time") == data.get("old_time") and t.get("content") == data.get("old_content"):
            t["date"] = data.get("new_date")
            t["time"] = data.get("new_time", "")
            t["content"] = data.get("new_content")
            t["note"] = data.get("new_note", "")
            break
    storage.save_data(tasks)
    return jsonify({"status": "success"}), 200

@app.route('/api/web-photo', methods=['POST'])
def web_photo():
    data = request.json or {}
    tasks = storage.load_data()
    for t in tasks:
        if t.get("date") == data.get("date") and t.get("time") == data.get("time") and t.get("content") == data.get("content"):
            if "photos" not in t: t["photos"] = []
            if "photo_notes" not in t: t["photo_notes"] = []
            
            raw_path = data.get("path", "").strip()
            clean_path = raw_path.replace('/', '\\')
            
            t["photos"].append(clean_path)
            desc = data.get("desc", "").strip()
            t["photo_notes"].append(desc if desc != "" else "無解說")
            break
    storage.save_data(tasks)
    return jsonify({"status": "success"}), 200

@app.route('/api/web-photo-update', methods=['POST'])
def web_photo_update():
    data = request.json or {}
    tasks = storage.load_data()
    idx = data.get("photo_index")
    for t in tasks:
        if t.get("date") == data.get("date") and t.get("time") == data.get("time") and t.get("content") == data.get("content"):
            if "photos" in t and idx < len(t["photos"]):
                raw_path = data.get("new_path", "").strip()
                t["photos"][idx] = raw_path.replace('/', '\\')
            
            if "photo_notes" not in t: t["photo_notes"] = ["無解說"] * len(t["photos"])
            while len(t["photo_notes"]) < len(t["photos"]): t["photo_notes"].append("無解說")
                
            desc = data.get("new_desc", "").strip()
            t["photo_notes"][idx] = desc if desc != "" else "無解說"
            break
    storage.save_data(tasks)
    return jsonify({"status": "success"}), 200

@app.route('/api/web-photo-delete', methods=['POST'])
def web_photo_delete():
    data = request.json or {}
    tasks = storage.load_data()
    idx = data.get("photo_index")
    for t in tasks:
        if t.get("date") == data.get("date") and t.get("time") == data.get("time") and t.get("content") == data.get("content"):
            if "photos" in t and idx < len(t["photos"]): t["photos"].pop(idx)
            if "photo_notes" in t and idx < len(t["photo_notes"]): t["photo_notes"].pop(idx)
            break
    storage.save_data(tasks)
    return jsonify({"status": "success"}), 200

@app.route('/api/view-photo', methods=['GET'])
def view_photo():
    photo_path = request.args.get('path', '')
    photo_path = photo_path.strip('"').strip("'")
    if os.path.exists(photo_path):
        return send_file(photo_path)
    return jsonify({"error": "File not found"}), 404

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
    except Exception: 
        return jsonify({"status": "success"}), 200

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
    app.run(host='127.0.0.1', port=5001, debug=True)