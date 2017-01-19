
.PHONY = demo all dev-setup
build := build

all:

demo:
	ssh -to ForwardAgent=yes tpademo@tpademo -- cd /home/tpademo/tpa/TPA \; git pull

$(build):
	mkdir -p $(build)

dev-setup: $(build)/env $(build)/node_modules $(build)/static $(build)/bundle

$(build)/env: $(build)
	virtualenv --no-site-packages $(build)/env

$(build)/node_modules: $(build)
	mkdir -p $(build)/node_modules \
		&& npm -g --prefix $(build)/node_modules install npm@latest \
		|| rmdir -f $(build)/node_modules
