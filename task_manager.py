from datetime import datetime

def create_task_input():
    """ 取得使用者輸入並回傳一個 dict """
    print("\n✨ 【新增行程欄位】 ✨")
    date = input("📅 日期 (YYYY-MM-DD): ").strip()
    time = input("⏰ 時間 (HH:MM): ").strip()
    content = input("📝 行程內容: ").strip()
    note = input("💡 備註事項: ").strip()
    return {
        "date": date,
        "time": time,
        "content": content,
        "note": note,
        "photos": [],      # 每筆照片存成 dict: {"path": 路徑, "desc": 解說}
        "reminded": False
    }

def display_tasks(tasks):
    """ 格式化輸出所有行程，並加上防呆與相片檢視功能 """
    print("\n================ 🗓️ 您的行程清單 ================")
    if not tasks:
        print("   目前沒有任何行程喔！請先選擇功能 1 新增行程。")
        print("=====================================================")
        return

    for i, t in enumerate(tasks):
        # 防呆：確保 photos 一定是清單型態
        if 'photos' not in t or not isinstance(t.get('photos'), list):
            t['photos'] = []
            
        photos = t.get('photos', [])
        photo_count = len(photos)
        print(f"\n📌 [{i}] {t['date']} ｜ {t['time']} ｜ 【{t['content']}】 ({photo_count} 張照片)")
        if t.get('note'):
            print(f"   💡 備註: {t['note']}")
            
        # 顯示照片路徑與文字解說
        if photo_count > 0:
            print("   📷 附加相片：")
            for idx, p in enumerate(photos):
                desc = p.get('desc', '無解說')
                print(f"      └─ 圖片 {idx+1}: {p['path']} (💬 解說: {desc})")
    print("\n=====================================================")

    # 詢問是否要查看相片詳細資料
    photo_count_total = sum(len(t.get('photos', [])) for t in tasks)
    if photo_count_total > 0:
        view_photo = input("是否要單獨查看特定行程的照片詳細解說？(y/n): ").strip().lower()
        if view_photo == 'y':
            try:
                index = int(input("請輸入行程編號: "))
                if 0 <= index < len(tasks):
                    target_task = tasks[index]
                    if target_task.get('photos'):
                        print(f"\n🖼️  行程【{target_task['content']}】的照片日記：")
                        for p_idx, p in enumerate(target_task['photos']):
                            print(f"   👉 照片 {p_idx+1} 路徑: {p['path']}")
                            print(f"      💬 文字解說: {p['desc']}")
                    else:
                        print("❌ 該行程目前還沒有照片喔！")
                else:
                    print("❌ 輸入的編號不存在。")
            except ValueError:
                print("❌ 請輸入有效的數字編號。")

def add_photo_to_task(tasks, index, path):
    """ 進階功能：在指定的行程中加入照片路徑與『文字解說』，限制最多 10 張 """
    if 0 <= index < len(tasks):
        # 防呆補全結構
        if 'photos' not in tasks[index] or not isinstance(tasks[index].get('photos'), list):
            tasks[index]['photos'] = []
            
        if len(tasks[index]['photos']) < 10:
            # 進階功能：讓使用者為這張照片輸入一段敘述文字
            desc = input("💬 請輸入這張照片的文字解說: ").strip()
            
            # 將照片路徑與解說包裝成一個字典存進去
            photo_data = {"path": path, "desc": desc}
            tasks[index]['photos'].append(photo_data)
            print("✨ 照片與文字解說已成功記錄！")
        else:
            print("❌ 已達 10 張照片上限。")
    else:
        print("❌ 找不到該編號的行程，無法新增照片。")

def monthly_review(tasks):
    """ 
    核心與進階功能：當月行程與相片回顧 (自動與個人化排版功能)
    讓使用者輸入年份與月份，並自由調整版面配置（要顯示照片牆或純文字）
    """
    print("\n================ 💖 TIMETRO 每月生活回顧 ================")
    if not tasks:
        print("   目前沒有任何資料可以回顧喔。")
        print("========================================================")
        return

    target_month = input("🔍 請輸入想回顧的月份 (格式如 2026-05): ").strip()
    
    # 進階功能：調整版面配置
    print("\n🎨 選擇你的回顧版面配置 (Layout Style)：")
    print("   [A] 豐富日記牆 (顯示行程、備註、相片及解說)")
    print("   [B] 簡約文字流 (僅顯示行程與備註，隱藏相片路徑)")
    layout_choice = input("👉 請選擇排版風格 (A/B): ").strip().upper()
    if layout_choice not in ['A', 'B']:
        layout_choice = 'A'  # 預設為風格 A

    print(f"\n✨✨✨ {target_month} 的生活碎片回顧展 (風格 {layout_choice}) ✨✨✨")
    print("-" * 56)
    
    found = False
    for t in tasks:
        # 檢查行程日期開頭是否符合使用者輸入的月份 (例如 2026-05-14 符合 2026-05)
        if t.get('date', '').startswith(target_month):
            found = True
            if 'photos' not in t or not isinstance(t.get('photos'), list):
                t['photos'] = []
            photos = t.get('photos', [])
            
            print(f"📅 【{t.get('date')}】 {t.get('time')}")
            print(f"📝 行程: {t.get('content')}")
            if t.get('note'):
                print(f"💡 備註: {t['note']}")
            
            # 根據設計的排版配置顯示
            if layout_choice == 'A':
                if photos:
                    print("🖼️  照片牆排版：")
                    for p_idx, p in enumerate(photos):
                        print(f"   [照片 {p_idx+1}] 🔗 {p['path']}")
                        print(f"   └── 💬 內文紀錄: {p['desc']}")
                else:
                    print("   📷 (這天沒有上傳照片)")
            elif layout_choice == 'B':
                if photos:
                    print(f"   📎 (已為你隱藏該天附加的 {len(photos)} 張相片詳細內容)")
            print("-" * 56)
            
    if not found:
        print(f"🔍 找不到 {target_month} 的任何行程紀錄喔！")
    print("========================================================")