I write academic papers in LaTeX, and every paper I submit gets
formatted through BibTeX. I give BibTeX three inputs: a database
of references (a `.bib` file), a style file provided by the
journal (a `.bst` file), and the list of citation keys my paper
actually uses. BibTeX produces the formatted reference list (a
`.bbl` file) that LaTeX pulls into the final document.

I'd like a command-line tool that does the same job the historic
BibTeX 0.99c binary does. When I feed it one of the canonical
reference styles (`plain.bst`, `alpha.bst`, `unsrt.bst`,
`abbrv.bst`) alongside a real `.bib` database, the `.bbl` your
tool writes should be the same reference list BibTeX would have
produced — same entries in the same order, same author-name
formatting, same line wrapping, same handling of `@string` macros
and `crossref` inheritance, same treatment of special characters
in titles. Another way to say this: if I swap your tool in for
BibTeX on my existing LaTeX workflow, my compiled PDFs should
look identical.

The documentation in `docs/authoritative/` contains Patashnik's
original sources — *BIBTEXing* (`btxdoc.tex`, the user guide),
*Designing BibTeX Styles* (`btxhak.tex`, the style-language
guide), the complete `bibtex.web` literate-Pascal source, and the
four reference styles themselves. Those are the authoritative
specification. `docs/summary.md` is a reading index I wrote to
help orient someone coming to BibTeX fresh; it's useful as a
starting point, but when it disagrees with the authoritative
sources, the authoritative sources govern.

I also want a structured JSON log summarizing what happened:
which entries were found, which macros were defined, and any
warnings BibTeX would have raised.
