DIST_DIR := dist

default: clean compile-agent sdist

clean:
	rm -rf $(DIST_DIR)/*

compile-agent:
	cd agent && npm run build

sdist:
	python3 setup.py sdist

testupload:
	twine upload dist/* -r testpypi

upload:
	twine upload dist/*
