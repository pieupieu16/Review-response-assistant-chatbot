import os


def merge_project_files(project_path, output_file):
    # Các thư mục rác hoặc môi trường ảo cần bỏ qua (directories to exclude)
    exclude_dirs = {'.git', '__pycache__', 'venv', 'env', '.venv', 'node_modules', '.idea', '.vscode','data','data\raw'}

    # Các định dạng file chứa mã nguồn và cấu hình quan trọng (allowed extensions)
    # Bao gồm cả .sql cho database và .py cho các pipeline xử lý
    allowed_extensions = {'.py', '.sql', '.json', '.md', '.txt', '.yaml', '.yml', '.env.example'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        for root, dirs, files in os.walk(project_path):
            # Bỏ qua các thư mục đã định nghĩa trong exclude_dirs (ignore unneeded folders)
            dirs[:] = [d for d in dirs if d not in exclude_dirs]

            for file in files:
                if any(file.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, file)

                    # Ghi tiêu đề file (File header) với đường dẫn rõ ràng để dễ review
                    outfile.write(f"\n{'=' * 60}\n")
                    outfile.write(f"### File path: {file_path} ###\n")
                    outfile.write(f"{'=' * 60}\n\n")

                    # Đọc và ghi nội dung (Read and extract content)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read())
                            outfile.write("\n")
                    except Exception as e:
                        # Bắt lỗi nếu gặp file định dạng lạ không thể đọc dưới dạng text
                        outfile.write(f"# Lỗi không thể đọc file này (Error reading file): {e}\n")

    print(f"Hoàn tất quá trình gộp! (Merge completed!)\nToàn bộ source code đã được lưu vào: {output_file}")


if __name__ == "__main__":
    # Thư mục hiện tại (Current directory)
    PROJECT_DIR = "../"

    # Tên file đầu ra (Output file name)
    OUTPUT_FILE = "toan_bo_du_an_RAG.txt"

    merge_project_files(PROJECT_DIR, OUTPUT_FILE)
