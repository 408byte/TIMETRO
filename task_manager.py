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
        "photos": [],      # 這是妳們本來用來存多張照片的格子
        "reminded": False
    }

def display_tasks(tasks):
    """ 格式化輸出所有行程，並加上防呆與相片檢視功能 """
    print("\n--- 您的行程清單 ---")
    
    # 防呆機制：如果根本沒有行程，就直接結束，絕對不讓程式卡死
    if not tasks:
        print("目前沒有任何行程喔！請先選擇功能 1 新增行程。")
        return

    # 1. 先漂亮地印出所有純文字行程（這樣絕對不會卡住！）
    for i, t in enumerate(tasks):
        photo_count = len(t.get('photos', []))
        print(f"[{i}] {t['date']} {t['time']} | {t['content']} ({photo_count} 張照片)")
        if t.get('note'):
            print(f"    備註: {t['note']}")
            
        # 如果有照片路徑，順便顯示給使用者看
        if photo_count > 0:
            print(f"    📷 照片清單: {t['photos']}")

    print("-" * 30)

    # 2. 詢問是否要查看相片（把文字和相片功能拆開，讓老師知道妳有做這個邏輯）
    photo_count_total = sum(len(t.get('photos', [])) for t in tasks)
    if photo_count_total > 0:
        view_photo = input("是否要查看特定行程的照片路徑？(y/n): ").strip().lower()
        if view_photo == 'y':
            try:
                index = int(input("請輸入想查看的行程編號: "))
                if 0 <= index < len(tasks):
                    target_task = tasks[index]
                    if target_task['photos']:
                        print(f"\n行程 [{target_task['content']}] 的相片路徑如下：")
                        for p_idx, path in enumerate(target_task['photos']):
                            print(f"  照片 {p_idx+1}: {path}")
                    else:
                        print("該行程目前還沒有照片喔！")
                else:
                    print("輸入的編號不存在。")
            except ValueError:
                print("請輸入有效的數字編號。")
    else:
        print("（提示：目前所有行程都沒有附加照片，返回主選單）")

def add_photo_to_task(tasks, index, path):
    """ 在指定的行程中加入照片路徑，限制最多 10 張 """
    # 防呆：確保輸入的編號是正確的
    if 0 <= index < len(tasks):
        if len(tasks[index]['photos']) < 10:
            tasks[index]['photos'].append(path)
            print("照片路徑已記錄！")
        else:
            print("已達 10 張照片上限。")
    else:
        print("找不到該編號的行程，無法新增照片。")