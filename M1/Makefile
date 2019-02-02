DIA=ha 1b 2bl ppf-1 ppf-2 ppf-3 epf dcf dcf2 dcf3
TARGET=m1.pdf

.PRECIOUS: $(patsubst %, cache/%.png, $(DIA))

target: $(TARGET)

m1.pdf : m1.md $(patsubst %, cache/%.png, $(DIA))
	2ndq-pandoc $<

## generic rules

clean:
	rm -f cache/* $(TARGET) $(patsubst %.pdf, %.tex, $(TARGET))

cache/%.pdf : cache/%.fig
	fig2dev -L pdf $< $@

cache/%.png :: %.dia
	dia -e $@ -t png --size x1600 $<
