# LAS 2.0.5 zero-waveform fixture correction — 2026-09-21

This tests-only correction retains valid file-level descriptor and storage
records while testing a point whose waveform block is all zero. It changes four
fixtures and their names, preserves the 223-case denominator, and changes no
model-visible prompt/document bytes, reference implementation, or saved source.

## Public-contract basis and correction of earlier reporting

The supplied `prompt/docs/17-030r1-layout.txt`, lines 975–979, says descriptor
index zero means no waveform is associated with **this point**. The supplied
technical requirements, lines 155–168, permit an omitted point waveform object
and specify zero-valued wire fields when rendering it. Those statements do not
explicitly waive file-level records: the same supplied specification titles
both Waveform Packet Descriptor and Waveform Data Packets as required for point
formats 4, 5, 9 and 10 (around lines 1720 and 1768).

The former fixture removed every descriptor and packet record and cleared both
storage flags. Its acceptance requirement selected an interpretation not
unequivocally established by the whole supplied corpus. Earlier validation,
review notes and result summaries called its four failures implementation
defects. That classification is withdrawn. Original grades and commentary
remain preserved in their historical records; current publications must use
separate regrades and corrected editorial explanations.

The repaired fixture starts with the canonical valid file and omits only the
point's waveform object. Its encoder therefore changes only the 29-byte point
waveform region to zero. The descriptor, storage flag, internal EVLR, its
payload, and its header pointer remain valid. No supplied rule requires all
stored packets to have a point reference, and sample layout/padding are
explicitly opaque. Keeping one point avoids introducing ordering or additional
point-count dependencies merely to make stored packet bytes referenced.

Whether a waveform-capable format may omit all file-level descriptors and
storage when no point refers to them is now unscored, pending an explicit
public-input revision. The existing missing nonzero descriptor and referenced
packet-interval rejection tests remain unchanged.

## Independent observations

The four format cases still accept either omission of the decoded waveform
object or its complete seven-field zero representation. They require a real
point observation, reject nonzero or incomplete waveform data, and do not
repeat assertions on unrelated headers, metadata, point fields, or the response
envelope. A shared zero-association bug may fail all four formats; these are
format-layout observations, not four independent bugs. No new shared
prerequisite is added to the other 219 cases.

Independent static review checked the whole public corpus relevant to this
condition, preferred the single-point fixture, and requested both positive and
negative controls. The trusted encoder byte check confirms all four fixtures
differ from their canonical file only within the 29-byte waveform block.

## Validation

Ruff, formatting and strict Pyright pass for both changed test files. Every
assembled public-input hash across all 28 task/language combinations is unchanged.
The suite hash changes from `d280a8b50945a5e93f598b2f9d82055b6e4437b1a0ab5df2feac595070e3602b`
to `4a72c8692e429a56106af4f6aa5f5d5bba2513948770dafd862030a6855e5a23`. All collected cases are unique.

| Control | Passed / total | Focused four |
| --- | ---: | --- |
| baseline | 223/223 | 4/4 pass |
| explicit-zero-output | 223/223 | 4/4 pass |
| reject-index-zero | 219/223 | 0/4 pass |
| wrong-zero-field | 219/223 | 0/4 pass |
| unrelated-output-fields | 183/223 | 4/4 pass |
| strict-file-metadata | 223/223 | 4/4 pass |
| strict-file-metadata-prior | 219/223 | 0/4 pass |

The two intentional zero-waveform defects fail only the four named cases.
The unrelated-fields mutant fails 40 other observations while all four focused
cases pass. The strict-metadata control changes from 219/223 to 223/223 on the
same source, isolating the corrected fixture interpretation. Machine-readable
control evidence is in [LAS-2.0.5-controls.json](LAS-2.0.5-controls.json).

All execution uses one offline Docker grader at a time, pinned to
`sha256:9a4f1fe0219b50b94c4a7abeb8a48cedd6a9c17c1ab90d34cc4bb4d826a7c90c`.
The active Luna Rust generation was allowed to finish its original 2.0.4 grade
before the live suite changed. Controls and regrades use disposable copies of
all saved source files. Original raw results, source contents, tokens, costs
and generation metadata are retained; regrades make no additional model calls.

Local evidence is under `work/las-zero-waveform-followup/`: candidate and prior
suite snapshots, `candidate-plan.json`, `independent-candidate-review.json`,
`fixture-byte-validation.json`, complete reference mutant copies and patches,
control reports, and official per-submission regrade records. The four renamed
nodes have an explicit mapping in the plan; each of the other 219 identities
and outcomes must match exactly on every saved-source comparison.

## Saved submissions

The rubric is committed before official regrading. The 15 existing LAS rows
and the just-completed Luna Rust source will be processed one at a time, with
per-case comparison, editorial review, preserved historical publication/audit
chains, and a bounded-memory dashboard rebuild. This section will record the
measured results when that publication migration completes.
