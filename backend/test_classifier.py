from services.ml_engine import DocumentClassifier

classifier = DocumentClassifier()
print("Classifier initialized.")
res = classifier.classify("Consolidated statements of income... Gross profit increased...")
print(f"Classification result: {res}")
