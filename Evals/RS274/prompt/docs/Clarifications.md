# RS274 Clarifications

This document records disambiguations of `RS274NGC.md` where the spec text
admits multiple defensible readings. Each item is a normative rule for
this eval; agents should treat these on equal footing with the spec.

## Cutter radius compensation: arc input semantics

§3.5.3 of `RS274NGC.md` says: "If cutter radius compensation is active,
the motion will differ from what is described here. See Appendix B." That
sentence defers the *motion* to Appendix B but does not redefine the
*input semantics* of R, I, and J under CRC, and Appendix B describes the
geometric construction without explicitly restating what R, I, and J
mean. §B.6's auxiliary-arc construction (the auxiliary arc has its center
at the programmed center point and passes through the programmed end
point) and §B.1.1's note that the world model tracks the tool-tip center
under CRC together leave the following resolved:

Under cutter radius compensation, on a G2/G3 arc move — whether the move
is the entry move (first compensated motion after G41 or G42) or a
continuation move:

- X, Y name the programmed contour endpoint (the auxiliary-arc endpoint
  per §B.6), not the position the tool tip will reach.
- R names the radius of the path the tool tip actually traces (the
  "generated arc" per §B.6, which shares its center with the auxiliary
  arc).
- I, J are offsets from the current tool-tip location (per §B.1.1's
  world-model convention) to that shared center — not from the previous
  programmed contour endpoint.
