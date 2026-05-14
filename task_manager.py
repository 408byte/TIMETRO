#功能模組
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