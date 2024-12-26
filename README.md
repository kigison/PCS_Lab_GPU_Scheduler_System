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
```
.
├── .gitignore
├── app
│   ├── static
│   │   ├── css
│   │   │   ├── login-styles.css
│   │   │   └── styles.css
│   │   ├── images
│   │   │   └── icon.png
│   │   └── js
│   │       ├── account_manage.js
│   │       ├── edit_profile.js
│   │       ├── login.js
│   │       ├── register.js
│   │       └── reservation.js
│   ├── templates
│   │   ├── account_manage.html
│   │   ├── dashboard.html
│   │   ├── edit_profile.html
│   │   ├── layout.html
│   │   ├── login.html
│   │   ├── register.html
│   │   └── reservation.html
│   ├── app.py
│   ├── config.py
│   ├── create_admin.py
│   ├── models.py
│   └── email_sender.py
└── README.md
```
---
---
<br><br>


# Database tables:
## Table `Reservation`:
| Field             | Type          | Constraints                              | Description                     |
| ------------------|---------------|------------------------------------------|---------------------------------|
| `id`              | Integer       | Primary Key                              | 唯一識別碼                       |
| `user_id`         | Integer       | ForeignKey('user.id'), nullable=False    | 連接到 User 表的外鍵             |
| `card`            | String(20)    | Nullable=False                           | 用戶的卡片資訊                   |
| `duration`        | Integer       | Nullable=False                           | 預約的持續時間                   |
| `reservation_time`| DateTime      | Nullable=False                           | 預約時間                         |
| `start_time`      | DateTime      | Nullable=True                            | 預約開始時間                     |
| `end_time`        | DateTime      | Nullable=True                            | 預約結束時間                     |
| `user`            | Relationship  | backref='reservations'                   | 與 User 表的關聯                 |

<br><br>

## Table `User`:
| Field            | Type           | Constraints                              | Description                       |
|------------------|----------------|------------------------------------------|-----------------------------------|
| `id`             | Integer        | Primary Key                              | 唯一識別碼                         |
| `username`       | String(80)     | Unique, Nullable=False                   | 用戶名                             |
| `name`           | String(100)    | Nullable=False                           | 用戶名稱                           |
| `email`          | String(100)    | Unique, Nullable=False                   | 電子郵件                           |
| `phone`          | String(16)     | Unique, Nullable=False                   | 電話號碼                           |
| `lab`            | String(80)     | Nullable=False                           | 所屬實驗室                         |
| `priority`       | Integer        | Nullable=False                           | 優先級                             |
| `authentication` | Boolean        | Default=False, Nullable=False            | 用戶認證狀態                       |
| `is_admin`       | Boolean        | Default=False, Nullable=False            | 是否為管理員                       |
| `password_hash`  | String(128)    | Nullable=False                           | 密碼哈希值                         |

<br><br>

## Table `gpu_stats`:
| Field                  | Type           | Constraints                              | Description                              |
|------------------------|----------------|------------------------------------------|------------------------------------------|
| `id`                   | Integer        | Primary Key, Autoincrement               | 唯一識別碼                                |
| `gpu_index`            | Integer        |                                          | GPU 索引                                 |
| `timestamp`            | DateTime       |                                          | 記錄時間                                 |
| `name`                 | String(255)    |                                          | GPU 名稱                                 |
| `pci_bus_id`           | String(255)    |                                          | PCI bus ID                               |
| `driver_version`       | String(255)    |                                          | 驅動版本                                 |
| `pstate`               | String(50)     |                                          | GPU 狀態                                 |
| `pcie_link_gen_max`    | Integer        |                                          | 最大 PCIe 連結代數                        |
| `pcie_link_gen_current`| Integer        |                                          | 當前 PCIe 連結代數                        |
| `temperature_gpu`      | Float          |                                          | GPU 溫度                                 |
| `utilization_gpu`      | Float          |                                          | GPU 使用率                               |
| `utilization_memory`   | Float          |                                          | 記憶體使用率                             |
| `memory_total`         | Float          |                                          | 記憶體總量                               |
| `memory_free`          | Float          |                                          | 可用記憶體                               |
| `memory_used`          | Float          |                                          | 已用記憶體                               |




