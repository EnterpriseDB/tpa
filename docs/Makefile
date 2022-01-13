# © Copyright EnterpriseDB UK Limited 2015-2022 - All rights reserved.

# Output: $PDFBUILDDIR/tpaexec.pdf

DOCDIR=$(shell pwd)
PDFBUILDDIR=${DOCDIR}/pdf

src/images/bdr-simple.png: src/images/bdr-simple.dot
	circo -Tpng $< -o $@

src/images/m1.png: src/images/m1.dot
	dot -Tpng $< -o $@

tpaexec.pdf:
	mkdir -p "${PDFBUILDDIR}"
	ENABLE_PDF_EXPORT=1 mkdocs build -v -d "${PDFBUILDDIR}" -t material -f tpa.yml

all: src/images/bdr-simple.png src/images/m1.png tpaexec.pdf

clean:
	rm -rvf ${PDFBUILDDIR} src/images/bdr-simple.png src/images/m1.png


.PHONY: all clean $(SUBDIRS)
.DEFAULT_GOAL := all
