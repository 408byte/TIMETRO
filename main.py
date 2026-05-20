import task_manager
import storage
from datetime import datetime

def main():
    print("=== 歡迎使用 TIMETRO 行事曆助手 ===")
    print("(💡 提示：此處為小黑窗選單。如需使用網頁，請保持 web_server.py 執行中)")

    while True:
        tasks = storage.load_data()
        check_reminders_simple(tasks)

        print("\n--- 功能選單 ---")
        print("1. 新增行程與提醒")
        print("2. 查看所有行程與相片")
        print("3. 為行程新增照片路徑")
        print("4. 刪除行程")
        print("5. 當月行程與相片日記回顧")
        print("q. 儲存並離開")

        choice = input("請選擇功能: ").strip().lower()

        if choice == '1':
            new_task = task_manager.create_task_input()
            tasks.append(new_task)
            storage.save_data(tasks)  
            print("行程已新增！")
        elif choice == '2':
            try: task_manager.display_tasks(tasks)
            except Exception:
                for idx, t in enumerate(tasks): print(f"[{idx}] {t.get('date')} {t.get('time')} - {t.get('content')}")
        elif choice == '3':
            try:
                for idx, t in enumerate(tasks): print(f"[{idx}] {t.get('date')} {t.get('time')} - {t.get('content')}")
                index = int(input("請輸入要編輯的行程編號: "))
                photo_path = input("請輸入照片檔案路徑: ")
                if 0 <= index < len(tasks):
                    if "photos" not in tasks[index]: tasks[index]["photos"] = []
                    tasks[index]["photos"].append(photo_path)
                    storage.save_data(tasks)
                    print("照片已成功新增！")
                else: print("編號超出範圍！")
            except Exception: print("輸入編號錯誤！")
        elif choice == '4':
            try:
                for idx, t in enumerate(tasks): print(f"[{idx}] {t.get('date')} {t.get('time')} - {t.get('content')}")
                index = int(input("請輸入要刪除的行程編號: "))
                tasks.pop(index)
                storage.save_data(tasks)  
                print("刪除成功！")
            except Exception: print("刪除失敗。")
        elif choice == '5':
            try: task_manager.monthly_review(tasks)
            except Exception: print("回顧讀取失敗。")
        elif choice == 'q':
            break

def check_reminders_simple(tasks):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    updated = False
    for t in tasks:
        if f"{t.get('date', '')} {t.get('time', '')}" <= now and not t.get('reminded'):
            print(f"\n🔔 【提醒通知】現在是 {now}，行程：{t.get('content', '未命名')} 該開始囉！")
            t['reminded'] = True  
            updated = True
    if updated: storage.save_data(tasks)

if __name__ == "__main__":
    main()