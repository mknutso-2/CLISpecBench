# RS274 Clarifications

This document records disambiguations of `RS274NGC.md` where the spec text
admits multiple defensible readings. Each item is a normative rule for
this simulator and should be treated on equal footing with the spec.

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

## Cutter radius compensation: D0 and zero radius

§3.5.10 and §B.2.4 of `RS274NGC.md` say that G41 and G42 may use D0,
and that D0 gives a cutter radius of zero. When G41 D0 or G42 D0 is
active, cutter radius compensation remains active with D set to zero. G40
is still required to turn cutter radius compensation off.

With a zero cutter radius, the compensated tool-center path coincides
with the programmed contour. A first compensated move with zero radius
therefore ends at the programmed endpoint, rather than applying a
nonzero tangent-circle offset.

## G87 back boring: omitted I, J, and K words

§3.5.16.8 of `RS274NGC.md` describes the I, J, and K words used by G87
but does not state whether omitting any of them is an error or what value
an omitted word has. In this simulator, omitted I, J, and K words on a
G87 block default to 0.

Defaulted I and J are zero offsets from the programmed in-plane hole
position, following §3.5.16.8's rule that I and J are always increments.
A defaulted K is the numeric K value 0 interpreted by §3.5.16.8's same
distance-mode rule as an explicit K0: absolute Z coordinate 0 in G90, or
a zero increment from the cycle's resolved Z target position in G91.

This default defines simulator behavior for omitted words. It does not
change §3.5.16.8's programming guidance that explicit I and J values
should be chosen to provide tool clearance in a real back-boring setup.
If a defaulted word makes a G87 sub-motion zero-length, that sub-motion
follows the general zero-duration trace rule and produces no trace entry.

## G88 boring: non-interactive manual retract

§3.5.16.9 of `RS274NGC.md` says that G88 stops the program so the
operator can retract the spindle manually. During command-line execution,
that manual retract is modeled as an automatic rapid retract to the
canned-cycle clear level defined by §3.5.16 and §3.5.20.

The intermediate program stop and temporary spindle stop/restart are not
modeled as pauses, errors, or separate trace/output state transitions.
During the automatic retract and after the cycle, the observable spindle
direction remains the direction that was active before the G88 cycle.
