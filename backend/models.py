# 数据库模型
from flask_sqlalchemy import SQLAlchemy

# 创建数据库实例
db = SQLAlchemy()

class History(db.Model):
    """打卡历史表"""
    __tablename__ = 'history'
    
    date = db.Column(db.String(10), primary_key=True, comment='日期（YYYY-MM-DD）')
    images = db.Column(db.Integer, default=0, comment='上传的图片数量')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp(), comment='创建时间')
    
    # 关系
    tasks = db.relationship('Task', backref='history', lazy=True, cascade='all, delete-orphan')

class Task(db.Model):
    """任务表"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='任务ID')
    date = db.Column(db.String(10), db.ForeignKey('history.date'), nullable=False, comment='关联的日期')
    text = db.Column(db.Text, nullable=False, comment='任务内容')
    tag = db.Column(db.String(50), nullable=False, comment='任务标签')
    tag_color = db.Column(db.String(20), nullable=False, comment='标签颜色')
    completed = db.Column(db.Integer, default=0, comment='完成状态（1=已完成，0=未完成）')
    completed_time = db.Column(db.String(20), nullable=True, comment='完成时间')