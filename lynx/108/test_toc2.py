from docx import Document
# from docx.enum.text import WD_STYLE_TYPE

# 打开 Word 文档
document = Document('result0.docx')

# 查找所有标题样式的段落
headings = []
for paragraph in document.paragraphs:
    if paragraph.style.name.startswith('Heading'):
        headings.append(paragraph)

# 打印目录
for i, heading in enumerate(headings):
    level = int(heading.style.name[-1])
    text = heading.text.strip()
    print('{}{}. {}'.format('    ' * (level-1), i+1, text))