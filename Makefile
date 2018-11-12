TARGET=bdr3ao.pdf m1.pdf

all: $(TARGET)

bdr3ao.pdf:
	$(MAKE) -C BDR-Always-ON
	cp BDR-Always-ON/bdr3ao.pdf $@

m1.pdf:
	$(MAKE) -C M1
	cp M1/m1.pdf $@

clean:
	rm -f $(TARGET)
	$(MAKE) clean -C BDR-Always-ON
	$(MAKE) clean -C M1
