#!/bin/bash
clear
echo "==========================================="
echo "   FB AUTOMATION AGENT - CONTROL PANEL   "
echo "==========================================="
echo "1. Đăng Quiz tự động (Từ Ảnh câu hỏi scale)"
echo "2. Đăng Ảnh tự tạo với AI (Từ Ảnh tự tạo)"
echo "3. Kiểm tra trạng thái Sheet"
echo "4. Thoát"
echo "==========================================="
read -p "Chọn tác vụ (1-4): " choice

case $choice in
    1)
        echo "🚀 Đang chạy luồng Quiz Tự Động..."
        npm start
        ;;
    2)
        echo "🤖 Đang chạy luồng Ảnh Tự Tạo (AI Analysis)..."
        npm run process-custom
        ;;
    3)
        echo "📊 Kiểm tra dữ liệu Ready..."
        node scripts/check_sheet.js
        ;;
    4)
        echo "Tạm biệt!"
        exit 0
        ;;
    *)
        echo "Lựa chọn không hợp lệ."
        ;;
esac
