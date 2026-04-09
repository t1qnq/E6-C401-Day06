# Individual reflection — Hồ Hải Thuận (2A202600058)

## 1. Role
Feedback Loop + Learning Signal. Phụ trách thiết kế node 'handle_feedback' và 'feedback_learning'

## 2. Đóng góp cụ thể

- Thiết kế feedback loop dựa trên 4 bước chính:
  1. **Trích xuất dữ liệu**: Xác định action (upvote/downvote/correct), chuẩn hóa priority
  2. **Thu thập context**: Gom text từ teacher_note, extracted_text, notification title/content
  3. **Xác thực phản hồi**: Kiểm tra action hợp lệ và corrected_priority không rỗng
  4. **Lưu tín hiệu học tập**: Gửi signal đến feedback_learner với metadata (action, priority levels, category, scope)

- Kết quả: Dict chứa `feedback_recorded` (boolean) và `learning_signal` (string mô tả)
- Xử lý edge case: Feedback không hợp lệ trả về `{"feedback_recorded": False, "learning_signal": "no_valid_feedback"}`

## 3. Luồng Hoạt Động End-to-End

```
Người dùng Phản Hồi (UI gửi state dict)
    ↓
handle_feedback() node
    ├─ Chuẩn hóa priority (HIGH/MEDIUM/LOW)
    ├─ Tập hợp văn bản từ 4 nguồn
    ├─ Xác thực: action ∈ {upvote, downvote, correct} ∧ corrected_priority ≠ ""
    └─ Gọi feedback_learner.append_feedback_signal()
        ↓
    append_feedback_signal()
    ├─ Tạo safe_signal dict + timestamp
    └─ Ghi vào JSONL file (data/feedback/priority_feedback.jsonl)
        ↓
    maybe_rebuild()
    ├─ Kiểm tra: (now - last_rebuild_ts) ≥ 1800s?
    └─ Nếu YES → rebuild_learned_keywords()
        ├─ Đọc toàn bộ JSONL feedback
        ├─ Tokenize text, đếm frequency per level
        ├─ Lọc top-60 keywords per level
        └─ Lưu vào JSON (data/feedback/learned_keywords.json)
        
Kết quả: load_learned_keywords() returned {HIGH: set(), MEDIUM: set(), LOW: set()}
         → Dùng cho prioritizer trong vòng tiếp theo
```

## 4. SPEC mạnh/yếu (Cụ Thể Cho Features Này)
- **Mạnh nhất:** 
  - Feedback loop closure hoàn chỉnh: user input → learning signal → keyword updates → improved prioritization
  - JSONL format cho feedback log cho phép incremental append + dễ xử lý song song
  - Graceful degradation: system hoạt động bình thường ngay cả khi learned_keywords.json không tồn tại
  
- **Yếu nhất:** 
  - Tokenization từ đơn (không xử lý N-grams hay phrase-level keywords)
  - Không có weight decay: keywords cũ không bao giờ disappear, chỉ bị "chìm dưới" keywords mới
  - Rebuild timestamp không persist: sau khi process restart, timestamp reset → có thể rebuild lại ngay (chưa tối ưu)

## 5. Điều học được
- **Feedback Loop Complexity**: Nhìn ra rằng thiết kế feedback loop không chỉ là logic đơn giản. Phải cân nhắc:
  - Khi nào trigger rebuild (không quá thường xuyên)?
  - Làm sao lưu trữ để scale được khi feedback log to?
  - Làm sao handle edge cases (corrupt JSONL, missing fields)?
  
- **Cấu hình vs. Hard-coding**: Ban đầu định hard-code các thông số (min_frequency=2, rebuild_interval=1800). Nhưng khi integrate vào hệ thống lớn, _mỗi_ thông số lại cần tuning khác nhau tùy theo environment (dev/staging/prod). Lesson: config management từ đầu, không hard-code.

- **JSONL > JSON List**: Thử nghiệm lưu tất cả feedback vào một JSON array, nhưng khi append feedback thứ 1000 thì phải rewrite toàn bộ file. JSONL giải quyết bằng cách mỗi dòng = một record, append O(1) thay vì O(n).

## 6. Nếu làm lại
- Sẽ thêm unit tests cho `_normalize_priority()` và `_tokenize()` sớm hơn — hiện chỉ test end-to-end qua handle_feedback()
- Sẽ implement persistence cho `_last_rebuild_ts` vào `learned_keywords.json` metadata để tránh rebuild dư thừa sau restart
- Sẽ add logging (import logging) để debug khi rebuild không được trigger (có thể interval chưa đủ)
- Sẽ test với mock data lớn (10,000+ feedback entries) để verify performance của rebuild_learned_keywords()

## 7. AI giúp gì / AI sai gì (Cụ Thể Cho Features Này)
- **Giúp:** 
  - Claude giúp design `_normalize_priority()` robustness check — từ input bất kỳ → chỉ output valid values
  - ChatGPT gợi ý JSONL format cho feedback log — tôi ban đầu định dùng CSV, JSONL tốt hơn vì flexible columns
  
- **Sai/mislead:** 
  - Claude gợi ý thêm "user_id" và "session_id" vào feedback signal để track individual learner trends. Nghe hay nhưng scope creep — ban đầu chỉ cần global keyword learning, không cần perUser tracking. Dừng lại để tập trung vào core feature.

## 8. Key Files & Lines
- `services/prioritization/feedback_learning.py` — `FeedbackLearner` class (full implementation)
- `services/prioritization/rules.py` (hoặc handler file) — `handle_feedback()` function
- `config/prioritization_runtime.json` — config cho feedback learning parameters
- `data/feedback/priority_feedback.jsonl` — runtime feedback log
- `data/feedback/learned_keywords.json` — learned keywords dictionary (output của rebuild)

---

**Note:** Features này chủ yếu là foundation cho closed-loop learning. Giá trị thực hiện hiện (hackathon D5-D6) là **concept validation** — chứng minh rằng có thể capture feedback + extract keywords + rebuild. Production-grade enhancements (multi-threading rebuild, database backend thay JSONL, weight decay) có thể làm ở sprint tiếp theo.