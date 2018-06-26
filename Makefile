build:
	# Copy python package
	python3 setup.py install

	# Copy main file
	cp ./aw_watcher_terminal/main.py ~/.local/bin/aw-watcher-terminal.py