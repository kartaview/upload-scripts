.PHONY: default pycodestyle clean docker help

default: help

help:
	@echo 'tags: Build ctags'
	@echo 'pycodestyle: run pycodestyle (pep8)'
	@echo 'docker: build docker containter'
	@echo 'clean: remove development and docker debris'

tags: *.py
	ctags ./

pycodestyle:
	pycodestyle --max-line-length=100 ./

clean:
	if [ -f tags ] ; then rm tags; fi
	if [ -f docker/requirements.txt ]; then rm docker/requirements.txt; fi

docker/requirements.txt:
	cp requirements.txt docker/requirements.txt

docker: docker/requirements.txt
	docker build -t osc-up docker
