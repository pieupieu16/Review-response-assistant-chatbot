import os
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer


class CustomerReviewAnalyzer:
    def __init__(self, model_dir=None):
        # Thiết lập đường dẫn động (Dynamic Path) thay vì hardcode Google Drive
        if model_dir is None:
            # Tự động trỏ ra thư mục onnx_export ở ngoài cùng (cùng cấp với thư mục src)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_dir = os.path.join(current_dir, '..', 'onnx_export')

        print(f'Đang tải mô hình ONNX từ: {model_dir}...')

        if not os.path.exists(model_dir):
            raise FileNotFoundError(f'Không tìm thấy thư mục: {model_dir}')

        onnx_files = [f for f in os.listdir(model_dir) if f.endswith('.onnx')]
        if not onnx_files:
            raise FileNotFoundError(f'Không tìm thấy file .onnx nào trong {model_dir}')

        model_path = os.path.join(model_dir, onnx_files[0])
        self.session = ort.InferenceSession(model_path)

        # Load tokenizer
        source_tokenizer = 'xlm-roberta-base'
        print(f'Đang tải tokenizer từ {source_tokenizer}...')
        self.tokenizer = AutoTokenizer.from_pretrained(source_tokenizer, use_fast=False)
        self.input_names = [ipt.name for ipt in self.session.get_inputs()]
        self.max_length = 256

    def analyze_review(self, review_text):
        inputs = self.tokenizer(
            review_text,
            return_tensors='np',
            truncation=True,
            padding='max_length',
            max_length=self.max_length
        )

        onnx_inputs = {}
        for name in self.input_names:
            if name in inputs:
                token_ids = inputs[name].astype(np.int64)
                token_ids[token_ids >= 64000] = 3
                onnx_inputs[name] = token_ids

        outputs = self.session.run(None, onnx_inputs)
        raw_output = outputs[0]

        # Xử lý ma trận đầu ra (Process logits)
        if len(raw_output.shape) == 3:
            logits = raw_output[0, 0, :]
        elif len(raw_output.shape) == 2:
            logits = raw_output[0]
        else:
            logits = raw_output

        logits = logits[:3]

        # Tính toán xác suất bằng Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)

        pred_class = np.argmax(probs)
        weight = float(probs[pred_class])

        mapping = {0: 'Tiêu cực (Negative)', 1: 'Trung lập (Neutral)', 2: 'Tích cực (Positive)'}
        sentiment = mapping.get(int(pred_class), 'Không xác định')

        return {
            'review': review_text,
            'sentiment': sentiment,
            'weight': round(weight, 4)
        }


if __name__ == '__main__':
    try:
        analyzer = CustomerReviewAnalyzer()
        sample_review = 'Sản phẩm giao nhanh nhưng bị xước góc, shop xử lý lỗi trầy xước này sao đây?'
        res = analyzer.analyze_review(sample_review)

        print('\n[ Kết quả Phân tích từ Mô hình ONNX ]')
        print('-' * 40)
        print(f"Ý kiến (Review): '{res['review']}'")
        print(f" ➔ Cảm xúc (Sentiment): {res['sentiment']}")
        print(f" ➔ Độ tin cậy (Confidence score): {res['weight']}")
    except Exception as e:
        import traceback

        print(f'Lỗi thực thi (Execution error): {e}')
        traceback.print_exc()
