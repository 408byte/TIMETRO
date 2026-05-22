import storage
import os
from flask import Flask, jsonify, request, render_template_string, send_file
from flask_cors import CORS
import logging

app = Flask(__name__)
CORS(app) 

# =====================================================
# 🌐 網頁 HTML 前端：修正按鈕擠壓與相片顯示路徑問題
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
        
        /* 📸 相片牆網格樣式 */
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

        /* 🛠️ 修正：控制按鈕底座，允許內容自然排開 */
        .action-container { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-top: 12px; 
            border-top: 1px solid #f1f3f9; 
            padding-top: 10px; 
            width: 100%; 
            gap: 12px;
        }
        .btn-danger { background-color: #e74a3b; width: auto; }
        .btn-danger:hover { background-color: #be2617; }
        .btn-success { background-color: #1cc88a; width: auto; }
        .btn-success:hover { background-color: #13855c; }
        
        /* 🛠️ 修正：讓按鈕群組寬度自動，不壓縮彼此 */
        .btn-group { 
            display: flex; 
            gap: 8px; 
            align-items: center; 
            width: auto; 
            flex-shrink: 0;
        }

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

        /* ⭕ 新增左側欄樣式 */
        .left-panel { width: 35%; height: 100%; padding: 24px; box-sizing: border-box; background-color: #ffffff; border-right: 2px solid #e3e6f0; overflow-y: auto; }
        
        /* ⭕ 新增右側欄樣式 */
        .right-panel { width: 65%; height: 100%; padding: 24px; box-sizing: border-box; background-color: #f8fafc; overflow-y: auto; }

        /* 🛠️ 修正：讓所有功能按鈕字體舒服展開，拒絕擠壓換行，留白充裕 */
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
            <div style="padding: 10px; margin-bottom: 12px; background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; border-radius: 6px;">
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

        // 🔧 內部輔助：處理相片 URL 的特殊反斜線，防止傳輸損壞
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
                                            const src = getPhotoUrl(pPath);
                                            return `<label class="photo-toggle checked" data-day="${day}" data-photo-index="${idx}">` +
                                                `<input type="checkbox" checked data-day="${day}" data-photo-index="${idx}">` +
                                                `<img src="${src}" alt="回顧圖" onerror="this.style.display='none';">` +
                                                `</label>`;
                                        }).join('');
                                        const visiblePhotos = allPhotos.slice(0, 6).map((p, idx) => {
                                            const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                                            const src = getPhotoUrl(pPath);
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
            }

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

            fetchTasks();
            startReminderClock();

            const autoReviewMonth = reviewMonthInput ? reviewMonthInput.value : '';
            if (autoReviewMonth && reviewBtn) {
                setTimeout(() => {
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
            const photoPath = prompt(`📸 請輸入要為【${targetTrip.content}】新增的照片檔案路徑：\n(例如：C:\\images\\pic.jpg 或 圖片網址)`);
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

        function closeEditModal() { editModal.style.display = 'none'; }

        editTripForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const inputDate = document.getElementById('editDate').value.trim();
            const inputTime = document.getElementById('editTime').value.trim();
            const inputContent = document.getElementById('editContent').value.trim();
            const inputNote = document.getElementById('editNote').value.trim();
            const datePattern = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;
            if (!datePattern.test(inputDate)) {
                alert("❌ 日期格式錯誤！\n請務必符合 YYYY-MM-DD 格式（例如：2026-05-20）");
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
                    new_time: inputTime,
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

        function closePhotoEditModal() { photoEditModal.style.display = 'none'; }

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
                        const rmInput = document.getElementById('reviewMonthInput');
                        const rBtn = document.getElementById('reviewBtn');
                        if (rmInput && rBtn && rmInput.value) { rBtn.click(); }
                    } else {
                        alert("❌ 移除失敗：" + data.message);
                    }
                })
                .catch(err => alert("❌ 連線錯誤：" + err));
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
                tripList.innerHTML = `<li class="no-result">沒有找到任何行程記錄 📭</li>`;
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
                    photosHTML += `<div class="trip-photos"><h5>🖼️ 精選相片日記</h5><div class="photo-grid">`;
                    trip.photos.forEach((p, pIdx) => {
                        const pPath = (typeof p === 'object' && p !== null) ? p.path : p;
                        
                        let pDesc = "無解說";
                        if (trip.photo_notes && trip.photo_notes[pIdx]) {
                            pDesc = trip.photo_notes[pIdx];
                        } else if (typeof p === 'object' && p !== null && p.desc) {
                            pDesc = p.desc;
                        }

                        const imgSrc = getPhotoUrl(pPath);

                        // 轉義單引號防止 JS 傳參崩潰
                        const safePath = pPath.replace(/\\/g, "\\\\").replace(/'/g, "\\'");
                        const safeDesc = pDesc.replace(/'/g, "\\'");

                        photosHTML += `
                            <div class="photo-item" data-photo-idx="${pIdx}">
                                <div class="photo-grid-desc-text">💬 <span class="txt-span">${pDesc}</span></div>
                                <img src="${imgSrc}" onerror="this.src='https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=200'; this.style.opacity='0.5';">
                                <div class="photo-actions">
                                    <button type="button" class="btn-success btn-photo-mini inner-edit-btn" onclick="openPhotoEditModalDirectly('${serializedTrip}', ${pIdx}, '${safePath}', '${safeDesc}')">✏️ 更改</button>
                                    <button type="button" class="btn-danger btn-photo-mini inner-del-btn" onclick="fireDeleteSinglePhoto('${serializedTrip}', ${pIdx})">🗑️</button>
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
# 🐍 Flask 後端核心路由與相片路徑傳輸安全修正
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
            # 🔧 修正：統一將雙反斜線或單反斜線轉回標準 Windows 檔案路徑
            clean_path = raw_path.replace('/', '\\')
            
            t["photos"].append(clean_path)
            desc = data.get("desc", "無解說")
            t["photo_notes"].append(desc if desc.strip() != "" else "無解說")
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
            while len(t["photo_notes"]) < len(t["photos"]):
                t["photo_notes"].append("無解說")
                
            if idx < len(t["photo_notes"]):
                t["photo_notes"][idx] = data.get("new_desc", "無解說")
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
            if "photos" in t and idx < len(t["photos"]):
                t["photos"].pop(idx)
            if "photo_notes" in t and idx < len(t["photo_notes"]):
                t["photo_notes"].pop(idx)
            
            if not t.get("photos") or len(t["photos"]) == 0:
                t["photos"] = []
                t["photo_notes"] = []
            break
    storage.save_data(tasks)
    return jsonify({"status": "success"}), 200

@app.route('/api/view-photo', methods=['GET'])
def view_photo():
    photo_path = request.args.get('path', '')
    # 🔧 修正：解碼並移除 Windows 可能在 URL 傳輸中被加上的前後引號
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
    app.run(host='127.0.0.1', port=5001, debug=True)