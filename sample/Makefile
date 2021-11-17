test:
	dnstemple *.IN
	for i in *.TEST; do \
	  if ! cmp $$i $$(basename $$i .TEST).OUT; then \
	    echo; \
	    diff -u $$i $$(basename $$i .TEST).OUT; \
	    exit 1; \
	  fi; \
	done

.PHONE: test
