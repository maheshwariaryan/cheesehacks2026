from services.ml_engine import DocumentClassifier
classifier = DocumentClassifier()
print(classifier.classify("Consolidated statements of income... Gross profit increased..."))
