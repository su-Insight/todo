# 配置文件
import os

class Config:
    # 基础配置
    DEBUG = True
    SECRET_KEY = 'your-secret-key'
    
    # 数据库配置
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False