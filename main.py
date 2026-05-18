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
    """ 讓前端網頁新增行程 (同步支援複數照片日記結構) """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "沒有收到資料"}), 400
            
        # 🌟 完美相容終端機建立行程時的所有欄位名稱與恩琪的照片結構
        new_task = {
            "date": data.get("date"),
            "time": data.get("time"),
            "content": data.get("content"),
            "note": data.get("note", ""),
            "photos": data.get("photos", []),    # 支援 [{"path":..., "desc":...}] 結構
            "reminded": False                     # 預設未提醒
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
    print("=========================================")
    print("🌟   歡迎使用 TIMETRO 行事曆相簿助手   🌟")
    print("     結合生活行程與美好相簿的共享空間")
    print("=========================================")
    print("(💡 提示：網頁前端 API 伺服器已在背景同步啟動)\n")

    # 🚀 在背景啟動 Flask，程式才不會被 Flask 阻擋而無法操作選單
    flask_thread = threading.Thread(target=run_flask_server, daemon=True)
    flask_thread.start()

    while True:
        # 每次迴圈開始，自動檢查一次提醒
        check_reminders_simple(tasks)

        print("\n🎨 ━━━━━━ 功能選單 (TIMETRO) ━━━━━━")
        print("  1. 📅 新增行程與提醒")
        print("  2. 👀 查看所有行程與相片清單")
        print("  3. 📷 為特定行程上傳相片與解說 (恩琪進階)")
        print("  4. 🗑️ 刪除行程")
        print("  5. 💖 當月行程與相片日記回顧 (恩琪核心)")
        print("  q. 💾 儲存並安全離開")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        choice = input("👉 請選擇功能編號: ").strip().lower()

        if choice == '1':
            new_task = task_manager.create_task_input()
            # 防呆補全欄位
            if 'reminded' not in new_task:
                new_task['reminded'] = False
            if 'photos' not in new_task:
                new_task['photos'] = []
                
            tasks.append(new_task)
            storage.save_data(tasks)  # 新增完立刻存檔，網頁端才看得到
            print("✅ 行程已成功新增！")

        elif choice == '2':
            task_manager.display_tasks(tasks)

        elif choice == '3':
            task_manager.display_tasks(tasks)
            if not tasks:
                continue
            try:
                index = int(input("🔢 請輸入要附加照片的行程編號: "))
                photo_path = input("🔗 請輸入照片檔案路徑 (例如 pic.jpg): ").strip()
                task_manager.add_photo_to_task(tasks, index, photo_path)
                storage.save_data(tasks) # 存檔確保網頁端同步更新照片
            except (ValueError, IndexError):
                print("❌ 輸入錯誤，找不到該編號行程，請重新操作。")

        elif choice == '4':
            task_manager.display_tasks(tasks)
            if not tasks:
                continue
            try:
                index = int(input("🔢 請輸入要刪除的行程編號: "))
                if 0 <= index < len(tasks):
                    removed = tasks.pop(index)
                    storage.save_data(tasks)
                    print(f"🗑️ 已成功刪除行程：【{removed['content']}】")
                else:
                    print("❌ 找不到該編號的行程。")
            except (ValueError, IndexError):
                print("❌ 輸入錯誤，請重新操作。")

        elif choice == '5':
            # 呼叫當月回顧核心與排版功能
            task_manager.monthly_review(tasks)

        elif choice == 'q':
            storage.save_data(tasks)
            print("\n💾 資料已安全儲存！感謝使用 TIMETRO，下次見！✨")
            break
        else:
            print("❌ 無效輸入，請輸入 1~5 或 q。")

def check_reminders_simple(tasks):
    """ MVP 提醒功能 """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for t in tasks:
        task_time = f"{t.get('date', '')} {t.get('time', '')}"
        if len(t.get('date', '')) == 10 and len(t.get('time', '')) == 5:
            if now >= task_time and not t.get('reminded'):
                print(f"\n🔔 ⚡【TIMETRO 系統即時提醒】")
                print(f"   現在時間是 {now}")
                print(f"   ⏰ 您的行程：【{t.get('content', '未命名')}】該開始囉！")
                if t.get('note'):
                    print(f"   💡 備註提醒: {t['note']}")
                print("━" * 25)
                t['reminded'] = True  # 標記為已提醒

if __name__ == "__main__":
    main()