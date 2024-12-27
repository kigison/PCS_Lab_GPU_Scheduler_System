需改善:
- 需要設定user 可見的card (例如某些外借單位不能見到某些卡)
- 新增使用時數顯示頁面-依GPU分類
- nginx gpusched.iottalk.tw
- user table的Priority, Status移至user_gpu_access，原本的Status改作為使用者的狀態
- 密碼欄位中文輸入法應禁用



---
---


## Priority:
User.priority first(0>1>2), and then use reservation_time to queue


---
---

已知Bug:

- `"GET /favicon.ico HTTP/1.1" 404`
  - 沒放icon - 用layout 方法在母版引入icon
- `"The Query.get() method is considered legacy as of the 1.x series of SQLAlchemy and becomes a legacy construct in 2.0. The method is now available as Session.get() (deprecated since: 2.0) (Background on SQLAlchemy 2.0 at: https://sqlalche.me/e/b8d9)"`
  - ModelClass.query.get(primary_key) 要改成 db.session.get(ModelClass, primary_key)。因query.get() 已被標記為過時 - 已修復
- register page 成功之後會跳轉，但沒有訊息。 - 已修復，尚未測試

---
---

<br><br>
# Project Directory Structure:
```bash tree -I "__pycache__" --dirsfirst
.
├── static
│   ├── css
│   │   ├── login-styles.css
│   │   └── styles.css
│   ├── images
│   │   └── icon.png
│   └── js
│       ├── account_manage.js
│       ├── edit_profile.js
│       ├── GPU_manage.js
│       ├── login.js
│       ├── register.js
│       ├── reservation.js
│       ├── reset_password.js
│       └── user_gpu_access_manage.js
├── templates
│   ├── account_manage.html
│   ├── dashboard.html
│   ├── edit_profile.html
│   ├── GPU_manage.html
│   ├── index.html
│   ├── layout.html
│   ├── login.html
│   ├── register.html
│   ├── reservation.html
│   ├── reservation_manage.html
│   ├── reset_password.html
│   └── user_gpu_access_manage.html
├── app.py
├── config.py
├── create_admin.py
├── email_sender.py
├── models.py
└── README.md

6 directories, 29 files
```
---
---
<br><br>



## Config setup:
```python
# config.py
import os

class Flask_Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://[account]:[password]@localhost/[db name]'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = False

class SMTP_Config:
    SENDER_EMAIL = "xxxxxxx@gmail.com"
    PASSWORD = "xxxxxxxx"

class Charts_Config:
    MAX_DISPLAY_DAYS = 7
    AGGREGATION_INTERVAL_MINUTES = 30
```
---
---
<br><br>

# Database Schema (資料庫結構)

## Tables (資料表)

### User (使用者)
| Column                | Type        | Constraints                                 | Description                             |
|-----------------------|-------------|---------------------------------------------|-----------------------------------------|
| id                    | Integer     | Primary Key                                 | User's UID                              |
| username              | String(80)  | Unique, Not Null                            | User's Account                          |
| name                  | String(100) | Not Null                                    | User's Fullname                         |
| email                 | String(100) | Unique, Not Null                            | User's Email                            |
| phone                 | String(16)  | Unique, Not Null                            | User's Phone Number                     |
| lab                   | String(80)  | Not Null                                    | User's Lab                               |
| priority              | Integer     | Not Null                                    | 使用者的優先級 (數值越小優先度越高)         |
| time_multiplier       | Float       | Default: 1.0, Not Null                      | GPU 可租用時間倍率 (例如 1.0 表示正常倍率)  |
| is_admin              | Boolean     | Default: False, Not Null                    | 是否為管理員                              |
| password_hash         | String(128) | Not Null                                    | 使用者密碼的雜湊值                         |

### GPU (圖形處理器)
| Column                | Type        | Constraints                                 | Description (描述)                            |
|-----------------------|-------------|---------------------------------------------|-----------------------------------------------|
| id                    | Integer     | Primary Key                                 | GPU 的唯一編號                                 |
| model                 | String(80)  | Not Null                                    | GPU 型號                                       |
| cuda_version          | String(80)  | Not Null                                    | 支援的 CUDA 版本                               |
| max_hours             | Integer     | Default: 48, Not Null                       | 單次申請 GPU 的最大時數                        |
| connection_info       | String(255) | Not Null                                    | GPU Server 連線資訊                      |
| status                | Boolean     | Not Null                                    | GPU 狀態 (啟用/禁用)                           |
| in_use                | Boolean     | Default: False                              | GPU 是否正在使用                               |

### Reservation (GPU 預約)
| Column                | Type        | Constraints                                 | Description (描述)                            |
|-----------------------|-------------|---------------------------------------------|-----------------------------------------------|
| id                    | Integer     | Primary Key                                 | 預約的唯一編號                                 |
| user_id               | Integer     | Foreign Key (user.id), Not Null             | 預約使用者的 ID                                |
| gpu_id                | Integer     | Foreign Key (gpu.id), Not Null              | 預約 GPU 的 ID                                 |
| duration              | Integer     | Not Null                                    | 預約使用的時間長度 (以小時為單位)             |
| reservation_time      | DateTime    | Not Null                                    | 預約建立的時間                                 |
| notification_time     | DateTime    | Nullable                                    | 通知下一位使用者的時間                         |
| start_time            | DateTime    | Nullable                                    | GPU 使用開始時間                               |
| end_time              | DateTime    | Nullable                                    | GPU 使用結束時間                               |

### GPUStats (GPU 統計數據)
| Column                | Type        | Constraints                                 | Description (描述)                            |
|-----------------------|-------------|---------------------------------------------|-----------------------------------------------|
| id                    | Integer     | Primary Key, Auto Increment                 | 統計數據的唯一編號                             |
| gpu_index             | Integer     |                                             | GPU 的索引編號                                 |
| timestamp             | DateTime    |                                             | 記錄時間                                       |
| name                  | String(255) |                                             | GPU 名稱                                       |
| pci_bus_id            | String(255) |                                             | PCI Bus ID                                     |
| driver_version        | String(255) |                                             | 驅動版本                                       |
| pstate                | String(50)  |                                             | 電源狀態                                       |
| pcie_link_gen_max     | Integer     |                                             | 最大 PCIe 傳輸代數                             |
| pcie_link_gen_current | Integer     |                                             | 當前 PCIe 傳輸代數                             |
| temperature_gpu       | Float       |                                             | GPU 溫度                                       |
| utilization_gpu       | Float       |                                             | GPU 使用率 (%)                                 |
| utilization_memory    | Float       |                                             | 記憶體使用率 (%)                               |
| memory_total          | Float       |                                             | GPU 記憶體總量 (MB)                            |
| memory_free           | Float       |                                             | GPU 記憶體空閒量 (MB)                          |
| memory_used           | Float       |                                             | GPU 記憶體使用量 (MB)                          |

### user_gpu_access (使用者-GPU 關聯表)
| Column                | Type        | Constraints                                 | Description (描述)                            |
|-----------------------|-------------|---------------------------------------------|-----------------------------------------------|
| user_id               | Integer     | Foreign Key (user.id), Primary Key, Cascade | 使用者的 ID                                    |
| gpu_id                | Integer     | Foreign Key (gpu.id), Primary Key, Cascade  | GPU 的 ID                                      |

## Relationships (關聯關係)

1. **User (使用者)**
   - `reservations`: 與 Reservation 的一對多關係
   - 與 GPU 的多對多關係 (透過 `user_gpu_access`)

2. **GPU (圖形處理器)**
   - `reservations`: 與 Reservation 的一對多關係
   - 與 User 的多對多關係 (透過 `user_gpu_access`)

3. **Reservation (GPU 預約)**
   - `user`: 與 User 的多對一關係
   - `gpu`: 與 GPU 的多對一關係


