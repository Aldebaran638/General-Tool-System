from docx import Document
from pathlib import Path


def docx_to_text(docx_path: str) -> str:
    """将 .docx 文件转换为纯文本。"""
    doc = Document(docx_path)
    lines = [para.text for para in doc.paragraphs]
    return "\n".join(lines)


if __name__ == "__main__":
    docx_path = "题目3.docx"

    if not Path(docx_path).exists():
        print(f"文件不存在：{docx_path}")
        exit(1)

    text = docx_to_text(docx_path)
    print(text)
