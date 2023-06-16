import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

# 输入文本
text = "脾胃是人体中的重要消化器官。脾主运化水谷精微，胃主受纳消化。在中医理论中，脾胃是相互依存、相互作用的，两者合称为脾胃。脾胃的功能失调"

# 将文本转化为小写
text = text.lower()

# 分词
tokens = word_tokenize(text)

# 去除停用词
stop_words = set(stopwords.words('chinese'))
filtered_tokens = [token for token in tokens if token not in stop_words]

# 词干提取
stemmer = PorterStemmer()
stemmed_tokens = [stemmer.stem(token) for token in filtered_tokens]

# 寻找与脾、胃、脾胃有关系的主题词
related_words = []
for token in stemmed_tokens:
    if '脾' in token or '胃' in token or '脾胃' in token:
        related_words.append(token)

# 去除重复的主题词
related_words = list(set(related_words))

# 打印结果
print(related_words)