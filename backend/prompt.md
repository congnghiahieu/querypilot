Tôi đang xây dựng backend FastAPI cho 1 ứng dụng Chatbot text2sql. Bao gồm các thông tin sau:

- App của tôi hướng đến sử dụng công nghệ AWS RDS (PostgreSQL) và AWS S3 (lưu trữ file upload của người dùng). Tuy nhiên tôi đang trong giai đoạn prototype nên sẽ sử dụng SQLlite và save file vào static file. Các tính năng bên dưới tôi liệt kê sẽ liên quan đến techstack này

- Hiện tại app của tôi có các chức năng sau:
1. Đăng nhập, đăng ký, đăng xuất, quên mật khẩu
2. Chat mới (chat trực tiếp), vào lại 1 đoạn chat trong lịch sử và chat tiếp. Chat có thể trả về kết quả là 1 trong 3 dạng text, chart, table. Vì app của tôi là text2sql nên sẽ có 1 hàm dịch prompt của người dùng về text2sql nhưng mà hiện tại tôi chưa có logic này, hãy viết cho tôi 1 stub function. Tôi sẽ hỏi bạn implement sau
3. Khi trả về kết quả cho client, người dùng có thể dowload table, chart dưới 3 định dạng PDF, CSV, Excel. Quá trình thực sự là người dùng call API đến chat, chat gọi đến text2sql, thực thi SQL, trả về kết quả JSON cho client, client render bảng hoặc chart tuỳ vào loại. Khi người dùng dowload thực ra là dowload data JSON dưới dạng CSV, Excel
4. Upload 1 file knowledge base mới, xem các file knowledge base được đã được upload, xoá 1 file knowlledge đã upload.
5. Quản lý thông tin người dùng, xem người dùng có đủ quyền truy cập đến datasource nào.

- Tôi đã có code base cho các router:
1. chat_router
2. kb_router
3. query_router
4. user_router

- Với các chức năng và router phía trên, hãy chỉnh sửa code sao cho phù hợp. Với các 5 tính năng mà tôi liệt kê hãy cho tôi bản cài đặt tiếp tục cài đặt của 5 tính năng trên, hãy cho tôi code thật và chạy được
