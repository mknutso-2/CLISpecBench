Review pre-3.0 CNCSim test changes.
Replace the committed per-test dashboard aggregate with a generated local SQLite DB plus static-friendly sharded JSON for published dashboards.
Update agent CLI versions
Ensure MCPs / local configs aren't leaking
rewrite EvalDesign (4 core requirements)
5-10 new evals of different domains and sizes
Eval -> EvalPrototype
Task -> Eval
Update submission_command and just specify that application must run (and build if required) via run.sh.
Bump docker hardware specs.
