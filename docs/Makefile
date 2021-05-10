# © Copyright EnterpriseDB UK Limited 2015-2021 - All rights reserved.

# Output: $PDFBUILDDIR/tpaexec.pdf

DOCDIR=$(shell pwd)
PDFBUILDDIR=${DOCDIR}/../pdf

images/bdr-simple.png: images/bdr-simple.dot
	circo -Tpng $< -o $@

images/m1.png: images/m1.dot
	dot -Tpng $< -o $@

tpaexec.pdf:
	mkdir -p "${PDFBUILDDIR}"
	ENABLE_PDF_EXPORT=1 mkdocs build -v -d "${PDFBUILDDIR}" -t material -f tpa.yml

all: images/bdr-simple.png images/m1.png tpaexec.pdf

clean:
	rm -rvf ${PDFBUILDDIR} images/bdr-simple.png images/m1.png


.PHONY: all clean $(SUBDIRS)
.DEFAULT_GOAL := all
