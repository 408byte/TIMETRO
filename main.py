import task_manager
import storage
from datetime import datetime

def main():
    # 1. 初始化：載入舊有資料
    tasks = storage.load_data()
    print("=== 歡迎使用 TIMETRO 行事曆助手 ===")

    while True:
        # 每次迴圈開始，先自動檢查一次提醒 (MVP 簡化版提醒)
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
            tasks.append(new_task)
            print("行程已新增！")

        elif choice == '2':
            task_manager.display_tasks(tasks)

        elif choice == '3':
            task_manager.display_tasks(tasks)
            index = int(input("請輸入要編輯的行程編號: "))
            photo_path = input("請輸入照片檔案路徑: ")
            task_manager.add_photo_to_task(tasks, index, photo_path)

        elif choice == '4':
            task_manager.display_tasks(tasks)
            index = int(input("請輸入要刪除的行程編號: "))
            tasks.pop(index)
            print("刪除成功！")

        elif choice == 'q':
            storage.save_data(tasks)
            print("資料已儲存，下次見！")
            break
        else:
            print("無效輸入，請重新選擇。")

def check_reminders_simple(tasks):
    """
    MVP 提醒功能：檢查目前時間是否超過行程時間且尚未提醒過
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for t in tasks:
        task_time = f"{t['date']} {t['time']}"
        if now >= task_time and not t.get('reminded'):
            print(f"\n🔔 【提醒通知】現在是 {now}，行程：{t['content']} 該開始囉！")
            t['reminded'] = True  # 標記為已提醒，避免重複跳出

if __name__ == "__main__":
    main()