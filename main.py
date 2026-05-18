import task_manager
import storage
from datetime import datetime
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

# 初始化 Flask App
app = Flask(__name__)
CORS(app)  # 允許網頁前端跨網域連線

# 1. 初始化：載入舊有資料（讓終端機與 Flask 共享同一個 tasks 陣列）
tasks = storage.load_data()

# ==================== 🌐 區塊 A：Flask API 伺服器 (給網頁前端用) ====================

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """ 讓前端網頁獲取所有行程 """
    return jsonify(tasks)

@app.route('/api/tasks', methods=['POST'])
def add_task():
    """ 讓前端網頁新增行程 """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "沒有收到資料"}), 400
            
        # 🌟 嚴格對齊你終端機建立行程時的所有欄位名稱
        new_task = {
            "date": data.get("date"),
            "time": data.get("time"),
            "content": data.get("content"),
            "note": data.get("note", ""),
            "photo": "",          # 預留功能 3 的相片路徑欄位
            "reminded": False     # 給終端機/前端提醒用的標籤
        }
        
        tasks.append(new_task)
        storage.save_data(tasks)  # 立刻寫入 json 檔案
        
        print(f"\n🌐 [網頁同步] 成功新增行程: {new_task['content']}") 
        return jsonify({"message": "前端新增成功！", "task": new_task}), 201
        
    except Exception as e:
        print(f"\n❌ 前端新增行程時出錯: {str(e)}")
        return jsonify({"error": str(e)}), 500

def run_flask_server():
    """ 啟動 Flask 伺服器 (關閉 debug 模式以防與主執行緒衝突) """
    app.run(port=5000, debug=False, use_reloader=False)


# ==================== 💻 區塊 B：原本的終端機功能與主程式 ====================

def main():
    print("=== 歡迎使用 TIMETRO 行事曆助手 ===")
    print("(💡 提示：網頁前端 API 伺服器已在背景同步啟動)")

    # 🚀 在背景啟動 Flask，程式才不會被 Flask 阻擋而無法操作選單
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()

    while True:
        # 每次迴圈開始，自動檢查一次提醒 (你原本的 MVP 提醒)
        check_reminders_simple(tasks)

        print("\n--- 功能選單 ---")
        print("1. 新增行程與提醒")
        print("2. 查看所有行程與相片")
        print("3. 為行程新增照片路徑")
        print("4. 刪除行程")
        print("q. 儲存並離開")

        choice = input("請選擇功能: ").strip().lower()

        if choice == '1':
            new_task = task_manager.create_task_input()
            # 確保欄位完整
            if 'reminded' not in new_task:
                new_task['reminded'] = False
            if 'photo' not in new_task:
                new_task['photo'] = ""
                
            tasks.append(new_task)
            storage.save_data(tasks)  # 新增完立刻存檔，網頁端才看得到
            print("行程已新增！")

        elif choice == '2':
            task_manager.display_tasks(tasks)

        elif choice == '3':
            task_manager.display_tasks(tasks)
            try:
                index = int(input("請輸入要編輯的行程編號: "))
                photo_path = input("請輸入照片檔案路徑: ")
                task_manager.add_photo_to_task(tasks, index, photo_path)
                storage.save_data(tasks)
            except (ValueError, IndexError):
                print("輸入錯誤，請重新操作。")

        elif choice == '4':
            task_manager.display_tasks(tasks)
            try:
                index = int(input("請輸入要刪除的行程編號: "))
                tasks.pop(index)
                storage.save_data(tasks)
                print("刪除成功！")
            except (ValueError, IndexError):
                print("輸入錯誤，請重新操作。")

        elif choice == 'q':
            storage.save_data(tasks)
            print("資料已儲存，下次見！")
            break
        else:
            print("無效輸入，請重新選擇。")

def check_reminders_simple(tasks):
    """ MVP 提醒功能 """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for t in tasks:
        task_time = f"{t.get('date', '')} {t.get('time', '')}"
        if now >= task_time and not t.get('reminded'):
            print(f"\n🔔 【提醒通知】現在是 {now}，行程：{t.get('content', '未命名')} 該開始囉！")
            t['reminded'] = True  # 標記為已提醒

if __name__ == "__main__":
    main()