# Failure independence and interpretation

The final cohort has **25 failed outcomes across 6,660 test executions**. Six
of twelve submissions pass all 555 tests. The standard scores remain raw
pytest pass fractions; they are not counts of independent capabilities or bugs.
The [machine-readable cluster record](failure-clusters.json) maps every remaining
failure to its run UID and test ID.

| Common failure mechanism | Failed outcomes | Submissions affected | Interpretation |
|---|---:|---|---|
| Tool-length controlled-point coordinates | 20 | C++ Low, Python High, Python Low, JavaScript Max | Five cases per submission: three G43 coordinate checks and two TLC/probe integration checks can share one coordinate-frame defect |
| Zero-duration dwell with a modal change | 3 | C++ Low, Python Low, JavaScript Low | G4 P0 suppresses a required concurrent modal-state delta; each is one focused trace case |
| Probe with turning spindle accepted | 1 | Rust Low | Explicit positive S500/M3 setup establishes the invalid probe condition |
| Probe starts inside the box and is accepted | 1 | Rust Low | The initial controlled point is explicitly within the box |

The TLC cases exercise useful offset-change and integration paths, but their
shared prerequisite means their five failures should not be presented as five
independent defects. No post-hoc weighting was applied to these models; the
cluster information accompanies the raw rubric scores. A fundamental inability
to parse a valid program, move an axis, or emit required observable output can
still affect multiple tests. The audit removes incidental shared assumptions
without claiming complete statistical independence.

This distinction mattered materially. The preliminary v3.2.1 regrade produced
133 failed outcomes; 108 were traced to missing spindle speed (66), missing
T selection before M6 (20), unsupported default/sparse-parameter membership (6),
a G20 no-op presented as a unit change (8), and unspecified raw-versus-effective
G92 offset serialization (8). The final fixture corrections remove those
assumptions. The same saved source is being measured throughout.

An independent adversarial control exposed a broader potential cascade: an
otherwise passing reference with the legally permitted final parameters={}
failed 36 preliminary cases. It passes all 555 corrected cases. The tests now
observe required positions, mandatory trace data, or parameter-file values;
corrupted-value controls still fail the relevant cases. Parameter-file formatting
also has a dedicated gate: a sorting defect fails that gate while six
persistence/value checks continue to measure their intended behavior.

The historical fixture repairs explain the higher scores. They also expose
**a ceiling limitation for this saved Astra cohort**: six perfect submissions and
all others above 98.9% leave little room to distinguish reasoning settings.
There is only one run per language/effort. These data do not support a reliable
Max/High/Low ranking or establish complete specification coverage.

Public phase two should separately settle EOF termination, implicit D, raw versus
effective G92 maps, spindle direction at S0, and explicit-Z/TLC wording before
new tests rely on those choices. Keep these unchanged-input regrades associated
with their original generation metadata even when a later public contract exists.
