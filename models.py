from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from sqlalchemy import select
from datetime import datetime, timedelta

db = SQLAlchemy()
bcrypt = Bcrypt()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(16), unique=True, nullable=False)
    lab = db.Column(db.String(80), nullable=False)
    priority = db.Column(db.Integer, nullable=False) # 使用者的優先權 (數值越小優先度越高)
    time_multiplier = db.Column(db.Float, default=1.0, nullable=False)  # GPU 可租用時間倍率
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_show = db.Column(db.Boolean, default=True, nullable=False)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def list_gpu_access_id(self):
        stmt = (
            select(GPU.id)
            .select_from(user_gpu_access.join(GPU))
            .where(user_gpu_access.c.user_id == self.id)
        )
        return db.session.execute(stmt).scalars().all()
    
    def list_gpu_access_model(self):
        stmt = (
            select(GPU.model, GPU.cuda_version)
            .select_from(user_gpu_access.join(GPU))
            .where(user_gpu_access.c.user_id == self.id)
        )
        return db.session.execute(stmt).all()
    
    def add_gpu_access(self, gpu_id):
        # 檢查是否已經有這個 GPU 存取權限
        existing_access = db.session.execute(
            user_gpu_access.select().where(
                user_gpu_access.c.user_id == self.id,
                user_gpu_access.c.gpu_id == gpu_id
            )
        ).fetchone()

        if existing_access:
            return  # 如果已經有這個關聯，則不進行插入
    
        db.session.execute(user_gpu_access.insert().values(user_id=self.id, gpu_id=gpu_id))
        db.session.commit()

    def remove_gpu_access(self, gpu_id):
        # 檢查是否存在此關聯
        existing_access = db.session.execute(
            user_gpu_access.select().where(
                user_gpu_access.c.user_id == self.id,
                user_gpu_access.c.gpu_id == gpu_id
            )
        ).fetchone()
        
        if not existing_access:
            return  # 如果沒有此關聯，則不進行刪除
        
        db.session.execute(
            user_gpu_access.delete().where(
                db.and_(
                    user_gpu_access.c.user_id == self.id,
                    user_gpu_access.c.gpu_id == gpu_id
                )
            )
        )
        db.session.commit()

    def __repr__(self) -> str:
        return "<User {}>".format(self.username)

class GPU(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model = db.Column(db.String(80), nullable=False)  # GPU型號
    cuda_version = db.Column(db.String(80), nullable=False)  # CUDA版本
    max_hours = db.Column(db.Integer, nullable=False, default=48)  # 單次申請 GPU 的最大時數限制
    connection_info = db.Column(db.String(255), nullable=False)  # 連線方式與帳密
    status = db.Column(db.Boolean, nullable=False)  # 狀態：啟用/禁用
    in_use = db.Column(db.Boolean, default=False)  # 是否正在使用
    is_show = db.Column(db.Boolean, default=True, nullable=False)

    def list_users(self):
        stmt = (
            db.select(User)
            .select_from(user_gpu_access.join(User))
            .where(user_gpu_access.c.gpu_id == self.id)
            .order_by(User.is_admin.desc())  # 在查詢語句中添加排序
        )
        return db.session.execute(stmt).scalars().all()
    
    def __repr__(self):
        return f"<GPU {self.model}, CUDA {self.cuda_version}, Status {'Enabled' if self.status else 'Disabled'}>"

user_gpu_access = db.Table(
    'user_gpu_access',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('gpu_id', db.Integer, db.ForeignKey('gpu.id', ondelete='CASCADE'), primary_key=True)
)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gpu_id = db.Column(db.Integer, db.ForeignKey('gpu.id'), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    reservation_time = db.Column(db.DateTime, nullable=False)
    notification_time = db.Column(db.DateTime, nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref='reservations')
    gpu = db.relationship('GPU', backref='reservations')

    def __repr__(self) -> str:
        return "<Reservation {}, User {}, GPU {}, {} - {}>".format(self.id, self.user_id, self.gpu_id, self.start_time, self.end_time)


class GPUStats(db.Model):
    __tablename__ = 'gpu_stats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    gpu_index = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    name = db.Column(db.String(255))  # 指定最大長度為 255 字元
    pci_bus_id = db.Column(db.String(255))  # 同樣指定長度
    driver_version = db.Column(db.String(255))
    pstate = db.Column(db.String(50))  # 根據實際需求調整長度
    pcie_link_gen_max = db.Column(db.Integer)
    pcie_link_gen_current = db.Column(db.Integer)
    temperature_gpu = db.Column(db.Float)
    utilization_gpu = db.Column(db.Float)
    utilization_memory = db.Column(db.Float)
    memory_total = db.Column(db.Float)
    memory_free = db.Column(db.Float)
    memory_used = db.Column(db.Float)