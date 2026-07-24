Ship the Kate syntax file in the package and expose its install path

Users installing pandoc-allium outside of a checkout of this repo (e.g.
via `pip install`, the way pandoc-plantuml-filter is distributed) had no
way to get syntax highlighting: the wheel never actually included
`syntax/allium.xml`, and the README's `--syntax-definition` instructions
only worked when run from this source tree, since they hardcoded a
repo-relative path. This packages the syntax file properly and adds
`pandoc-allium --syntax-path` so any install method (pipenv, pip, an
editable checkout) can locate it, clearing the way to publish this to
PyPI.
