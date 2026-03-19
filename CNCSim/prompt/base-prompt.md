I work with CNC machines and I need software that can simulate the execution of G-code programs — the language CNC machines use to describe tool paths and machining operations.

The complete specification for the G-code language I use is in the docs/ directory. Please read it and build a simulator that correctly executes G-code programs according to that specification.

The simulator should be a command-line program. When I run it, I want to give it a G-code file with X lines and get back the full state of the machine at the end of each the X lines — where the tool ended up, what the feed rate was, spindle status, and so on.