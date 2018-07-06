
pip_install_args := . --upgrade -r requirements.txt

ifdef DEV
pip_install_args := --editable $(pip_install_args)
endif

build:
	pip3 install $(pip_install_args)

package:
	pip3 install . --upgrade

test:
	python3 ./aw_watcher_terminal/test/test.py