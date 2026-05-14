from flask import Flask, request, jsonify
import storage # 引入您現有的 storage.py

app = Flask(__name__)

@app.route('/')
def home():
    return 'Hello, Flask API is running!'

@app.route('/tasks', methods=['POST'])
def add_task():
    # 確保接收到的資料是 JSON 格式
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    new_task_data = request.get_json() # 取得前端傳來的 JSON 資料

    # 這裡我們需要調整 create_task_input 的邏輯
    # 讓它可以直接從 new_task_data 建立任務，而不是透過 input()
    # 為了簡化，目前我們先直接將收到的資料作為新任務
    task = {
        "date": new_task_data.get('date'),
        "time": new_task_data.get('time'),
        "content": new_task_data.get('content'),
        "note": new_task_data.get('note', ''), # 備註可選
        "photos": [],
        "reminded": False
    }

    tasks = storage.load_data()
    tasks.append(task)
    storage.save_data(tasks)

    return jsonify({"message": "Task added successfully!", "task": task}), 201


@app.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = storage.load_data()
    return jsonify(tasks)

# 為了在 Colab 中運行 Flask，我們需要指定 host 和 port
# 並將 debug 設置為 True 方便開發
# 注意：在生產環境中，debug 模式應關閉
if __name__ == '__main__':
    # 使用 0.0.0.0 讓外部可以訪問 (在 Colab 環境中很重要)
    app.run(host='0.0.0.0', port=5000, debug=True)
