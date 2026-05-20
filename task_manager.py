def create_task_input():
    """ 取得使用者輸入並回傳一個 dict """
    date = input("日期 (YYYY-MM-DD): ")
    time = input("時間 (HH:MM): ")
    content = input("行程內容: ")
    note = input("備註: ")
    return {
        "date": date,
        "time": time,
        "content": content,
        "note": note,
        "photos": [],
        "reminded": False
    }

def display_tasks(tasks):
    """ 格式化輸出所有行程 """
    print("\n--- 您的行程清單 ---")
    for i, t in enumerate(tasks):
        photo_count = len(t['photos'])
        print(f"[{i}] {t['date']} {t['time']} | {t['content']} ({photo_count} 張照片)")
        if t['note']:
            print(f"    備註: {t['note']}")

def add_photo_to_task(tasks, index, path):
    """ 在指定的行程中加入照片路徑，限制最多 10 張 """
    if len(tasks[index]['photos']) < 10:
        tasks[index]['photos'].append(path)
        print("照片路徑已記錄！")
    else:
        print("已達 10 張照片上限。")

def monthly_review(tasks):
    """ 依特定月份過濾行程與照片，維持簡約排版風格 """
    print("\n--- 每月生活回顧 ---")
    if not tasks:
        print("目前沒有任何資料可以回顧。")
        return

    target_month = input("請輸入想回顧的月份 (例如 2026-05): ").strip()
    print(f"\n--- {target_month} 歷史紀錄回顧 ---")
    
    found = False
    for t in tasks:
        if t.get('date', '').startswith(target_month):
            found = True
            photos = t.get('photos', [])
            print(f"[{t.get('date')}] {t.get('time')} | {t.get('content')}")
            if t.get('note'):
                print(f"    備註: {t['note']}")
            if photos:
                print("    附加相片路徑:")
                for p in photos:
                    print(f"      - {p}")
            print("-" * 30)
            
    if not found:
        print(f"找不到 {target_month} 的任何行程紀錄。")