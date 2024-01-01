# Define token types
KEYWORD = 'keyword'
IDENTIFIER = 'identifier'
INTEGER = 'integer'
REAL = 'real'
OPERATOR = 'operator'
SEPARATOR = 'separator'
COMMENT = 'comment'
INVALID = 'invalid'

# Define sets for different token types
keywords = {'integer', 'bool', 'if', 'ret', 'while', 'else', 'endif', 'get', 'true', 'false', 'real', 'put'}
operators = {'<', '>', '=', '!', '+', '-', '*', '/'}
long_operators = {'<=', '==', '!=', '=>', '+-'}
relational_operators = {'<=', '==', '!=', '=>', '<', '>'}
separators = {'#', '{', '}', ';', ',', '(', ')'}

class Lexer:

    

    def __init__(self):
        self.tokens = []
        self.index = -1

    def lexer_fsm(self, input_string):
        tokens = []
        current_token = ''
        i = 0
        in_comment = False
        in_real = False

        while i < len(input_string):
            char = input_string[i]
            lookahead = input_string[i+1] if (i + 1) < len(input_string) else ''

            # Handling comments
            if in_comment:
                if char == '*' and lookahead == ']':
                    in_comment = False
                    i += 2  # Skip past the ']' of the comment end
                    continue
                i += 1
                continue

            # Check for start of comment
            if char == '[' and lookahead == '*':
                in_comment = True
                i += 2  # Skip past the '*' of the comment start
                continue

            if char.isspace():
                i += 1
                continue

            # Check for operators and separators
            if (char + lookahead) in long_operators:
                tokens.append((OPERATOR, char + lookahead))
                i += 2
                continue
            elif char in operators:
                tokens.append((OPERATOR, char))
                i += 1
                continue
            elif char in separators:
                tokens.append((SEPARATOR, char))
                i += 1
                continue

            # Check for keywords, identifiers, numbers, reals, and invalid tokens
            if char.isalpha():
                while i < len(input_string) and input_string[i].isalnum():
                    current_token += input_string[i]
                    i += 1
                if current_token in keywords:
                    tokens.append((KEYWORD, current_token))
                elif current_token[-1].isdigit():
                    tokens.append((INVALID, current_token))
                elif current_token[0].isalpha():
                    tokens.append((IDENTIFIER, current_token))
                else:
                    tokens.append((INVALID, current_token))
                current_token = ''
            elif char.isdigit():
                # Begin number handling
                in_number = True
                while i < len(input_string) and (input_string[i].isdigit() or input_string[i] == '.' or input_string[i].isalpha()):
                    if input_string[i] == '.':
                        if in_real:
                            break  # Second dot found, which is invalid
                        in_real = True
                    if input_string[i].isalpha():
                        in_number = False
                    current_token += input_string[i]
                    i += 1
                if not in_number or (in_real and current_token.endswith('.')):
                    tokens.append((INVALID, current_token))
                elif in_real:
                    tokens.append((REAL, current_token))
                else:
                    tokens.append((INTEGER, current_token))
                current_token = ''
                in_real = False
            else:
                if char == '.':
                    # Handle invalid tokens starting with a dot
                    while i < len(input_string) and (input_string[i].isdigit() or input_string[i] == '.'):
                        current_token += input_string[i]
                        i += 1
                    tokens.append((INVALID, current_token))
                    current_token = ''
                else:
                    # Anything else not recognized is invalid
                    tokens.append((INVALID, char))
                    i += 1

        self.tokens = tokens

    def tokenize(self, input_string):
        # Clears previous tokens and processes the new input string
        self.tokens = []  # Clear any existing tokens
        self.index = -1   # Reset index
        self.lexer_fsm(input_string)  # Process the input string to tokenize it

    def next_token(self):
        self.index += 1
        if self.index < len(self.tokens):
            return self.tokens[self.index]
        else:
            return ('EOF', 'EOF')  # End of file/token stream

    def peek(self):
        next_index = self.index + 1
        if next_index < len(self.tokens):
            return self.tokens[next_index]
        else:
            return ('EOF', 'EOF')  # End of file/token stream
        

class SymbolTableEntry:
    def __init__(self, lexeme, memory_address):
        self.lexeme = lexeme
        self.memory_address = memory_address

class SymbolTable:
    def __init__(self):
        self.table = {}
        self.memory_address = 7000
        

    def add_identifier(self, lexeme):
        if lexeme in self.table:
            raise Exception(f"Duplicate identifier declared: {lexeme}")
        self.table[lexeme] = SymbolTableEntry(lexeme, self.memory_address)
        self.memory_address += 1

    def check_identifier(self, lexeme):
        if lexeme not in self.table:
            raise Exception(f"Undeclared identifier used: {lexeme}")
        
    def print_symbol_table(self):
        print("Symbol Table Contents:")
        for lexeme, entry in self.table.items():
            print(f"Identifier: {lexeme}, Memory Address: {entry.memory_address}")



class Parser:
    def __init__(self, lexer, output_file):
        self.lexer = lexer
        self.current_token = None
        self.output = []
        self.lexer.index = 0
        self.printing_rules = True
        self.output_file = output_file
        self.last_token = ''
        self.symbol_table = SymbolTable()
        self.is_declaration_context = False
        self.assembly_code = []
        self.instruction_count = 0


    def parse(self, input_string):
        # Pass the input string to the lexer's tokenize method
        self.current_token = self.lexer.tokens[self.lexer.index]
        self.rat23f()

    def match(self, token_type):
        if self.current_token is None:
            self.error(f"Unexpected end of input, was expecting {token_type}")
        elif self.current_token[1] == token_type:
            self.current_token = self.lexer.next_token()  # assuming get_next_token() is the method that fetches the next token
        else:
            self.error(f"Expected {token_type}, got {self.current_token[1]}")

    def match_type(self, token_type):
        if self.current_token is None:
            self.error(f"Unexpected end of input, was expecting {token_type}")
        elif self.current_token[0] == token_type:
            self.current_token = self.lexer.next_token()  # assuming get_next_token() is the method that fetches the next token
        else:
            self.error(f"Expected {token_type}, got {self.current_token[0]}")

    def rat23f(self):
        # R1. <Rat23F> ::= <Opt Function Definitions> # <Opt Declaration List> <Statement List> #
        if self.printing_rules:
            self.output_rule("<Rat23F> ::= <Opt Function Definitions> # <Opt Declaration List> <Statement List> #")

        self.opt_function_definitions()
        self.match('#')
        self.opt_declaration_list()
        self.statement_list()
        self.match('#')

    # You will need to define methods for each non-terminal in the grammar.
    # For example:
    def opt_function_definitions(self):
        # R2. <Opt Function Definitions> ::= <Function Definitions> | <Empty>
        if self.current_token[1] == 'function':
            if self.printing_rules:
                self.output_rule("<Opt Function Definitions> ::= <Function Definitions>")

            self.function_definitions()
        else:
            self.empty()

    def function_definitions(self):
        # R3. <Function Definitions> ::= <Function> | <Function> <Function Definitions>
        if self.printing_rules:
                self.output_rule("<Function Definitions> ::= <Function> | <Function> <Function Definitions>")

        self.function()
        if self.current_token[1] == 'function':
            self.function_definitions()

    def function(self):
        # R4. <Function> ::= function <Identifier> ( <Opt Parameter List> ) <Opt Declaration List> <Body>
        if self.printing_rules:
                self.output_rule("<Function> ::= function <Identifier> ( <Opt Parameter List> ) <Opt Declaration List> <Body>")

        self.match('function')
        self.match_type('identifier')  # Function name
        self.match('(')
        self.is_declaration_context = True   # Set context for parameter declaration
        self.opt_parameter_list()
        self.is_declaration_context = False  # Reset context after parameters
        self.match(')')
        self.opt_declaration_list()
        self.body()

    def opt_parameter_list(self):
        # R5. <Opt Parameter List> ::= <Parameter List> | <Empty>
        if self.current_token[0] == IDENTIFIER:
            if self.printing_rules:
                self.output_rule("<Opt Parameter List> ::= <Parameter List>")

            self.parameter_list()
        else:
            self.empty()

    def parameter_list(self):
        # R6. <Parameter List> ::= <Parameter> | <Parameter> , <Parameter List>
        if self.printing_rules:
                self.output_rule("<Parameter List> ::= <Parameter> | <Parameter> , <Parameter List>")

        self.parameter()
        while self.current_token[0] == SEPARATOR and self.current_token[1] == ',':
            self.match_type(SEPARATOR)  # Match comma
            self.parameter()  # Process next parameter

    def parameter(self):
        # R7. <Parameter> ::= <IDs > <Qualifier>
        if self.printing_rules:
                self.output_rule("<Parameter> ::= <IDs > <Qualifier>")

        self.ids()
        self.qualifier()

    def qualifier(self):
        # R8. <Qualifier> ::= integer | bool | real
        if self.printing_rules:
                self.output_rule("<Qualifier> ::= integer | bool | real")

        if self.current_token[1] in keywords and self.current_token[1] in {'integer', 'bool', 'real'}:
            self.match_type(KEYWORD)  # Match the keyword which is a qualifier
        else:
            self.error("Expected qualifier")

    def body(self):
        # R9. <Body> ::= { < Statement List> }
        if self.printing_rules:
                self.output_rule("<Body> ::= { < Statement List> }")

        self.match_type(SEPARATOR)
        self.statement_list()
        self.match_type(SEPARATOR)

    def opt_declaration_list(self):
        # R10. <Opt Declaration List> ::= <Declaration List> | <Empty>
        if self.current_token[1] in {'integer', 'bool', 'real'}:
            if self.printing_rules:
                self.output_rule("<Opt Declaration List> ::= <Declaration List>")

            self.declaration_list()
        else:
            self.empty()

    def declaration_list(self):
        # R11. <Declaration List> ::= <Declaration> ; <Declaration List>
        if self.printing_rules:
            self.output_rule("<Declaration List> ::= <Declaration> ; <Declaration List>")

        self.declaration()
        self.match_type(SEPARATOR)
        if self.current_token[1] in {'integer', 'bool', 'real'}:
            self.declaration_list()

    def declaration(self):
        self.is_declaration_context = True
        # R12. <Declaration> ::= <Qualifier > <IDs>
        if self.printing_rules:
            self.output_rule("<Declaration> ::= <Qualifier > <IDs>")

        self.qualifier()
        self.ids()
        self.is_declaration_context = False

    def ids(self):
        # R13. <IDs> ::= <Identifier> | <Identifier>, <IDs>
        if self.printing_rules:
            self.output_rule("<IDs> ::= <Identifier> | <Identifier>, <IDs>")

        while True:
            if self.current_token[0] != IDENTIFIER:
                break

            identifier = self.current_token[1]
            if self.is_declaration_context:
                self.symbol_table.add_identifier(identifier)
            else:
                self.symbol_table.check_identifier(identifier)

            self.match_type(IDENTIFIER)

            if self.current_token[1] == ',':
                self.match_type(SEPARATOR)
            else:
                break




    def statement_list(self):
        # R14. <Statement List> ::= <Statement> <Statement List Prime>
        if self.printing_rules:
            self.output_rule("<Statement List> ::= <Statement> <Statement List Prime>")

        self.statement()
        self.statement_list_prime()

    def statement_list_prime(self):
        # R14_Prime. <Statement List Prime> ::= <Statement> <Statement List Prime> | ε
        if (self.current_token[1] in {'{', 'if', 'ret', 'put', 'get', 'while'} or self.current_token[0] == 'identifier'):
            if self.printing_rules:
                self.output_rule("<Statement List Prime> ::= <Statement> <Statement List Prime>")

        while (self.current_token[1] in {'{', 'if', 'ret', 'put', 'get', 'while'} or self.current_token[0] == 'identifier'):
            self.statement()
            self.statement_list_prime()

    def statement(self):
        # R15. <Statement> ::= <Compound> | <Assign> | <If> | <Return> | <Print> | <Scan> | <While>
        if self.current_token[0] == SEPARATOR and self.current_token[1] == '{':
            if self.printing_rules:
                self.output_rule("<Statement> ::= <Compound>")

            self.parse_compound()
        elif self.current_token[0] == IDENTIFIER:
            if self.printing_rules:
                self.output_rule("<Statement> ::= <Assign>")

            self.parse_assign()
        elif self.current_token[1] == 'if':
            if self.printing_rules:
                self.output_rule("<Statement> ::= <If>")

            self.parse_if()
        elif self.current_token[1] == 'ret':
            if self.printing_rules:
                self.output_rule("<Statement> ::= <Return>")

            self.parse_return()
        elif self.current_token[1] == 'put':
            if self.printing_rules:
                self.output_rule("<Statement> ::= <Print>")

            self.parse_print()
        elif self.current_token[1] == 'get':
            if self.printing_rules:
                self.output_rule("<Statement> ::= <Scan>")

            self.parse_scan()
        elif self.current_token[1] == 'while':
            if self.printing_rules:
                self.output_rule("<Statement> ::= <While>")

            self.parse_while()
        else:
            self.error("Expected statement")

    # R16. <Compound> ::= { <Statement List> }
    def parse_compound(self):
        if self.printing_rules:
            self.output_rule("<Compound> ::= { <Statement List> }")

        self.match('{')
        self.statement_list()
        self.match('}')


    # R17. <Assign> ::= <Identifier> = <Expression> ;
    def parse_assign(self):
        if self.printing_rules:
            self.output_rule("<Assign> ::= <Identifier> = <Expression> ;")

        # Get the identifier's name and its memory location
        variable_name = self.current_token[1]
        self.match_type(IDENTIFIER)
        variable_memory_location = self.symbol_table.table[variable_name].memory_address

        self.match('=')

        # Evaluate the expression on the right-hand side
        # This should generate assembly instructions to compute the expression
        self.parse_expression()

        # After the expression is evaluated, the result will be on top of the stack
        # Generate a POPM instruction to store the result in the variable's location
        self.assembly_code.append((self.instruction_count, f"POPM {variable_memory_location}"))
        self.instruction_count += 1

        self.match(';')


    # R18. <If> ::= if ( <Condition> ) <Statement> endif | if ( <Condition> ) <Statement> else <Statement> endif
    def parse_if(self):
        if self.printing_rules:
            self.output_rule("<If> ::= if ( <Condition> ) <Statement> endif | if ( <Condition> ) <Statement> else <Statement> endif")

        self.match('if')
        self.match('(')
        self.condition()  # Generates the comparison assembly instructions
        self.match(')')

        # Append a JUMPZ placeholder and remember its index
        jumpz_instruction_index = self.instruction_count
        self.assembly_code.append((self.instruction_count, "JUMPZ placeholder"))
        self.instruction_count += 1

        self.statement()

        has_else = self.current_token[1] == 'else'
        if has_else:
            # Append a JUMP placeholder to skip the else part and remember its index
            jump_instruction_index = self.instruction_count
            self.assembly_code.append((self.instruction_count, "JUMP placeholder"))
            self.instruction_count += 1

            # Update the JUMPZ instruction with the correct destination (start of the else part)
            jumpz_destination = self.instruction_count
            self.assembly_code[jumpz_instruction_index] = (jumpz_instruction_index, f"JUMPZ {jumpz_destination}")

            self.match('else')
            self.statement()

            # Update the JUMP instruction with the correct destination (after the else part)
            jump_destination = self.instruction_count
            self.assembly_code[jump_instruction_index] = (jump_instruction_index, f"JUMP {jump_destination}")
        else:
            # Update the JUMPZ instruction to jump after the if statement if there's no else
            jumpz_destination = self.instruction_count
            self.assembly_code[jumpz_instruction_index] = (jumpz_instruction_index, f"JUMPZ {jumpz_destination}")

        self.match('endif')







    # R19. <Return> ::= ret ; | ret <Expression> ;
    def parse_return(self):
        if self.printing_rules:
            self.output_rule("<Return> ::= ret ; | ret <Expression> ;")

        self.match('ret')
        if self.current_token[1] != ';':
            self.parse_expression()  # Generate assembly for the expression
        self.match(';')

        # Generate return-related assembly code here (if needed)


    # R20. <Print> ::= put ( <Expression> );
    def parse_print(self):
        if self.printing_rules:
            self.output_rule("<Print> ::= put ( <Expression> );")

        self.match('put')
        self.match('(')
        self.parse_expression()  # This will generate assembly to evaluate the expression
        self.match(')')

        # Add STDOUT instruction to print the value
        self.assembly_code.append((self.instruction_count, "STDOUT"))
        self.instruction_count += 1

        self.match(';')


    # R21. <Scan> ::= get ( <IDs> );
    def parse_scan(self):
        if self.printing_rules:
            self.output_rule("<Scan> ::= get ( <IDs> );")

        self.match('get')
        self.match('(')
        
        # Handle identifiers one by one
        while True:
            if self.current_token[0] != IDENTIFIER:
                break

            identifier = self.current_token[1]
            memory_location = self.symbol_table.table[identifier].memory_address
            
            # Generate STDIN and POPM instructions for each identifier
            self.assembly_code.append((self.instruction_count, "STDIN"))
            self.instruction_count += 1
            self.assembly_code.append((self.instruction_count, f"POPM {memory_location}"))
            self.instruction_count += 1

            self.match_type(IDENTIFIER)

            if self.current_token[1] == ',':
                self.match_type(SEPARATOR)
            else:
                break

        self.match(')')
        self.match(';')



    def parse_while(self):
        if self.printing_rules:
            self.output_rule("<While> ::= while ( <Condition> ) <Statement>")

        start_label = self.instruction_count
        self.assembly_code.append((self.instruction_count, "LABEL"))
        self.instruction_count += 1

        self.match('while')
        self.match('(')
        self.condition()
        self.match(')')

        # Generate JUMPZ for conditional exit
        exit_label = self.instruction_count + 2  # Placeholder for the jump destination
        self.assembly_code.append((self.instruction_count, f"JUMPZ {exit_label}"))
        self.instruction_count += 1

        self.statement()

        # Jump back to the start of the loop
        self.assembly_code.append((self.instruction_count, f"JUMP {start_label}"))
        self.instruction_count += 1

        # Label for loop exit
        self.assembly_code.append((self.instruction_count, f"LABEL {exit_label}"))
        self.instruction_count += 1


    def condition(self):
        if self.printing_rules:
            self.output_rule("<Condition> ::= <Expression> <Relop> <Expression>")

        self.parse_expression()
        self.relop()
        self.parse_expression()

        # Add assembly code for the relational operation based on self.relop_op
        # Assuming self.relop_op is set in the relop() method to the operation type
        if self.relop_op == "==":
            self.assembly_code.append((self.instruction_count, "EQU"))
        elif self.relop_op == "<":
            self.assembly_code.append((self.instruction_count, "LES"))
        # ... handle other relational operators ...
        self.instruction_count += 1


    def relop(self):
        if self.printing_rules:
            self.output_rule("<Relop> ::= == | != | > | < | <= | =>")

        relop_instruction_map = {
            '==': 'EQU', '!=': 'NEQ', '>': 'GRT', '<': 'LES',
            '<=': 'LEQ', '>=': 'GEQ'
        }

        if self.current_token[1] in relational_operators:
            self.relop_op = self.current_token[1]  # Set the operation type
            self.match(self.current_token[1])
        else:
            self.error("Expected relational operator")


    def parse_expression(self):
        if self.printing_rules:
            self.output_rule("<Expression> ::= <Term> <Expression Prime>")

        self.term()
        self.expression_prime()

    def expression(self):
        # R25. <Expression> ::= <Term> <Expression Prime>
        if self.printing_rules:
            self.output_rule("<Expression> ::= <Term> <Expression Prime>")

        self.term()
        self.expression_prime()

    def expression_prime(self):
        # R25_Prime. <Expression Prime> ::= + <Term> <Expression Prime> | - <Term> <Expression Prime> | <Empty>
        while self.current_token[1] in {'+', '-'}:
            op = self.current_token[1]
            self.match(op)
            self.term()
            if op == '+':
                self.assembly_code.append((self.instruction_count, "ADD"))
            elif op == '-':
                self.assembly_code.append((self.instruction_count, "SUB"))
            self.instruction_count += 1

    def term(self):
        # R26. <Term> ::= <Factor> <Term Prime>
        if self.printing_rules:
            self.output_rule("<Term> ::= <Factor> <Term Prime>")

        self.factor()
        self.term_prime()

    def term_prime(self):
        # R26_Prime. <Term Prime> ::= * <Factor> <Term Prime> | / <Factor> <Term Prime> | <Empty>
        if self.printing_rules:
            self.output_rule("<Term Prime> ::= * <Factor> <Term Prime> | / <Factor> <Term Prime>")

        while self.current_token[1] in {'*', '/'}:
            op = self.current_token[1]
            self.match(op)
            self.factor()

            # Generate the appropriate assembly code based on the operator
            if op == '*':
                self.assembly_code.append((self.instruction_count, "MUL"))
            elif op == '/':
                self.assembly_code.append((self.instruction_count, "DIV"))
            self.instruction_count += 1

            # Call term_prime recursively to handle potential consecutive multiplication/division operations
            self.term_prime()


    def factor(self):
        # R27. <Factor> ::= - <Primary> | <Primary>
        if self.printing_rules:
            self.output_rule("<Factor> ::= - <Primary> | <Primary>")

        if self.current_token[1] == '-':  # Check if there's a unary minus
            self.match('-')
        self.primary()

    def primary(self):
        # R28. <Primary> ::= <Identifier> | <Integer> | <Identifier> (<IDs>) | (<Expression>) | true | false
        if self.current_token[0] == IDENTIFIER:
            if self.printing_rules:
                self.output_rule("<Primary> ::= <Identifier> | <Identifier> (<IDs>)")

            # Save the identifier to check if it's followed by '('
            saved_identifier = self.current_token
            self.match_type(IDENTIFIER)
            
            # If the identifier is followed by '(', it's a function call
            if self.current_token[1] == '(':
                self.match('(')
                self.ids()  # Process the function arguments
                self.match(')')
                # Add assembly code for function call here (if applicable)
            else:
                # Regular identifier - generate PUSHM instruction
                memory_location = self.symbol_table.table[saved_identifier[1]].memory_address
                self.assembly_code.append((self.instruction_count, f"PUSHM {memory_location}"))
                self.instruction_count += 1
        elif self.current_token[0] == INTEGER:
            if self.printing_rules:
                self.output_rule("<Primary> ::= <Integer>")

            # Integer literal - generate PUSHI instruction
            self.assembly_code.append((self.instruction_count, f"PUSHI {self.current_token[1]}"))
            self.instruction_count += 1
            self.match_type(INTEGER)
        elif self.current_token[1] == '(':
            if self.printing_rules:
                self.output_rule("<Primary> ::= (<Expression>)")

            self.match('(')
            self.expression()  # Process the expression inside the parentheses
            self.match(')')
        elif self.current_token[1] in {'true', 'false'}:
            if self.printing_rules:
                self.output_rule("<Primary> ::= true | false")

            # Boolean literal - convert to integer and push
            bool_value = 1 if self.current_token[1] == 'true' else 0
            self.assembly_code.append((self.instruction_count, f"PUSHI {bool_value}"))
            self.instruction_count += 1
            self.match(KEYWORD)
        else:
            self.error(f"Invalid primary token: {self.current_token}")


    def empty(self):
        # R29. <Empty> ::= epsilon
        # No action is needed for the empty production, as it just signifies the end of the recursion
        pass

    def error(self, message):
        raise Exception(message)

    def output_rule(self, rule):
        print(f"Token: {self.current_token[0]}    Lexeme: {self.current_token[1]}")
        print(rule)

        if self.last_token != self.current_token:
            self.output.append(f"Token: {self.current_token[0]},    Lexeme: {self.current_token[1]}")
            self.last_token = self.current_token

        self.output.append(f"  {rule}")

# Main program logic
if __name__ == "__main__":
    program_running = True

    while program_running:
        input_file = input("Input the name of the file to read from, or enter 'q' to quit: ")
        if input_file == 'q':
            program_running = False
            break

        output_file = input("Input the name of the file to write the assembly code and symbol table to: ")
        print("\n")

        lexer_instance = Lexer()

        try:
            with open(input_file, "r", encoding='utf-8-sig') as input_f:
                # Read the input from the file
                input_string = input_f.read()
                
                # Tokenize the input string using the lexer
                lexer_instance.tokenize(input_string)
                
                # Create a parser instance with the lexer instance
                parser = Parser(lexer_instance, output_file)
                
                # Start parsing by passing the input string to the parse method
                parser.parse(input_string)

                # Print and write assembly code and symbol table to the output file
                with open(output_file, "w", encoding='utf-8') as output_f:
                    # Assembly code
                    output_f.write("Assembly Code:\n")
                    print("\nAssembly Code:")
                    for instruction in parser.assembly_code:
                        line = f"{instruction[0]}: {instruction[1]}"
                        print(line)
                        output_f.write(line + "\n")

                    # Symbol table
                    output_f.write("\nSymbol Table:\n")
                    print("\nSymbol Table:")
                    for lexeme, entry in parser.symbol_table.table.items():
                        line = f"Identifier: {lexeme}, Memory Address: {entry.memory_address}"
                        print(line)
                        output_f.write(line + "\n")

        except IOError as e:
            print(f"An error occurred: {e.strerror}")
