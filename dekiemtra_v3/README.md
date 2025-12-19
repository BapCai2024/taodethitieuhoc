# Tool ra đề kiểm tra (CT2018/TT27) — V3

## Cấu trúc
```
dekiemtra_v3/
  app.py
  modules/
  data/
  requirements.txt
  .streamlit/config.toml
```

## Chạy local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy Streamlit Cloud
- Repo phải đặt `app.py` và thư mục `modules/` **cùng cấp**.
- Trên Streamlit Cloud → `Main file path`: `dekiemtra_v3/app.py` (nếu bạn để trong thư mục con).

## API Gemini (tùy chọn)
- Đặt biến môi trường `GEMINI_API_KEY`, hoặc nhập trong sidebar.
- Bấm **Kiểm tra API** để bật AI.
