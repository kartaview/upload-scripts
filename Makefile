.PHONY: default pycodestyle clean

default: tags pycodestyle

tags: *.py
	ctags ./

pycodestyle:
	pycodestyle --max-line-length=100 ./

clean:
	rm tags
