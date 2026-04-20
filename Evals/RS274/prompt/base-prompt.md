I work with CNC machines and I need software that can simulate the execution of G-code programs — the language CNC machines use to describe tool paths and machining operations.

The complete specification for the G-code language I use is in the docs/ directory. Please read it and build a simulator that correctly executes G-code programs according to that specification.

The simulator should be a command-line program. When I run it, I want to give it a G-code file and get back the full state of the machine at the end of the program — where the tool ended up, what the feed rate was, spindle status, and so on. Sometimes I also want a time-ordered record of how the machine state evolved *during* execution, sampled at a configurable granularity, so that I can replay the tool path line by line in a GUI or audit what happened step by step.
