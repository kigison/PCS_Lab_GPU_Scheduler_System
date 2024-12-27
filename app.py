from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, Response, abort
from flask_cors import CORS
from flask_caching import Cache
from config import Flask_Config, Charts_Config
from email_sender import EmailSender
from models import db, User, GPU, GPUStats, Reservation
from datetime import datetime, timedelta
from sqlalchemy import func
import pandas as pd
import json
import threading
import random, string, math
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

app = Flask(__name__)
app.config.from_object(Flask_Config)
db.init_app(app)
CORS(app)
email_sender = EmailSender()

# 配置快取
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache', 'CACHE_DEFAULT_TIMEOUT': Charts_Config.AGGREGATION_INTERVAL_MINUTES*60})

@app.before_request
def set_remote_addr():
    # 檢查 'X-Forwarded-For' 是否存在於標頭中
    if 'X-Forwarded-For' in request.headers:
        x_forwarded_for = request.headers['X-Forwarded-For']
        # 通常 X-Forwarded-For 包含一個 IP 列表，以逗號分隔，取第一個 IP
        request.environ['REMOTE_ADDR'] = x_forwarded_for.split(',')[0].strip()
    else:
        # 如果沒有該標頭，可以選擇拒絕請求或保留默認值
        abort(403, "Missing X-Forwarded-For header")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.json
        name = data.get('name')
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        password = data.get('password')

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return jsonify({"error": "User already exists or email has been registered!"}), 400

        new_user = User(
            name=name, 
            username=username, 
            email=email, 
            phone=phone, 
            lab="Other", 
            priority=2, 
            is_admin=False
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({"message": f"User {name}({username}) registered successfully!"}), 200
    
    return render_template('register.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        data = request.json
        action = data.get('action')
        current_user = db.session.get(User, session['user_id'])
        if action == "user_reset_password":
            old_password = data.get('old_password')
            new_password = data.get('new_password')
            if not current_user:
                return jsonify({"error": "Password reset fail. Please login first!"}), 400
            if current_user.check_password(old_password):
                # 更新密碼
                current_user.set_password(new_password)
                db.session.commit()
                threading.Thread(
                    target=email_sender.send_pwd_change_notify,
                    args=(current_user.name, current_user.username, current_user.email, datetime.now(), request.environ['REMOTE_ADDR']),
                    daemon=True
                ).start()
                return jsonify({"message": "Password reset successfully! Please use new password to login again!"}), 200
            else:
                return jsonify({"error": "Password reset fail. Old password isn't correct!"}), 400
        else:  # action == "admin_reset_password"
            try:
                user = db.session.get(User, data.get('id'))
                characters = string.ascii_letters + string.digits + string.punctuation
                new_password = ''.join(random.choices(characters, k=16))
                user.set_password(new_password)
                db.session.commit()
                threading.Thread(
                    target=email_sender.send_new_pwd,
                    args=(user.name, user.username, user.email, new_password),
                    daemon=True
                ).start()
                return jsonify({"message": "Password reset successfully!"}), 200
            except:
                return jsonify({"error": "Password reset fail!"}), 400
            
    return render_template('reset_password.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')

        user = User.query.filter_by(username=username).first()
        if user and user.is_show:
            return jsonify({"message": f"Hi, {user.name}. You have been deleted!"}), 401
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = username
            session['name'] = user.name
            session['is_admin'] = user.is_admin
            threading.Thread(
                target=email_sender.send_login_notify,
                args=(user.name, user.username, user.email, datetime.now(), request.environ['REMOTE_ADDR']),
                daemon=True
            ).start()
            return jsonify({"message": f"Hi, {user.name}. You have successfully logged in!"}), 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    
    # Redirect logged-in users to the index
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    # Clear the session
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    print(request.headers['X-Forwarded-For'])
    # Retrieve all GPUs from the database and show them in a list.
    current_user = db.session.get(User, session['user_id'])
    access_gpu_model = []
    for model, _ in current_user.list_gpu_access_model():
        if model not in access_gpu_model:
            access_gpu_model.append(model)
    return render_template('dashboard.html', access_gpu_model=access_gpu_model)

@app.route('/charts')
@cache.cached(timeout=Charts_Config.AGGREGATION_INTERVAL_MINUTES*60)  # 設置快取時間
def charts():
    # 獲取資料（增量更新）
    data = get_incremental_data()
    df = pd.DataFrame(data)

    # 將數據按scale time聚合，取最大值
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    df_resampled = df.groupby([pd.Grouper(freq=f'{Charts_Config.AGGREGATION_INTERVAL_MINUTES}min'), 'Index/Bus-Id']).max().reset_index()

    # 繪製圖表
    fig_utilization_memory = px.line(df_resampled, x='timestamp', y='utilization_memory', color='Index/Bus-Id',
                   labels={'timestamp': 'Time', 'utilization_memory': 'Memory Utilization (%)'},
                   title="Memory Utilization per GPU")
    fig_utilization_gpu = px.line(df_resampled, x='timestamp', y='utilization_gpu', color='Index/Bus-Id',
                   labels={'timestamp': 'Time', 'utilization_gpu': 'GPU Utilization (%)'},
                   title="GPU Utilization per GPU")
    fig_memory_used = px.line(df_resampled, x='timestamp', y='memory_used', color='Index/Bus-Id',
                   labels={'timestamp': 'Time', 'memory_used': 'Memory Used (MB)'},
                   title="Memory Used per GPU")
    fig_temperature_gpu = px.line(df_resampled, x='timestamp', y='temperature_gpu', color='Index/Bus-Id',
                   labels={'timestamp': 'Time', 'temperature_gpu': 'GPU Temperature (°C)'},
                   title="GPU Temperature per GPU")
    
    # 將圖表轉換為 JSON 可序列化的格式
    response = {
        'fig_utilization_memory': fig_utilization_memory,
        'fig_utilization_gpu': fig_utilization_gpu,
        'fig_memory_used': fig_memory_used,
        'fig_temperature_gpu': fig_temperature_gpu,
    }

    # 使用自定義的 PlotlyJSONEncoder 進行序列化
    return json.dumps(response, cls=PlotlyJSONEncoder)

def get_incremental_data():
    """增量獲取資料"""
    # 從 Cache 中讀取最後的時間戳，首次預設為 7 天前
    last_fetched_time = cache.get('last_fetched_time')
    if last_fetched_time is None:
        last_fetched_time = datetime.now() - timedelta(days=Charts_Config.MAX_DISPLAY_DAYS)
    else:
        last_fetched_time = pd.to_datetime(last_fetched_time)

    # 查詢新數據
    query = GPUStats.query.filter(GPUStats.timestamp > last_fetched_time).all()
    data = [
        {
            'Index/Bus-Id': f"{record.gpu_index}/{record.pci_bus_id.split(':')[1]}",
            'timestamp': record.timestamp,
            'temperature_gpu': record.temperature_gpu,
            'utilization_gpu': record.utilization_gpu,
            'utilization_memory': record.utilization_memory,
            'memory_used': record.memory_used
        }
        for record in query
    ]

    # 更新最後的時間戳
    if data:
        new_last_time = max(record['timestamp'] for record in data)
        cache.set('last_fetched_time', new_last_time)

    # 如果快取中已有舊數據，合併新數據
    cached_data = cache.get('gpu_data') or []
    combined_data = cached_data + data

    # 將合併後的數據快取
    cache.set('gpu_data', combined_data)
    return combined_data

@app.route('/reservation', methods=['GET', 'POST'])
def reservation():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = db.session.get(User, session['user_id'])
    
    if request.method == 'GET':
        gpu_access_id_list = current_user.list_gpu_access_id()
        
        GPU_list = GPU.query.order_by(
            -GPU.status, GPU.model, GPU.cuda_version, GPU.id
        ).filter(
            GPU.is_show==True
        ).all()
        GPUs_data = []
        
        for gpu in GPU_list:
            if gpu.id in gpu_access_id_list:
                existing_reservations = db.session.query(User, Reservation).join(
                    Reservation, 
                    Reservation.user_id == User.id
                ).order_by(
                    User.priority.asc(),
                    Reservation.reservation_time.asc()
                ).filter(
                    Reservation.gpu_id==gpu.id
                ).all()
                # print(existing_reservations)
                current_reservation = None
                duration = None
                start_time = None
                end_time = None
                notification_time = None
                waiting_list = []
                for existing_user, existing_reservation in existing_reservations:
                    if existing_reservation.end_time is None or existing_reservation.end_time > datetime.now():
                        waiting_list.append({
                            "name": existing_user.name,
                            "username": existing_user.username,
                            "lab": existing_user.lab,
                            "priority": existing_user.priority,
                            "duration": existing_reservation.duration
                        })
                        if existing_reservation.user_id == current_user.id:
                            current_reservation = existing_reservation
                            notification_time = current_reservation.notification_time
                            duration = current_reservation.duration
                            if current_reservation.start_time is not None:
                                start_time = current_reservation.start_time
                            elif current_reservation.end_time is not None:
                                end_time = current_reservation.end_time
                
                GPUs_data.append(
                    {
                        "id": gpu.id,
                        "model": gpu.model,
                        "cuda_version": gpu.cuda_version,
                        "max_hours": math.ceil(gpu.max_hours*current_user.time_multiplier),  # user可預約的最大時間
                        "connection_info": gpu.connection_info,  # 用於提供連接資訊(輪到當下才顯示)
                        "status": gpu.status,  # 用於判斷能否預約
                        "waiting_list": waiting_list,
                        "current_reservation": current_reservation,
                        "notification_time": notification_time,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration,
                    }
                )
        
        return render_template('reservation.html', GPUs_data=GPUs_data)
    
    else:
        data = request.json
        action = data.get('action')
        gpu_id = data.get('gpu')
        
        # print(action)
        # print(gpu_id)
        
        time_now = datetime.now()

        if action == 'terminate':
            current_reservation = db.session.query(Reservation).filter(
                Reservation.user_id==current_user.id,
                Reservation.gpu_id==gpu_id
            ).all()[-1]
            current_reservation.end_time = time_now
            
            next_pair = db.session.query(User, Reservation).join(
                Reservation, 
                Reservation.user_id == User.id
            ).order_by(
                User.priority.asc(),
                Reservation.reservation_time.asc()
            ).filter(
                Reservation.start_time.is_(None),
                Reservation.gpu_id==gpu_id
            ).first()
            if next_pair is not None:
                (next_user, next_reservation) = next_pair
                next_reservation.notification_time = time_now
            
            db.session.commit()
            
            return jsonify({'message': 'Reservation terminated successfully.'}), 200
            
        elif action == 'start':
            current_reservation = db.session.query(Reservation).filter(
                Reservation.user_id==current_user.id,
                Reservation.gpu_id==gpu_id
            ).all()[-1]
            current_reservation.start_time = time_now
            current_reservation.end_time = time_now + timedelta(hours=current_reservation.duration)
            
            db.session.commit()
            
            return jsonify({'message': 'Reservation started successfully.'}), 200
        
        elif action == 'cancel':
            scheduled_reservation = db.session.query(Reservation).filter(
                Reservation.user_id==current_user.id,
                Reservation.gpu_id==gpu_id
            ).all()[-1]
            scheduled_reservation.start_time = time_now
            scheduled_reservation.end_time = time_now
            
            db.session.commit()
            
            return jsonify({'message': 'Reservation canceled successfully.'}), 200
            
        else:  # action == 'reserve'
            reservations = db.session.query(Reservation).filter(
                Reservation.gpu_id==gpu_id
            ).all()
            
            has_ongoing_reservation = False
            for reservation in reservations:
                if reservation.end_time is None or reservation.end_time > time_now:
                    has_ongoing_reservation = True
                    break
            
            duration = data.get('duration')
            
            # Create a new reservation
            if has_ongoing_reservation:
                new_reservation = Reservation(
                    user_id=current_user.id,
                    gpu_id=gpu_id,
                    duration=duration,
                    reservation_time=time_now,
                )
            else:
                new_reservation = Reservation(
                    user_id=current_user.id,
                    gpu_id=gpu_id,
                    duration=duration,
                    reservation_time=time_now,
                    notification_time=time_now,
                )
            
            db.session.add(new_reservation)
            db.session.commit()

            return jsonify({'message': 'Reservation made successfully.'}), 200

@app.route('/reservation_manage', methods=['GET', 'POST'])
def reservation_manage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    current_user = db.session.get(User, session['user_id'])
    
    if not current_user or not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        GPU_list = GPU.query.order_by(-GPU.status, GPU.model, GPU.cuda_version, GPU.id).all()
        reservation_history = db.session.query(User, Reservation).join(
                Reservation, Reservation.user_id == User.id
            ).filter(
                Reservation.end_time.isnot(None)  # Exclude records where end_time is NULL
            ).order_by(
                Reservation.end_time.desc()
            )
        GPUs_data = []
            
        for gpu in GPU_list:
            GPUs_data.append(
                {
                    # "user_id":user.id,
                    "gpu_id": gpu.id,
                    "model": gpu.model,
                    "cuda_version": gpu.cuda_version,
                    "history_list": reservation_history.filter(Reservation.gpu_id==gpu.id).all()
                }
            )
        
        return render_template('reservation_manage.html', GPUs_data=GPUs_data)
    
    # if request.method == 'GET':
    #     for gpu in GPU_list:
    #         existing_reservations = db.session.query(User, Reservation).join(
    #             Reservation, 
    #             Reservation.user_id == User.id
    #         ).order_by(
    #             User.priority.asc(),
    #             Reservation.reservation_time.asc()
    #         ).filter(
    #             Reservation.gpu_id==gpu.id
    #         ).all()
    #         print(existing_reservations)
    #         current_reservation = None
    #         start_time = None
    #         end_time = None
    #         waiting_list = []
    #         for existing_user, existing_reservation in existing_reservations:
    #             if existing_reservation.end_time is None or existing_reservation.end_time > datetime.now():
    #                 waiting_list.append({
    #                     "name": existing_user.name,
    #                     "username": existing_user.username,
    #                     "lab": existing_user.lab,
    #                     "priority": existing_user.priority,
    #                     "duration": existing_reservation.duration
    #                 })
    #                 if existing_reservation.user_id == current_user.id:
    #                     current_reservation = existing_reservation
    #                     if current_reservation.start_time is not None:
    #                         start_time = current_reservation.start_time
    #                     elif current_reservation.end_time is not None:
    #                         end_time = current_reservation.end_time
            
    #         GPUs_data.append(
    #             {
    #                 "id": gpu.id,
    #                 "model": gpu.model,
    #                 "cuda_version": gpu.cuda_version,
    #                 "max_hours": math.ceil(gpu.max_hours*current_user.time_multiplier),  # user可預約的最大時間
    #                 "connection_info": gpu.connection_info,  # 用於提供連接資訊(輪到當下才顯示)
    #                 "status": gpu.status,  # 用於判斷能否預約
    #                 "waiting_list": waiting_list,
    #                 "current_reservation": current_reservation,
    #                 "start_time": start_time,
    #                 "end_time": end_time
    #             }
    #         )
    # else:
    #     data = request.json
    #     action = data.get('action')
    #     gpu_id = data.get('gpu')
        
    #     print(action)
    #     print(gpu_id)
        
    #     time_now = datetime.now()

    #     if action == 'terminate':
    #         current_reservation = db.session.query(Reservation).filter(
    #             Reservation.user_id==current_user.id,
    #             Reservation.gpu_id==gpu_id
    #         ).all()[-1]
    #         current_reservation.end_time = time_now
            
    #         next_pair = db.session.query(User, Reservation).join(
    #             Reservation, 
    #             Reservation.user_id == User.id
    #         ).order_by(
    #             User.priority.asc(),
    #             Reservation.reservation_time.asc()
    #         ).filter(
    #             Reservation.start_time.is_(None),
    #             Reservation.gpu_id==gpu_id
    #         ).first()
    #         if next_pair is not None:
    #             (next_user, next_reservation) = next_pair
    #             next_reservation.notification_time = time_now
            
    #         db.session.commit()
            
    #         return jsonify({'message': 'Reservation terminated successfully.'}), 200
            
    #     elif action == 'start':
    #         current_reservation = db.session.query(Reservation).filter(
    #             Reservation.user_id==current_user.id,
    #             Reservation.gpu_id==gpu_id
    #         ).all()[-1]
    #         current_reservation.start_time = time_now
    #         current_reservation.end_time = time_now + timedelta(hours=current_reservation.duration)
            
    #         db.session.commit()
            
    #         return jsonify({'message': 'Reservation started successfully.'}), 200
        
    #     elif action == 'cancel':
    #         scheduled_reservation = db.session.query(Reservation).filter(
    #             Reservation.user_id==current_user.id,
    #             Reservation.gpu_id==gpu_id
    #         ).all()[-1]
    #         scheduled_reservation.start_time = time_now
    #         scheduled_reservation.end_time = time_now
            
    #         db.session.commit()
            
    #         return jsonify({'message': 'Reservation canceled successfully.'}), 200
            
    #     else:
    #         reservations = db.session.query(Reservation).filter(
    #             Reservation.gpu_id==gpu_id
    #         ).all()
            
    #         has_ongoing_reservation = False
    #         for reservation in reservations:
    #             if reservation.end_time is None or reservation.end_time > time_now:
    #                 has_ongoing_reservation = True
    #                 break
            
    #         duration = data.get('duration')
            
    #         # Create a new reservation
    #         if has_ongoing_reservation:
    #             new_reservation = Reservation(
    #                 user_id=current_user.id,
    #                 gpu_id=gpu_id,
    #                 duration=duration,
    #                 reservation_time=time_now,
    #             )
    #         else:
    #             new_reservation = Reservation(
    #                 user_id=current_user.id,
    #                 gpu_id=gpu_id,
    #                 duration=duration,
    #                 reservation_time=time_now,
    #                 start_time=time_now,
    #                 end_time=time_now + timedelta(hours=float(duration)),
    #             )
            
    #         db.session.add(new_reservation)
    #         db.session.commit()

    #         return jsonify({'message': 'Reservation made successfully.'}), 200

@app.route('/account_manage', methods=['GET', 'POST'])
def account_manage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Ensure the user is admin, so the user can access this route.
    current_user = db.session.get(User, session['user_id'])
    
    if not current_user or not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        # Retrieve all users from the database and show them in a list.
        user_list = User.query.order_by(-User.is_admin).filter(
            User.is_show==True
        ).all()
        users_data = []
        
        for user in user_list:
            users_data.append(
                {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "email": user.email,
                    "phone": user.phone,
                    "lab": user.lab,
                    "priority": user.priority,
                    "time_multiplier": user.time_multiplier,
                    "is_admin": user.is_admin,
                }
            )
        
        return render_template('account_manage.html', users_data=users_data)
    
    else:
        data = request.json
        action = data.get('action')
        
        if action == "update":
            user_id = data.get('id')
            name = data.get('name')
            email = data.get('email')
            lab = data.get('lab')
            priority = data.get('priority')
            time_multiplier = data.get('time_multiplier')
            is_admin = data.get('is_admin')
            
            # Validate the user ID
            user = db.session.get(User, user_id)
            if not user:
                return jsonify({"error": "User not found"}), 400
            
            # Update status
            if lab:
                user.lab = lab
            if priority:
                user.priority = priority
            if name:
                user.name = name
            if email:
                user.email = email
            if time_multiplier is not None:
                user.time_multiplier = time_multiplier
            if is_admin is not None:
                user.is_admin = is_admin
                
            db.session.commit()
            return jsonify({"message": f"User {user.name}({user.username}) updated successfully"}), 200
        else:
            user_id = data.get('id')
            user = db.session.get(User, user_id)
            if current_user.id == user.id:
                return jsonify({"error": "You cannot delete your own account!"}), 400
            user.is_show = False
            
            user_waitings = db.session.query(Reservation).filter(
                Reservation.user_id==user_id,
                Reservation.start_time==None
            ).all()
            for user_waiting in user_waitings:
                db.session.delete(user_waiting)
            
            db.session.commit()
            return jsonify({"message": f"User {user.name}({user.username}) removed successfully"}), 200

@app.route('/GPU_manage', methods=['GET', 'POST'])
def GPU_manage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Ensure the user is admin, so the user can access this route.
    current_user = db.session.get(User, session['user_id'])
    
    if not current_user or not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        # Retrieve all GPUs from the database and show them in a list.
        GPU_list = GPU.query.order_by(
            -GPU.status, GPU.model, GPU.cuda_version, GPU.id
        ).filter(
            GPU.is_show==True
        ).all()
        GPUs_data = []
        
        for gpu in GPU_list:
            GPUs_data.append(
                {
                    "id": gpu.id,
                    "model": gpu.model,
                    "cuda_version": gpu.cuda_version,
                    "max_hours": gpu.max_hours,
                    "connection_info": gpu.connection_info,
                    "status": gpu.status,
                    "in_use": gpu.in_use
                }
            )
        
        return render_template('GPU_manage.html', GPUs_data=GPUs_data)
    
    else:  # Post
        data = request.json
        action = data.get('action')
        
        if action == "add":
            model = data.get("model")
            cuda_version = data.get("cuda_version")
            connection_info = data.get("connection_info")
            if not (model and cuda_version and connection_info):
                return jsonify({"error": "GPU add Error! Value not found!"}), 400
            
            db.session.add(GPU(model=model, cuda_version=cuda_version, connection_info=connection_info, status=False))
            db.session.commit()
            return jsonify({"message": f"GPU {model}({cuda_version}) add successfully"}), 200
        elif action == "update":
            GPU_id = data.get("id")
            max_hours = data.get("max_hours")
            connection_info = data.get("connection_info")
            status = data.get("status")

            gpu = db.session.get(GPU, GPU_id)
            if not gpu:
                return jsonify({"error": "GPU not found"}), 400

            # Update status
            if max_hours is not None:
                gpu.max_hours = max_hours
            if connection_info:
                gpu.connection_info = connection_info
            if status is not None:
                gpu.status = status
                
            db.session.commit()
            return jsonify({"message": f"GPU {gpu.model}({gpu.cuda_version}) updated successfully"}), 200
        else:
            GPU_id = data.get('id')
            gpu = db.session.get(GPU, GPU_id)
            if gpu.status:
                return jsonify({"error": "You cannot delete a GPU whose status is Enabled!"}), 400
            if gpu.in_use:
                return jsonify({"error": "You cannot delete a GPU whose is in use!"}), 400
            gpu.is_show = False
            db.session.commit()
            return jsonify({"message": f"GPU {gpu.model}({gpu.cuda_version}) removed successfully"}), 200

@app.route('/user_gpu_access_manage', methods=['GET', 'POST'])
def user_gpu_access_manage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Ensure the user is admin, so the user can access this route.
    current_user = db.session.get(User, session['user_id'])
    
    if not current_user or not current_user.is_admin:
        return redirect(url_for('index'))
    
    if request.method == 'GET':
        # Retrieve all GPUs from the database and show them in a list.
        user_list = User.query.order_by(-User.is_admin).filter(
            User.is_show==True
        ).all()
        GPU_list = GPU.query.order_by(
            -GPU.status, GPU.model, GPU.cuda_version, GPU.id
        ).filter(
            GPU.is_show==True
        ).all()
        users_data = []
        gpus_data = []
        
        for user in user_list:
            users_data.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "username": user.username,
                    "lab": user.lab,
                    "priority": user.priority,
                    "gpu_access_list": user.list_gpu_access_id()
                }
            )
        
        for gpu in GPU_list:
            gpus_data.append(
                {
                    "id": gpu.id,
                    "model": gpu.model,
                    "cuda_version": gpu.cuda_version,
                    "status": gpu.status,
                    "access_user_list": gpu.list_users()
                }
            )
        # all_GPU_list = db.session.query(GPU.id, GPU.model, GPU.cuda_version, GPU.status).order_by(-GPU.status, GPU.model, GPU.cuda_version, GPU.id).all()
        # print(all_GPU_list)
        return render_template('user_gpu_access_manage.html', users_data=users_data, gpus_data=gpus_data)
    
    else:  # Post
        try:
            data = request.json
            
            user_id = data.get('id')
            gpu_ids = data.get('selectedGpuIds')

            # 確保用戶 ID 和 GPU ID 為有效數據
            user = db.session.get(User, user_id)
            if not user:
                return jsonify({"error": "User not found"}), 400

            current_gpu_ids = user.list_gpu_access_id()  # 取得目前該用戶的 GPU 存取權限

            # 確保 gpu_ids 和 current_gpu_ids 的類型一致
            gpu_ids = [str(gpu_id) for gpu_id in gpu_ids]  # 前端傳來的 gpu_ids，轉換為字串
            current_gpu_ids = [str(gpu_id) for gpu_id in current_gpu_ids]  # 資料庫中的 GPU ID，轉換為字串
            

            # 計算需要新增的 GPU 和需要移除的 GPU
            gpus_to_add = set(gpu_ids) - set(current_gpu_ids)  # 需要新增的 GPU
            gpus_to_remove = set(current_gpu_ids) - set(gpu_ids)  # 需要移除的 GPU

            if not gpus_to_add and not gpus_to_remove:
                return Response(status=304)

            print(gpus_to_add, gpus_to_remove)
            # 新增 GPU 存取權限
            for gpu_id in gpus_to_add:
                user.add_gpu_access(gpu_id=gpu_id)

            # 移除 GPU 存取權限
            for gpu_id in gpus_to_remove:
                user.remove_gpu_access(gpu_id=gpu_id)

            return jsonify({"message": "User GPU access updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 500

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Ensure the user is admin, so the user can access this route.
    current_user = db.session.get(User, session['user_id'])
    # print(current_user.list_gpu_access_model())
    if request.method == 'GET':
        # Retrieve all users from the database and show them in a list.
        user_data = {
            "id": current_user.id,
            "name": current_user.name,
            "username": current_user.username,
            "email": current_user.email,
            "phone": current_user.phone,
            "lab": current_user.lab,
            "priority": current_user.priority,
            "is_admin": current_user.is_admin,
            "gpu_access_list": current_user.list_gpu_access_model()
            }
        return render_template('edit_profile.html', user=user_data)
    
    else:
        data = request.json
        user_id = data.get('id')
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        
        # Validate the user ID
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 400
        
        # Update user's info
        if email:
            user.email = email
        if phone:
            user.phone = phone
        if username:
            user.username = username
            
        db.session.commit()
        return jsonify({"message": f"User {session['name']} updated successfully"}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(host='127.0.0.1', port=54784, debug=True)
