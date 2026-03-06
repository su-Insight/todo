# 主应用文件
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from config import Config
from models import db, History, Task
import json
import os
from datetime import datetime
from werkzeug.utils import secure_filename

# API 路径前缀
API_PREFIX = '/todo/api'

# 创建应用实例
app = Flask(__name__)
app.config.from_object(Config)

# 配置文件上传
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大16MB

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化数据库
db.init_app(app)

# 启用CORS
CORS(app, resources={r"/todo/api/*": {"origins": "*"}}, supports_credentials=True)

# 创建数据库表
with app.app_context():
    db.create_all()

# API接口
@app.route(f'{API_PREFIX}/history/<date>', methods=['GET'])
def get_history(date):
    """获取指定日期的打卡记录"""
    history = History.query.filter_by(date=date).first()
    
    # 先检查是否有打卡记录（历史表），没有则返回404
    if not history:
        return jsonify({'error': 'Record not found'}), 404
    
    # 获取该日期的所有任务
    all_tasks = Task.query.filter_by(date=date).all()
    tasks = []
    for task in all_tasks:
        tasks.append({
            'id': task.id,
            'text': task.text,
            'tag': task.tag,
            'tagColor': task.tag_color,
            'completed': task.completed == 1,
            'completedTime': task.completed_time
        })
    
    return jsonify({
        'date': history.date,
        'tasks': tasks,
        'images': history.images
    })

@app.route(f'{API_PREFIX}/history', methods=['POST'])
def save_history():
    """保存打卡记录"""
    data = request.get_json()
    date = data.get('date')
    images = data.get('images', 0)
    
    # 检查是否已存在
    history = History.query.filter_by(date=date).first()
    if history:
        # 更新现有记录
        history.images = images
    else:
        # 创建新记录
        history = History(date=date, images=images)
        db.session.add(history)
    
    db.session.commit()
    return jsonify({'message': 'Record saved successfully'})

@app.route(f'{API_PREFIX}/history', methods=['GET'])
def get_all_history():
    """获取所有打卡记录"""
    histories = History.query.all()
    result = []
    for history in histories:
        result.append({
            'date': history.date,
            'images': history.images,
            'created_at': history.created_at.isoformat() if history.created_at else None
        })
    return jsonify(result)

@app.route(f'{API_PREFIX}/streak', methods=['GET'])
def get_streak():
    """计算连续打卡天数"""
    from datetime import datetime, timedelta
    
    histories = History.query.order_by(History.date.desc()).all()
    
    if not histories:
        return jsonify({'streak': 0})
    
    # 将日期字符串转换为datetime对象并排序
    dates = sorted([datetime.strptime(h.date, '%Y-%m-%d') for h in histories], reverse=True)
    
    # 计算连续打卡天数
    streak = 1
    today = datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 检查最新打卡日期是否是今天或昨天
    if dates[0] < today - timedelta(days=1):
        streak = 0
    else:
        for i in range(1, len(dates)):
            diff = (dates[i-1] - dates[i]).days
            if diff == 1:
                streak += 1
            else:
                break
    
    return jsonify({'streak': streak})

@app.route(f'{API_PREFIX}/tasks/<date>', methods=['GET'])
def get_tasks(date):
    """获取指定日期的任务"""
    tasks = Task.query.filter_by(date=date).all()
    result = []
    for task in tasks:
        result.append({
            'id': task.id,
            'text': task.text,
            'tag': task.tag,
            'tagColor': task.tag_color,
            'completed': task.completed == 1,
            'completedTime': task.completed_time
        })
    return jsonify(result)

@app.route(f'{API_PREFIX}/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """更新单个任务的状态"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    data = request.get_json()
    completed = data.get('completed')
    
    if completed is not None:
        task.completed = 1 if completed else 0
        if completed:
            from datetime import datetime
            task.completed_time = datetime.now().strftime('%H:%M')
        else:
            task.completed_time = None
    
    db.session.commit()
    return jsonify({'message': 'Task updated successfully'})

@app.route(f'{API_PREFIX}/tasks', methods=['POST'])
def create_task():
    """创建新任务"""
    data = request.get_json()
    date = data.get('date')
    text = data.get('text')
    tag = data.get('tag')
    tag_color = data.get('tagColor')
    
    new_task = Task(
        date=date,
        text=text,
        tag=tag,
        tag_color=tag_color,
        completed=0
    )
    
    db.session.add(new_task)
    db.session.commit()
    
    return jsonify({
        'id': new_task.id,
        'text': new_task.text,
        'tag': new_task.tag,
        'tagColor': new_task.tag_color,
        'completed': new_task.completed == 1
    })

@app.route(f'{API_PREFIX}/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'error': 'Task not found'}), 404
    
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted successfully'})

@app.route(f'{API_PREFIX}/tomorrow', methods=['GET'])
def get_tomorrow_tasks():
    """获取明日任务列表"""
    tomorrow = get_tomorrow_date()
    tasks = Task.query.filter_by(date=tomorrow).all()
    result = []
    for task in tasks:
        result.append({
            'id': task.id,
            'text': task.text,
            'tag': task.tag,
            'tagColor': task.tag_color
        })
    return jsonify(result)

@app.route(f'{API_PREFIX}/tomorrow', methods=['POST'])
def save_tomorrow_tasks():
    """保存明日任务列表"""
    data = request.get_json()
    tasks = data.get('tasks', [])
    tomorrow = get_tomorrow_date()
    
    # 删除旧的明日任务
    Task.query.filter_by(date=tomorrow).delete()
    
    # 添加新的明日任务
    for task in tasks:
        new_task = Task(
            date=tomorrow,
            text=task.get('text'),
            tag=task.get('tag'),
            tag_color=task.get('tagColor'),
            completed=0
        )
        db.session.add(new_task)
    
    db.session.commit()
    return jsonify({'message': 'Tomorrow tasks saved successfully'})

@app.route(f'{API_PREFIX}/tomorrow', methods=['DELETE'])
def clear_tomorrow_tasks():
    """清空明日任务列表"""
    tomorrow = get_tomorrow_date()
    Task.query.filter_by(date=tomorrow).delete()
    db.session.commit()
    return jsonify({'message': 'Tomorrow tasks cleared successfully'})

def get_tomorrow_date():
    """获取明天的日期"""
    from datetime import datetime, timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime('%Y-%m-%d')

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route(f'{API_PREFIX}/images/upload', methods=['POST'])
def upload_images():
    """上传图片"""
    if 'images' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('images')
    date = request.form.get('date')
    
    if not date:
        return jsonify({'error': 'Date is required'}), 400
    
    uploaded_files = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # 获取原始文件名的扩展名
            original_filename = file.filename
            ext = ''
            if '.' in original_filename:
                ext = original_filename.rsplit('.', 1)[1].lower()
                ext = '.' + ext
            
            # 添加日期前缀避免文件名冲突
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
            filename = f"{date}_{timestamp}{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            uploaded_files.append({
                'filename': filename,
                'url': f'{API_PREFIX}/images/{filename}'
            })
    
    return jsonify({
        'message': 'Files uploaded successfully',
        'files': uploaded_files
    })

@app.route(f'{API_PREFIX}/images/<filename>', methods=['GET'])
def get_image(filename):
    """获取图片"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route(f'{API_PREFIX}/images/date/<date>', methods=['GET'])
def get_images_by_date(date):
    """获取指定日期的所有图片"""
    images = []
    upload_folder = app.config['UPLOAD_FOLDER']
    
    if os.path.exists(upload_folder):
        for filename in os.listdir(upload_folder):
            if filename.startswith(f"{date}_") and allowed_file(filename):
                images.append({
                    'filename': filename,
                    'url': f'{API_PREFIX}/images/{filename}'
                })
    
    return jsonify(images)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)