
help:
	@grep -B1 -E "^[a-zA-Z0-9_-]+\:([^\=]|$$)" Makefile \
	 | grep -v -- -- \
	 | sed 'N;s/\n/###/' \
	 | sed -n 's/^#: \(.*\)###\(.*\):.*/\2###\1/p' \
	 | column -t  -s '###'

#: install python dependencies
deps:
	pi install

#: create git tag with the version number in poetry
release:
	git tag `pi version`
	git push origin `pi version`

#: re-create git tag with the version number in poetry
release-again:
	git tag -d `pi version`
	git push -d origin `pi version`
	git tag `pi version`
	git push origin `pi version`
