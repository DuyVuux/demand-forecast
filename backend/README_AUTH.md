# Backend Auth Guide (FastAPI)

## Tính năng
- Đăng ký (register), đăng nhập (login), làm mới token (refresh), lấy thông tin hiện tại (me)
- JWT Access/Refresh token
- Hash mật khẩu (bcrypt), validate input (Pydantic)
- Phân quyền cơ bản qua claim `role` (mặc định: `user`)

## Endpoint
- POST `/auth/register` — Đăng ký tài khoản mới
- POST `/auth/login` — Đăng nhập, trả về access_token và refresh_token
- POST `/auth/refresh` — Cấp lại cặp token từ refresh_token hợp lệ
- GET `/auth/me` — Thông tin tài khoản hiện tại (yêu cầu Authorization)

## Biến môi trường (.env)
```
JWT_SECRET=your_dev_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRES_MIN=60
REFRESH_TOKEN_EXPIRES_MIN=10080  # 7 ngày
```

## Cài đặt & chạy
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8010 --reload
```

## Luồng mẫu (cURL)
```bash
# 1) Đăng ký
curl -s -X POST http://localhost:8010/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username": "demo", "password": "secret123", "email": "demo@example.com"}'

# 2) Đăng nhập
LOGIN=$(curl -s -X POST http://localhost:8010/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username": "demo", "password": "secret123"}')
ACCESS=$(echo "$LOGIN" | jq -r .access_token)
REFRESH=$(echo "$LOGIN" | jq -r .refresh_token)

# 3) Gọi /auth/me với access token
curl -s -H "Authorization: Bearer $ACCESS" http://localhost:8010/auth/me

# 4) Làm mới token
REFRESHED=$(curl -s -X POST http://localhost:8010/auth/refresh \
  -H 'Content-Type: application/json' \
  -d '{"refresh_token": "'"$REFRESH"'"}')
```

## Tích hợp vào project
- Đã include router trong `app/main.py`: `app.include_router(auth.router)`
- Module liên quan:
  - `app/models/user.py` — SQLAlchemy model `User`
  - `app/schemas/user_schema.py` — Pydantic (Register/Login/Refresh/UserOut/TokenResponse)
  - `app/core/security.py` — Hash mật khẩu, JWT access/refresh, dependency `get_current_user_claims` & `require_roles`
  - `app/services/auth_service.py` — Đăng ký, xác thực và cấp token
  - `app/routers/auth.py` — Endpoint `/auth/*`
- DB: `app/db.py` đã import model `User` khi khởi động để tạo bảng `users`.

## Ghi chú bảo mật
- Dev: refresh token dạng stateless. Prod: cân nhắc rotate + revoke list.
- Đặt `JWT_SECRET` mạnh trong `.env`. Không commit `.env` vào VCS.
- Bật HTTPS ở môi trường sản xuất.
