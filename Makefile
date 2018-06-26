build:
	# Copy python package
	rm -r /home/a-a/.local/lib/python3.6/site-packages/aw_watcher_terminal
	cp -r ./aw_watcher_terminal /home/a-a/.local/lib/python3.6/site-packages/aw_watcher_terminal

	# Copy main file
	cp ./aw_watcher_terminal/main.py ~/.local/bin/aw-watcher-terminal.py