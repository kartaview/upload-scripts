.PHONY: default ctags pycodestyle clean

default: ctags pycodestyle

ctags:
	ctags ./

pycodestyle:
	pycodestyle --max-line-length=100 ./

clean:
	rm tags
