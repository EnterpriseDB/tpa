
.PHONY = demo all dev-setup
build := build

all:

demo:
	ssh -to ForwardAgent=yes tpademo@tpa-demo -- cd /home/tpademo/tpa/TPA \; git pull

$(build):
	mkdir -p $(build)

dev-setup: $(build)/env ./node_modules $(build)/static $(build)/bundle

$(build)/env: $(build)
	virtualenv --no-site-packages $(build)/env

./node_modules: $(build)
	mkdir -p ./node_modules \
		&& npm install npm@latest \
		|| rmdir -f ./node_modules
