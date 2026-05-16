# pp67 interpreter
# This file reads a program written in the pp67 language and runs it.
# pp67 is a tiny toy language.  The only source code that currently works
# uses the tokens described in the tokenizer.

import sys

class ReverseRequest(Exception):
    """Raised when a REVERSECODE token is encountered at the top level."""


def tokenize(source):
    """
    Convert pp67 source text into a list of token tuples.

    Each token is a pair: (type, value).
    Recognised token types:
        PRINT, WHILELOOP, IF, ELSE, VARIABLE, FORLOOP,
        REVERSECODE,
        BLOCKOPEN, BLOCKCLOSE,
        EQUALS, NOTEQUALS, GREATERTHAN, LESSTHAN,
        LITERAL  (everything else)

    Special behaviour for LITERAL:
    If a literal looks like a plain number, we subtract 1 from it
    before storing it in the token list.  This is a quirk of pp67.
    """
    # Multi-word keywords are merged into single tokens so the later
    # simple split() can find them.
    source = source.replace("ding dong", "dingdong")
    source = source.replace("))<>>((", "forloop")
    source = source.replace("deeznutz", "EQUALS")

    result = []
    # Split the source text on any whitespace to get individual tokens.
    for token in source.split():
        # Check whether the token matches a known pp67 keyword.
        if token == "8==D":
            result.append(("PRINT", token))
        elif token == "(())":
            result.append(("WHILELOOP", token))
        elif token == ":3":
            result.append(("IF", token))
        elif token == "UwU":
            result.append(("ELSE", token))
        elif token == "dingdong":
            result.append(("VARIABLE", token))
        elif token == "forloop":
            result.append(("FORLOOP", token))
        elif token == "EQUALS":
            result.append(("EQUALS", token))
        elif token == "peepee":
            result.append(("REVERSECODE", token))
        elif token == "{":
            result.append(("BLOCKOPEN", token))
        elif token == "}":
            result.append(("BLOCKCLOSE", token))
        elif token == "==":
            result.append(("EQUALS", token))
        elif token == "!=":
            result.append(("NOTEQUALS", token))
        elif token == ">":
            result.append(("GREATERTHAN", token))
        elif token == "<":
            result.append(("LESSTHAN", token))
        else:
            # Any word that didn't match a keyword is treated as a LITERAL.
            # If it can be interpreted as an integer, subtract 1 first
            # then store the adjusted number as a string.
            try:
                num = int(token)
                adjusted = num - 1
                result.append(("LITERAL", str(adjusted)))
            except ValueError:
                result.append(("LITERAL", token))
    return result


def run(tokens):
    """
    Execute the tokenised pp67 program.

    We use a helper _execute that can be called recursively for
    blocks inside IF/ELSE, WHILELOOP and FORLOOP.
    """
    # variables = dictionary that holds all pp67 variables (global scope)
    variables = {}

    def _execute(block_tokens, scope, top_level=False):
        """
        Walk through a list of tokens and execute them one by one.

        block_tokens : the list of tokens for the current block
        scope        : a dictionary of variable values visible here
        top_level    : True when this is the top‑level invocation.
        """
        ip = 0   # instruction pointer – where we are in the token list

        def resolve_value(val):
            """
            Given a token value (a string), work out what it really means.

            - If the string is a variable name that exists in 'scope',
              use its stored value.
            - Otherwise, if it can be turned into an integer, do so.
            - Otherwise, just keep it as a string.
            """
            if val in scope:
                return scope[val]
            try:
                return int(val)
            except ValueError:
                return val

        # Keep reading tokens until we reach the end of the block.
        while ip < len(block_tokens):
            ttype, tval = block_tokens[ip]

            # ---------- PRINT ----------
            if ttype == "PRINT":
                # The next token is the thing to print.
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("No value to print")
                next_type, next_val = block_tokens[ip + 1]
                if next_type != "LITERAL":
                    raise RuntimeError("Invalid argument for PRINT")
                # If the literal is a variable name, print its value.
                # Otherwise print the literal itself.
                if next_val in scope:
                    print(scope[next_val])
                else:
                    print(next_val)
                ip += 2

            # ---------- VARIABLE (ding dong) ----------
            elif ttype == "VARIABLE":
                # Expects: variable name, then value
                if ip + 2 >= len(block_tokens):
                    raise RuntimeError("Missing variable name or value")
                name_tok = block_tokens[ip + 1]
                val_tok  = block_tokens[ip + 2]
                if name_tok[0] != "LITERAL" or val_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid variable definition")
                name = name_tok[1]
                # If the value looks like a number, store it as an integer,
                # otherwise store the raw string.
                try:
                    value = int(val_tok[1])
                except ValueError:
                    value = val_tok[1]
                scope[name] = value
                ip += 3

            # ---------- WHILELOOP ((())) ----------
            elif ttype == "WHILELOOP":
                # The condition consumes the next three tokens:
                #   left operand, comparison operator, right operand
                if ip + 3 >= len(block_tokens):
                    raise RuntimeError("WHILELOOP missing condition")
                left_tok  = block_tokens[ip + 1]
                op_tok    = block_tokens[ip + 2]
                right_tok = block_tokens[ip + 3]

                if left_tok[0] != "LITERAL" or right_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid condition operands")
                ip += 4  # move instruction pointer past the condition tokens

                # The WHILE body must be surrounded by { ... }
                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after WHILE condition")
                ip += 1  # skip the opening {
                start_body = ip

                # Find the matching closing } for the WHILE body.
                depth = 1
                while ip < len(block_tokens) and depth > 0:
                    if block_tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif block_tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unmatched { for WHILE body")
                end_body = ip - 1   # index of the closing }
                while_body = block_tokens[start_body:end_body]

                # Evaluate the condition and keep looping while it is true.
                while True:
                    left_val  = resolve_value(left_tok[1])
                    right_val = resolve_value(right_tok[1])
                    op_type = op_tok[0]
                    if op_type == "EQUALS":
                        cond = left_val == right_val
                    elif op_type == "NOTEQUALS":
                        cond = left_val != right_val
                    elif op_type == "GREATERTHAN":
                        cond = left_val > right_val
                    elif op_type == "LESSTHAN":
                        cond = left_val < right_val
                    else:
                        raise RuntimeError("Unknown comparison operator")

                    if not cond:
                        break
                    _execute(while_body, scope)
                # ip already points just past the whole WHILE construct
                continue

            # ---------- FORLOOP ())<>>(() ----------
            elif ttype == "FORLOOP":
                # Expect a variable name (a LITERAL token) that holds the count.
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("FORLOOP missing variable")
                var_tok = block_tokens[ip + 1]
                if var_tok[0] != "LITERAL":
                    raise RuntimeError("FORLOOP variable must be a literal")
                var_name = var_tok[1]
                count_val = resolve_value(var_name)
                if not isinstance(count_val, int):
                    raise RuntimeError("FORLOOP count must be an integer")
                ip += 2  # skip the FORLOOP keyword and the variable

                # The FOR body must be surrounded by { ... }
                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after FORLOOP variable")
                ip += 1  # skip the opening {
                start_body = ip

                depth = 1
                while ip < len(block_tokens) and depth > 0:
                    if block_tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif block_tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unmatched { for FORLOOP body")
                end_body = ip - 1
                for_body = block_tokens[start_body:end_body]

                # Execute the body exactly count_val times.
                for _ in range(count_val):
                    _execute(for_body, scope)
                # ip already points past the FORLOOP construct
                continue

            # ---------- IF (:3) with optional ELSE (UwU) ----------
            elif ttype == "IF":
                # The condition consumes the next three tokens:
                #   left operand, comparison operator, right operand
                if ip + 3 >= len(block_tokens):
                    raise RuntimeError("IF missing condition")
                left_tok  = block_tokens[ip + 1]
                op_tok    = block_tokens[ip + 2]
                right_tok = block_tokens[ip + 3]

                if left_tok[0] != "LITERAL" or right_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid condition operands")

                # Turn the operands into real values (possibly variable lookups).
                left_val  = resolve_value(left_tok[1])
                right_val = resolve_value(right_tok[1])

                # Decide whether the condition is true or false.
                op_type = op_tok[0]
                if op_type == "EQUALS":
                    cond = left_val == right_val
                elif op_type == "NOTEQUALS":
                    cond = left_val != right_val
                elif op_type == "GREATERTHAN":
                    cond = left_val > right_val
                elif op_type == "LESSTHAN":
                    cond = left_val < right_val
                else:
                    raise RuntimeError("Unknown comparison operator")

                ip += 4  # move instruction pointer past the condition tokens

                # The IF body must be surrounded by { ... }
                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after IF condition")
                ip += 1  # skip the opening {
                start_if = ip

                # Find the matching closing } for the IF body.
                depth = 1
                while ip < len(block_tokens) and depth > 0:
                    if block_tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif block_tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unmatched { for IF body")
                end_if = ip - 1   # index of the closing }
                if_block = block_tokens[start_if:end_if]

                # Check for an optional ELSE branch (UwU { ... })
                else_block = None
                if ip < len(block_tokens) and block_tokens[ip][0] == "ELSE":
                    ip += 1  # consume the UwU token
                    if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                        raise RuntimeError("Expected { after else")
                    ip += 1  # skip the opening {
                    start_else = ip
                    depth_else = 1
                    while ip < len(block_tokens) and depth_else > 0:
                        if block_tokens[ip][0] == "BLOCKOPEN":
                            depth_else += 1
                        elif block_tokens[ip][0] == "BLOCKCLOSE":
                            depth_else -= 1
                        ip += 1
                    if depth_else != 0:
                        raise RuntimeError("Unmatched { for else body")
                    end_else = ip - 1
                    else_block = block_tokens[start_else:end_else]

                # Run the correct branch.
                if cond:
                    _execute(if_block, scope)
                elif else_block is not None:
                    _execute(else_block, scope)

                # The instruction pointer is now right after the whole IF/ELSE
                # construct, so just continue to the next loop iteration.
                continue

            # ---------- ELSE (UwU) outside an IF ----------
            elif ttype == "ELSE":
                # An ELSE token without a preceding IF is illegal.
                raise RuntimeError("Unexpected ELSE without matching IF")

            # ---------- REVERSECODE (peepee) ----------
            elif ttype == "REVERSECODE":
                if not top_level:
                    raise SyntaxError("REVERSECODE can only appear at the top level")
                # Signal the top‑level runner to reverse the token list and restart.
                raise ReverseRequest

            # ---------- Anything else ----------
            else:
                # For example, a stray literal that wasn't consumed by a command.
                # We simply skip it.
                ip += 1

    # The top‑level runner catches ReverseRequest and restarts from the beginning.
    while True:
        try:
            _execute(tokens, variables, top_level=True)
            break   # normal termination
        except ReverseRequest:
            # Find the first REVERSECODE token in the global token list and remove it.
            for i, (tt, _) in enumerate(tokens):
                if tt == "REVERSECODE":
                    del tokens[i]
                    break
            # Reverse the whole program and restart.
            tokens.reverse()
            # Variables are kept; execution resumes from the top.


if __name__ == "__main__":
    # The name of the pp67 source file is "mainturd.pp" by default.
    # You can pass a different filename on the command line.
    filename = "mainturd.pp"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    with open(filename, "r") as f:
        source = f.read()
    tokens = tokenize(source)
    run(tokens)
