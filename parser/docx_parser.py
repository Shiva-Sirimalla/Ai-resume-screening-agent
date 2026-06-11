from docx import Document

def extract_docx_text(file):

    doc = Document(file)

    text = []

    for para in doc.paragraphs:
        text.append(para.text)

    return "\n".join(text)
