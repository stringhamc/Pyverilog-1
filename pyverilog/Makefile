.PHONY: all
all:
	make -C ./vparser
	make -C ./dataflow
	make -C ./controlflow
	make -C ./ast_code_generator

.PHONY: clean
clean:
	make clean -C ./utils
	make clean -C ./vparser
	make clean -C ./dataflow
	make clean -C ./controlflow
	make clean -C ./ast_code_generator
	rm -rf *.pyc __pycache__ *.out parsetab.py *.html
