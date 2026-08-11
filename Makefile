.PHONY: all resumes validate clean

all: resumes validate

resumes:
	./scripts/build-all.sh

validate:
	python3 ./scripts/validate-pdfs.py

clean:
	./scripts/build-all.sh --clean

