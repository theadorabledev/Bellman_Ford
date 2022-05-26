install:
	sudo apt install -y python3-pip
	pip3 install netifaces
	pip3 install pythonping
run:
	python3 Bellman_Ford.py
