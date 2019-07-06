DIA=main
#ww ha swap pmf-1 pmf-2 pmf-3 pmf-4 epf 2ep dcf

TARGET=bdr3ww-manual.pdf bdr3ww-spec.pdf

.PRECIOUS: $(patsubst %, cache/%.png, $(DIA))

target: $(TARGET)

ifeq ($(DEBUG),1)
GPPDEF = -DDEBUG
else
GPPDEF =
endif

bdr3ww-spec.pdf   : bdr3ww.md $(patsubst %, cache/%.png, $(DIA))
	gpp $(GPPDEF)               -T < $< >bdr3ww-spec.md
	2ndq-pandoc bdr3ww-spec.md

bdr3ww-manual.pdf : bdr3ww.md $(patsubst %, cache/%.png, $(DIA))
	gpp $(GPPDEF) -DUSER_MANUAL -T < $< >bdr3ww-manual.md
	2ndq-pandoc bdr3ww-manual.md

## generic rules

clean:
	rm -f cache/* \
		$(patsubst %.pdf, %.md,  $(TARGET)) \
		$(patsubst %.pdf, %.tex, $(TARGET)) \
		$(TARGET)

cache/%.pdf : cache/%.fig
	fig2dev -L pdf $< $@

cache/%.png :: %.dia
	dia -e $@ -t png --size x1600 $<

cache/%.pdf :: %.dia
	dia -e $@ -t pdf $<
