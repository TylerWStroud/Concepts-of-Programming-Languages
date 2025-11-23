# Module_3rd Deliverable  

In the previous two deliverables, you created a scanner for a subset of the SCL language
that featured an array of keywords used in the subset of SCL, demonstrating your
understanding of the grammar of the subset of SCL.  

For the 3rd deliverable, you are required to develop a complete interpreter or translator to
intermediate code and an abstract machine that includes the scanner, parser, and executor.
Your report must demonstrate the execution of this interpreter program using one or more
input files, and it must show the results of executing every statement recognized by the
parser using the programming language of your choice, such as Ada, Python, or
another language that you haven't used in the previous two deliverables.  

To do this, you need to break down the code into lexemes and identify the type of lexeme,
whether it be a keyword, string literal, real constant, or even an integer constant. The parser
can then be implemented using one of the programming languages. In this case, we used
Java.  

The lexical analyzer is comprised of four (4) classes, while the parser has eleven classes,
and the interpreter also has eleven classes. The scanner identifies the appropriate token code
for the lexeme in question and finds the next token code for the parser to use. This stage is
also used to filter out commented out lines of code and sections.  

The interpreter has three fundamental components: program, statement, and expression
classes. The program class defines two main methods, load and run. The load method parses
the SCL program into a series of statements, which are defined in the Statement class and
can be thought of as a sentence in SCL. For example, a statement would be "set x = 45.95".
The various statements in the SCL program are added to an ArrayList during the parsing
phase.  

In conclusion, for the 3rd deliverable, you are required to develop a complete interpreter or
translator to intermediate code and an abstract machine that includes the scanner, parser,
and executor. You must use Python, Ada, or another language that you haven't used in the
previous two deliverables. Your report must show the execution of the interpreter program
by using one or more input files and demonstrate the results of executing every statement
recognized by the parser.  

For this project, we developed an interpreter for a subset of the SCL language using Python.
The interpreter includes a scanner, parser, and executer.  

The scanner identifies the lexemes in the input SCL program and produces tokens as output.
The parser then takes these tokens and constructs a parse tree representing the program.
Finally, the executer traverses the parse tree to execute the program.