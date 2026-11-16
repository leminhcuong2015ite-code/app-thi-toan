import re

LEVEL_MAP = {
    "N": "Nhận biết",
    "H": "Thông hiểu",
    "V": "Vận dụng",
    "C": "Vận dụng cao",
    "NB": "Nhận biết",
    "TH": "Thông hiểu",
    "VD": "Vận dụng",
    "VDC": "Vận dụng cao"
}

KNTT_DATA = {
    "6": {
        "chapters": {
            "C1": "Chương I. Tập hợp các số tự nhiên",
            "C2": "Chương II. Tính chia hết trong tập hợp các số tự nhiên",
            "C3": "Chương III. Số nguyên",
            "C4": "Chương IV. Một số hình phẳng trong thực tiễn",
            "C5": "Chương V. Tính đối xứng của hình phẳng trong tự nhiên",
            "C6": "Chương VI. Phân số",
            "C7": "Chương VII. Số thập phân",
            "C8": "Chương VIII. Những hình hình học cơ bản",
            "C9": "Chương IX. Dữ liệu và xác suất thực nghiệm"
        },
        "lessons": {
            "B1": ("C1", "Bài 1. Tập hợp"),
            "B2": ("C1", "Bài 2. Cách ghi số tự nhiên"),
            "B3": ("C1", "Bài 3. Thứ tự trong tập hợp các số tự nhiên"),
            "B4": ("C1", "Bài 4. Phép cộng và phép trừ số tự nhiên"),
            "B5": ("C1", "Bài 5. Phép nhân và phép chia số tự nhiên"),
            "B6": ("C1", "Bài 6. Lũy thừa với số mũ tự nhiên"),
            "B7": ("C1", "Bài 7. Thứ tự thực hiện các phép tính"),
            "B8": ("C2", "Bài 8. Quan hệ chia hết và tính chất"),
            "B9": ("C2", "Bài 9. Dấu hiệu chia hết"),
            "B10": ("C2", "Bài 10. Số nguyên tố"),
            "B11": ("C2", "Bài 11. Ước chung. Ước chung lớn nhất"),
            "B12": ("C2", "Bài 12. Bội chung. Bội chung nhỏ nhất"),
            "B13": ("C3", "Bài 13. Tập hợp các số nguyên"),
            "B14": ("C3", "Bài 14. Phép cộng và phép trừ số nguyên"),
            "B15": ("C3", "Bài 15. Quy tắc dấu ngoặc"),
            "B16": ("C3", "Bài 16. Phép nhân số nguyên"),
            "B17": ("C3", "Bài 17. Phép chia hết. Ước và bội của một số nguyên"),
            "B18": ("C4", "Bài 18. Hình tam giác đều. Hình vuông. Hình lục giác đều"),
            "B19": ("C4", "Bài 19. Hình chữ nhật. Hình thoi. Hình bình hành. Hình thang cân"),
            "B20": ("C4", "Bài 20. Chu vi và diện tích của một số tứ giác đã học"),
            "B21": ("C5", "Bài 21. Hình có trục đối xứng"),
            "B22": ("C5", "Bài 22. Hình có tâm đối xứng"),
            "B23": ("C6", "Bài 23. Mở rộng phân số. Phân số bằng nhau"),
            "B24": ("C6", "Bài 24. So sánh phân số. Hỗn số dương"),
            "B25": ("C6", "Bài 25. Phép cộng và phép trừ phân số"),
            "B26": ("C6", "Bài 26. Phép nhân và phép chia phân số"),
            "B27": ("C6", "Bài 27. Hai bài toán về phân số"),
            "B28": ("C7", "Bài 28. Số thập phân"),
            "B29": ("C7", "Bài 29. Tính toán với số thập phân"),
            "B30": ("C7", "Bài 30. Làm tròn và ước lượng"),
            "B31": ("C7", "Bài 31. Một số bài toán về tỉ số và tỉ số phần trăm"),
            "B32": ("C8", "Bài 32. Điểm và đường thẳng"),
            "B33": ("C8", "Bài 33. Điểm nằm giữa hai điểm. Tia"),
            "B34": ("C8", "Bài 34. Đoạn thẳng. Độ dài đoạn thẳng"),
            "B35": ("C8", "Bài 35. Trung điểm của đoạn thẳng"),
            "B36": ("C8", "Bài 36. Góc"),
            "B37": ("C8", "Bài 37. Số đo góc"),
            "B38": ("C9", "Bài 38. Dữ liệu và thu thập dữ liệu"),
            "B39": ("C9", "Bài 39. Bảng thống kê và biểu đồ tranh"),
            "B40": ("C9", "Bài 40. Biểu đồ cột"),
            "B41": ("C9", "Bài 41. Biểu đồ cột kép"),
            "B42": ("C9", "Bài 42. Kết quả có thể và sự kiện trong trò chơi, thí nghiệm"),
            "B43": ("C9", "Bài 43. Xác suất thực nghiệm")
        }
    },
    "7": {
        "chapters": {
            "C1": "Chương I. Số hữu tỉ",
            "C2": "Chương II. Số thực",
            "C3": "Chương III. Góc và đường thẳng song song",
            "C4": "Chương IV. Tam giác bằng nhau",
            "C5": "Chương V. Thu thập và biểu diễn dữ liệu",
            "C6": "Chương VI. Tỉ lệ thức và đại lượng tỉ lệ",
            "C7": "Chương VII. Biểu thức đại số và đa thức một biến",
            "C8": "Chương VIII. Làm quen với biến cố và xác suất của biến cố",
            "C9": "Chương IX. Quan hệ giữa các yếu tố trong một tam giác",
            "C10": "Chương X. Một số hình khối trong thực tiễn"
        },
        "lessons": {
            "B1": ("C1", "Bài 1. Tập hợp các số hữu tỉ"),
            "B2": ("C1", "Bài 2. Cộng, trừ, nhân, chia số hữu tỉ"),
            "B3": ("C1", "Bài 3. Lũy thừa với số mũ tự nhiên của một số hữu tỉ"),
            "B4": ("C1", "Bài 4. Thứ tự thực hiện các phép tính. Quy tắc chuyển vế"),
            "B5": ("C2", "Bài 5. Làm quen với số thập phân vô hạn tuần hoàn"),
            "B6": ("C2", "Bài 6. Số vô tỉ. Căn bậc hai số học"),
            "B7": ("C2", "Bài 7. Tập hợp các số thực"),
            "B8": ("C3", "Bài 8. Góc ở vị trí đặc biệt. Tia phân giác của một góc"),
            "B9": ("C3", "Bài 9. Hai đường thẳng song song và dấu hiệu nhận biết"),
            "B10": ("C3", "Bài 10. Tiên đề Euclid. Tính chất của hai đường thẳng song song"),
            "B11": ("C3", "Bài 11. Định lí và chứng minh định lí"),
            "B12": ("C4", "Bài 12. Tổng các góc trong một tam giác"),
            "B13": ("C4", "Bài 13. Hai tam giác bằng nhau. Trường hợp bằng nhau thứ nhất"),
            "B14": ("C4", "Bài 14. Trường hợp bằng nhau thứ hai và thứ ba của tam giác"),
            "B15": ("C4", "Bài 15. Các trường hợp bằng nhau của tam giác vuông"),
            "B16": ("C4", "Bài 16. Tam giác cân. Đường trung trực của đoạn thẳng"),
            "B17": ("C5", "Bài 17. Thu thập và phân loại dữ liệu"),
            "B18": ("C5", "Bài 18. Biểu đồ hình quạt tròn"),
            "B19": ("C5", "Bài 19. Biểu đồ đoạn thẳng"),
            "B20": ("C6", "Bài 20. Tỉ lệ thức"),
            "B21": ("C6", "Bài 21. Tính chất của dãy tỉ số bằng nhau"),
            "B22": ("C6", "Bài 22. Đại lượng tỉ lệ thuận"),
            "B23": ("C6", "Bài 23. Đại lượng tỉ lệ nghịch"),
            "B24": ("C7", "Bài 24. Biểu thức đại số"),
            "B25": ("C7", "Bài 25. Đa thức một biến"),
            "B26": ("C7", "Bài 26. Phép cộng và phép trừ đa thức một biến"),
            "B27": ("C7", "Bài 27. Phép nhân đa thức một biến"),
            "B28": ("C7", "Bài 28. Phép chia đa thức một biến"),
            "B29": ("C8", "Bài 29. Làm quen với biến cố"),
            "B30": ("C8", "Bài 30. Làm quen với xác suất của biến cố"),
            "B31": ("C9", "Bài 31. Quan hệ giữa góc và cạnh đối diện trong một tam giác"),
            "B32": ("C9", "Bài 32. Quan hệ giữa đường vuông góc và đường xiên"),
            "B33": ("C9", "Bài 33. Quan hệ giữa ba cạnh của một tam giác"),
            "B34": ("C9", "Bài 34. Sự đồng quy của ba đường trung tuyến, ba đường phân giác"),
            "B35": ("C9", "Bài 35. Sự đồng quy của ba đường trung trực, ba đường cao"),
            "B36": ("C10", "Bài 36. Hình hộp chữ nhật và hình lập phương"),
            "B37": ("C10", "Bài 37. Hình lăng trụ đứng tam giác và hình lăng trụ đứng tứ giác")
        }
    },
    "8": {
        "chapters": {
            "C1": "Chương I. Đa thức",
            "C2": "Chương II. Hằng đẳng thức đáng nhớ và ứng dụng",
            "C3": "Chương III. Tứ giác",
            "C4": "Chương IV. Định lí Thalès",
            "C5": "Chương V. Dữ liệu và biểu đồ",
            "C6": "Chương VI. Phân thức đại số",
            "C7": "Chương VII. Phương trình bậc nhất và hàm số bậc nhất",
            "C8": "Chương VIII. Mở đầu về tính xác suất của biến cố",
            "C9": "Chương IX. Tam giác đồng dạng",
            "C10": "Chương X. Một số hình khối trong thực tiễn"
        },
        "lessons": {
            "B1": ("C1", "Bài 1. Đơn thức"),
            "B2": ("C1", "Bài 2. Đa thức"),
            "B3": ("C1", "Bài 3. Phép cộng và phép trừ đa thức"),
            "B4": ("C1", "Bài 4. Phép nhân đa thức"),
            "B5": ("C1", "Bài 5. Phép chia đa thức cho đơn thức"),
            "B6": ("C2", "Bài 6. Hiệu hai bình phương. Bình phương của một tổng hay một hiệu"),
            "B7": ("C2", "Bài 7. Lập phương của một tổng. Lập phương của một hiệu"),
            "B8": ("C2", "Bài 8. Tổng và hiệu hai lập phương"),
            "B9": ("C2", "Bài 9. Phân tích đa thức thành nhân tử"),
            "B10": ("C3", "Bài 10. Tứ giác"),
            "B11": ("C3", "Bài 11. Hình thang cân"),
            "B12": ("C3", "Bài 12. Hình bình hành"),
            "B13": ("C3", "Bài 13. Hình chữ nhật"),
            "B14": ("C3", "Bài 14. Hình thoi và hình vuông"),
            "B15": ("C4", "Bài 15. Định lí Thalès trong tam giác"),
            "B16": ("C4", "Bài 16. Đường trung bình của tam giác"),
            "B17": ("C4", "Bài 17. Tính chất đường phân giác của tam giác"),
            "B18": ("C5", "Bài 18. Thu thập và phân loại dữ liệu"),
            "B19": ("C5", "Bài 19. Biểu diễn dữ liệu bằng bảng, biểu đồ"),
            "B20": ("C5", "Bài 20. Phân tích số liệu thống kê dựa vào biểu đồ"),
            "B21": ("C6", "Bài 21. Phân thức đại số"),
            "B22": ("C6", "Bài 22. Tính chất cơ bản của phân thức đại số"),
            "B23": ("C6", "Bài 23. Phép cộng và phép trừ phân thức đại số"),
            "B24": ("C6", "Bài 24. Phép nhân và phép chia phân thức đại số"),
            "B25": ("C7", "Bài 25. Phương trình bậc nhất một ẩn"),
            "B26": ("C7", "Bài 26. Giải bài toán bằng cách lập phương trình"),
            "B27": ("C7", "Bài 27. Khái niệm hàm số và đồ thị của hàm số"),
            "B28": ("C7", "Bài 28. Hàm số bậc nhất và đồ thị của hàm số bậc nhất"),
            "B29": ("C7", "Bài 29. Hệ số góc của đường thẳng"),
            "B30": ("C8", "Bài 30. Kết quả có thể và kết quả thuận lợi"),
            "B31": ("C8", "Bài 31. Cách tính xác suất của biến cố bằng tỉ số"),
            "B32": ("C8", "Bài 32. Mối liên hệ giữa xác suất thực nghiệm với xác suất và ứng dụng"),
            "B33": ("C9", "Bài 33. Hai tam giác đồng dạng"),
            "B34": ("C9", "Bài 34. Ba trường hợp đồng dạng của hai tam giác"),
            "B35": ("C9", "Bài 35. Định lí Pythagore và ứng dụng"),
            "B36": ("C9", "Bài 36. Các trường hợp đồng dạng của hai tam giác vuông"),
            "B37": ("C9", "Bài 37. Hình đồng dạng"),
            "B38": ("C10", "Bài 38. Hình chóp tam giác đều"),
            "B39": ("C10", "Bài 39. Hình chóp tứ giác đều")
        }
    },
    "9": {
        "chapters": {
            "C1": "Chương I. Phương trình và hệ hai phương trình bậc nhất hai ẩn",
            "C2": "Chương II. Phương trình và bất phương trình bậc nhất một ẩn",
            "C3": "Chương III. Căn bậc hai và căn bậc ba",
            "C4": "Chương IV. Hệ thức lượng trong tam giác vuông",
            "C5": "Chương V. Đường tròn",
            "C6": "Chương VI. Hàm số y = ax^2 và phương trình bậc hai một ẩn",
            "C7": "Chương VII. Tần số và tần số tương đối",
            "C8": "Chương VIII. Xác suất của biến cố trong một số mô hình xác suất đơn giản",
            "C9": "Chương IX. Đường tròn ngoại tiếp và đường tròn nội tiếp",
            "C10": "Chương X. Một số hình khối trong thực tiễn"
        },
        "lessons": {
            "B1": ("C1", "Bài 1. Khái niệm phương trình và hệ hai phương trình bậc nhất hai ẩn"),
            "B2": ("C1", "Bài 2. Giải hệ hai phương trình bậc nhất hai ẩn"),
            "B3": ("C1", "Bài 3. Giải bài toán bằng cách lập hệ phương trình"),
            "B4": ("C2", "Bài 4. Phương trình quy về phương trình bậc nhất một ẩn"),
            "B5": ("C2", "Bài 5. Bất đẳng thức và tính chất"),
            "B6": ("C2", "Bài 6. Bất phương trình bậc nhất một ẩn"),
            "B7": ("C3", "Bài 7. Căn bậc hai và căn thức bậc hai"),
            "B8": ("C3", "Bài 8. Khai căn bậc hai với phép nhân và phép chia"),
            "B9": ("C3", "Bài 9. Biến đổi đơn giản và rút gọn biểu thức chứa căn thức bậc hai"),
            "B10": ("C3", "Bài 10. Căn bậc ba và căn thức bậc ba"),
            "B11": ("C4", "Bài 11. Tỉ số lượng giác của góc nhọn"),
            "B12": ("C4", "Bài 12. Một số hệ thức giữa cạnh, góc trong tam giác vuông và ứng dụng"),
            "B13": ("C5", "Bài 13. Mở đầu về đường tròn"),
            "B14": ("C5", "Bài 14. Cung và dây của một đường tròn"),
            "B15": ("C5", "Bài 15. Độ dài của cung tròn. Diện tích hình quạt tròn và hình vành khuyên"),
            "B16": ("C5", "Bài 16. Vị trí tương đối của đường thẳng và đường tròn"),
            "B17": ("C5", "Bài 17. Vị trí tương đối của hai đường tròn"),
            "B18": ("C6", "Bài 18. Hàm số y = ax^2 (a khác 0)"),
            "B19": ("C6", "Bài 19. Phương trình bậc hai một ẩn"),
            "B20": ("C6", "Bài 20. Định lí Viète và ứng dụng"),
            "B21": ("C6", "Bài 21. Giải bài toán bằng cách lập phương trình"),
            "B22": ("C7", "Bài 22. Bảng tần số và biểu đồ tần số"),
            "B23": ("C7", "Bài 23. Bảng tần số tương đối và biểu đồ tần số tương đối"),
            "B24": ("C7", "Bài 24. Bảng tần số, tần số tương đối ghép nhóm và biểu đồ"),
            "B25": ("C8", "Bài 25. Phép thử ngẫu nhiên và không gian mẫu"),
            "B26": ("C8", "Bài 26. Xác suất của biến cố liên quan tới phép thử"),
            "B27": ("C9", "Bài 27. Góc nội tiếp"),
            "B28": ("C9", "Bài 28. Đường tròn ngoại tiếp và đường tròn nội tiếp của một tam giác"),
            "B29": ("C9", "Bài 29. Tứ giác nội tiếp"),
            "B30": ("C9", "Bài 30. Đa giác đều"),
            "B31": ("C10", "Bài 31. Hình trụ và hình nón"),
            "B32": ("C10", "Bài 32. Hình cầu")
        }
    },
    "10": {
        "chapters": {
            "C1": "Chương I. Mệnh đề và tập hợp",
            "C2": "Chương II. Bất phương trình và hệ bất phương trình bậc nhất hai ẩn",
            "C3": "Chương III. Hệ thức lượng trong tam giác",
            "C4": "Chương IV. Vectơ",
            "C5": "Chương V. Các số đặc trưng của mẫu số liệu không ghép nhóm",
            "C6": "Chương VI. Hàm số, đồ thị và ứng dụng",
            "C7": "Chương VII. Phương pháp tọa độ trong mặt phẳng",
            "C8": "Chương VIII. Đại số tổ hợp",
            "C9": "Chương IX. Tính xác suất theo định nghĩa cổ điển"
        },
        "lessons": {
            "B1": ("C1", "Bài 1. Mệnh đề"),
            "B2": ("C1", "Bài 2. Tập hợp và các phép toán trên tập hợp"),
            "B3": ("C2", "Bài 3. Bất phương trình bậc nhất hai ẩn"),
            "B4": ("C2", "Bài 4. Hệ bất phương trình bậc nhất hai ẩn"),
            "B5": ("C3", "Bài 5. Giá trị lượng giác của một góc từ 0 đến 180 độ"),
            "B6": ("C3", "Bài 6. Hệ thức lượng trong tam giác"),
            "B7": ("C4", "Bài 7. Các khái niệm mở đầu"),
            "B8": ("C4", "Bài 8. Tổng và hiệu của hai vectơ"),
            "B9": ("C4", "Bài 9. Tích của một vectơ với một số"),
            "B10": ("C4", "Bài 10. Vectơ trong mặt phẳng tọa độ"),
            "B11": ("C4", "Bài 11. Tích vô hướng của hai vectơ"),
            "B12": ("C5", "Bài 12. Số gần đúng và sai số"),
            "B13": ("C5", "Bài 13. Các số đặc trưng đo xu thế trung tâm"),
            "B14": ("C5", "Bài 14. Các số đặc trưng đo độ phân tán"),
            "B15": ("C6", "Bài 15. Hàm số"),
            "B16": ("C6", "Bài 16. Hàm số bậc hai"),
            "B17": ("C6", "Bài 17. Dấu của tam thức bậc hai"),
            "B18": ("C6", "Bài 18. Phương trình quy về phương trình bậc hai"),
            "B19": ("C7", "Bài 19. Phương trình đường thẳng"),
            "B20": ("C7", "Bài 20. Vị trí tương đối giữa hai đường thẳng. Góc và khoảng cách"),
            "B21": ("C7", "Bài 21. Đường tròn trong mặt phẳng tọa độ"),
            "B22": ("C7", "Bài 22. Ba đường conic"),
            "B23": ("C8", "Bài 23. Quy tắc đếm"),
            "B24": ("C8", "Bài 24. Hoán vị, chỉnh hợp và tổ hợp"),
            "B25": ("C8", "Bài 25. Nhị thức Newton"),
            "B26": ("C9", "Bài 26. Biến cố và định nghĩa cổ điển của xác suất"),
            "B27": ("C9", "Bài 27. Thực hành tính xác suất theo định nghĩa cổ điển")
        }
    },
    "11": {
        "chapters": {
            "C1": "Chương I. Hàm số lượng giác và phương trình lượng giác",
            "C2": "Chương II. Dãy số. Cấp số cộng và cấp số nhân",
            "C3": "Chương III. Các số đặc trưng đo xu thế trung tâm của mẫu số liệu ghép nhóm",
            "C4": "Chương IV. Quan hệ song song trong không gian",
            "C5": "Chương V. Giới hạn. Hàm số liên tục",
            "C6": "Chương VI. Hàm số mũ và hàm số lôgarit",
            "C7": "Chương VII. Quan hệ vuông góc trong không gian",
            "C8": "Chương VIII. Các quy tắc tính xác suất",
            "C9": "Chương IX. Đạo hàm"
        },
        "lessons": {
            "B1": ("C1", "Bài 1. Giá trị lượng giác của góc lượng giác"),
            "B2": ("C1", "Bài 2. Công thức lượng giác"),
            "B3": ("C1", "Bài 3. Hàm số lượng giác"),
            "B4": ("C1", "Bài 4. Phương trình lượng giác cơ bản"),
            "B5": ("C2", "Bài 5. Dãy số"),
            "B6": ("C2", "Bài 6. Cấp số cộng"),
            "B7": ("C2", "Bài 7. Cấp số nhân"),
            "B8": ("C3", "Bài 8. Mẫu số liệu ghép nhóm"),
            "B9": ("C3", "Bài 9. Các số đặc trưng đo xu thế trung tâm"),
            "B10": ("C4", "Bài 10. Đường thẳng và mặt phẳng trong không gian"),
            "B11": ("C4", "Bài 11. Hai đường thẳng song song"),
            "B12": ("C4", "Bài 12. Đường thẳng và mặt phẳng song song"),
            "B13": ("C4", "Bài 13. Hai mặt phẳng song song"),
            "B14": ("C4", "Bài 14. Phép chiếu song song"),
            "B15": ("C5", "Bài 15. Giới hạn của dãy số"),
            "B16": ("C5", "Bài 16. Giới hạn của hàm số"),
            "B17": ("C5", "Bài 17. Hàm số liên tục"),
            "B18": ("C6", "Bài 18. Lũy thừa với số mũ thực"),
            "B19": ("C6", "Bài 19. Lôgarit"),
            "B20": ("C6", "Bài 20. Hàm số mũ và hàm số lôgarit"),
            "B21": ("C6", "Bài 21. Phương trình, bất phương trình mũ và lôgarit"),
            "B22": ("C7", "Bài 22. Hai đường thẳng vuông góc"),
            "B23": ("C7", "Bài 23. Đường thẳng vuông góc với mặt phẳng"),
            "B24": ("C7", "Bài 24. Phép chiếu vuông góc. Góc giữa đường thẳng và mặt phẳng"),
            "B25": ("C7", "Bài 25. Hai mặt phẳng vuông góc"),
            "B26": ("C7", "Bài 26. Khoảng cách"),
            "B27": ("C7", "Bài 27. Thể tích"),
            "B28": ("C8", "Bài 28. Biến cố hợp, biến cố giao, biến cố độc lập"),
            "B29": ("C8", "Bài 29. Công thức cộng xác suất"),
            "B30": ("C8", "Bài 30. Công thức nhân xác suất cho hai biến cố độc lập"),
            "B31": ("C9", "Bài 31. Định nghĩa và ý nghĩa của đạo hàm"),
            "B32": ("C9", "Bài 32. Các quy tắc tính đạo hàm"),
            "B33": ("C9", "Bài 33. Đạo hàm cấp hai")
        }
    },
    "12": {
        "chapters": {
            "C1": "Chương I. Ứng dụng đạo hàm để khảo sát và vẽ đồ thị hàm số",
            "C2": "Chương II. Vectơ và hệ trục tọa độ trong không gian",
            "C3": "Chương III. Các số đặc trưng đo mức độ phân tán của mẫu số liệu ghép nhóm",
            "C4": "Chương IV. Nguyên hàm và tích phân",
            "C5": "Chương V. Phương pháp tọa độ trong không gian",
            "C6": "Chương VI. Xác suất có điều kiện"
        },
        "lessons": {
            "B1": ("C1", "Bài 1. Tính đơn điệu và cực trị của hàm số"),
            "B2": ("C1", "Bài 2. Giá trị lớn nhất và giá trị nhỏ nhất của hàm số"),
            "B3": ("C1", "Bài 3. Đường tiệm cận của đồ thị hàm số"),
            "B4": ("C1", "Bài 4. Khảo sát sự biến thiên và vẽ đồ thị của hàm số"),
            "B5": ("C1", "Bài 5. Ứng dụng đạo hàm để giải quyết một số vấn đề liên quan đến thực tiễn"),
            "B6": ("C2", "Bài 6. Vectơ trong không gian"),
            "B7": ("C2", "Bài 7. Hệ trục tọa độ trong không gian"),
            "B8": ("C2", "Bài 8. Biểu thức tọa độ của các phép toán vectơ"),
            "B9": ("C3", "Bài 9. Khoảng biến thiên và khoảng tứ phân vị"),
            "B10": ("C3", "Bài 10. Phương sai và độ lệch chuẩn"),
            "B11": ("C4", "Bài 11. Nguyên hàm"),
            "B12": ("C4", "Bài 12. Tích phân"),
            "B13": ("C4", "Bài 13. Ứng dụng hình học của tích phân"),
            "B14": ("C5", "Bài 14. Phương trình mặt phẳng"),
            "B15": ("C5", "Bài 15. Phương trình đường thẳng trong không gian"),
            "B16": ("C5", "Bài 16. Công thức tính góc trong không gian"),
            "B17": ("C5", "Bài 17. Phương trình mặt cầu"),
            "B18": ("C6", "Bài 18. Xác suất có điều kiện"),
            "B19": ("C6", "Bài 19. Công thức xác suất toàn phần và công thức Bayes")
        }
    }
}


def decode_kntt_tag(header_str, default_grade="12"):
    """Giải mã thẻ %[12-C4-B11-V] hoặc %[12-B11-V] thành thông tin chi tiết"""
    if not header_str:
        return None
    m = re.search(
        r'(\d{1,2})\s*-\s*(?:(C\d{1,2})\s*-\s*)?(B\d{1,2})\s*-\s*(VDC|VD|TH|NB|[NHVC])',
        header_str,
        re.IGNORECASE
    )
    if not m:
        return None

    g_raw = str(int(m.group(1)))
    c_raw = m.group(2).upper() if m.group(2) else None
    b_raw = m.group(3).upper()
    lvl_raw = m.group(4).upper()

    lvl_code = {"NB": "N", "TH": "H", "VD": "V", "VDC": "C"}.get(lvl_raw, lvl_raw)
    lvl_name = LEVEL_MAP.get(lvl_code, "Nhận biết")

    g_data = KNTT_DATA.get(g_raw, {})
    lessons = g_data.get("lessons", {})
    chapters = g_data.get("chapters", {})

    if b_raw in lessons:
        mapped_c, lesson_name = lessons[b_raw]
        c_code = c_raw if c_raw else mapped_c
    else:
        c_code = c_raw if c_raw else "C1"
        lesson_name = f"Bài {b_raw[1:]}"

    chapter_name = chapters.get(c_code, f"Chương {c_code[1:]}")
    return {
        "tag_id": f"{g_raw}-{c_code}-{b_raw}-{lvl_code}",
        "grade": g_raw,
        "chapter_code": c_code,
        "chapter_name": chapter_name,
        "lesson_code": b_raw,
        "lesson_name": lesson_name,
        "level_code": lvl_code,
        "level_name": lvl_name
    }