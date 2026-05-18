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

        print("\n🎨 ━━━━━━ 功能選單 (TIMETRO) ━━━━━━")
        print("  1. 📅 新增行程與提醒")
        print("  2. 👀 查看所有行程與相片清單")
        print("  3. 📷 為特定行程上傳相片與解說")
        print("  4. 🗑️ 刪除行程")
        print("  5. 💖 當月行程與相片日記回顧")
        print("  q. 💾 儲存並安全離開")
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        choice = input("👉 請選擇功能編號: ").strip().lower()

        if choice == '1':
            new_task = task_manager.create_task_input()
            tasks.append(new_task)
            print("✅ 行程已成功新增！")

        elif choice == '2':
            task_manager.display_tasks(tasks)

        elif choice == '3':
            task_manager.display_tasks(tasks)
            if not tasks:
                continue
            try:
                index = int(input("🔢 請輸入要附加照片的行程編號: "))
                photo_path = input("🔗 請輸入照片檔案路徑 (例如 pic.jpg): ").strip("C:\Users\user\OneDrive\桌面\𝐍𝐂𝐔\114第二學期(大三下)\教育部海外研習申請\簡報照片\背景-3.jpg")
                task_manager.add_photo_to_task(tasks, index, photo_path)
            except ValueError:
                print("❌ 編號請輸入有效的數字。")

        elif choice == '4':
            task_manager.display_tasks(tasks)
            if not tasks:
                continue
            try:
                index = int(input("🔢 請輸入要刪除的行程編號: "))
                if 0 <= index < len(tasks):
                    removed = tasks.pop(index)
                    print(f"🗑️ 已成功刪除行程：【{removed['content']}】")
                else:
                    print("❌ 找不到該編號的行程。")
            except ValueError:
                print("❌ 請輸入有效的數字。")

        elif choice == '5':
            # 呼叫當月回顧功能
            task_manager.monthly_review(tasks)

        elif choice == 'q':
            storage.save_data(tasks)
            print("\n💾 資料已安全儲存！感謝使用 TIMETRO，下次見！✨")
            break
        else:
            print("❌ 無效輸入，請輸入 1~5 或 q。")

def check_reminders_simple(tasks):
    """
    MVP 提醒功能：檢查目前時間是否超過行程時間且尚未提醒過
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    for t in tasks:
        task_time = f"{t['date']} {t['time']}"
        # 為了確保輸入格式不對時不會當掉，加上長度防呆
        if len(t.get('date', '')) == 10 and len(t.get('time', '')) == 5:
            if now >= task_time and not t.get('reminded'):
                print(f"\n🔔 ⚡【TIMETRO 系統即時提醒】")
                print(f"   現在時間是 {now}")
                print(f"   ⏰ 您的行程：【{t['content']}】該開始囉！")
                if t.get('note'):
                    print(f"   💡 備註提醒: {t['note']}")
                print("━" * 25)
                t['reminded'] = True  # 標記為已提醒

if __name__ == "__main__":
    main()