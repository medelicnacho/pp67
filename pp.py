# pp67 interpreter
# This file reads a program written in the pp67 language and runs it.
# pp67 is a tiny toy language.  The only source code that currently works
# uses the tokens described in the tokenizer.

import sys


def tokenize(source):
    """
    Convert pp67 source text into a list of token tuples.

    Each token is a triple: (type, value, raw_string).
    raw_string is the original token from the source before any adjustment.
    Recognised token types:
        PRINT, WHILELOOP, IF, ELSE, VARIABLE, FORLOOP,
        REVERSECODE, LOCALREVERSE,
        BLOCKOPEN, BLOCKCLOSE,
        EQUALS, NOTEQUALS, GREATERTHAN, LESSTHAN,
        CLASSDEF, FUNCDEF, INSTANTIATE, SNIFF, HUMP,
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
            result.append(("PRINT", token, token))
        elif token == "(())":
            result.append(("WHILELOOP", token, token))
        elif token == ":3":
            result.append(("IF", token, token))
        elif token == "UwU":
            result.append(("ELSE", token, token))
        elif token == "dingdong":
            result.append(("VARIABLE", token, token))
        elif token == "forloop":
            result.append(("FORLOOP", token, token))
        elif token == "EQUALS":
            result.append(("EQUALS", token, token))
        elif token == "peepee":
            result.append(("REVERSECODE", token, token))
        elif token == "dildo":
            result.append(("LOCALREVERSE", token, token))
        elif token == "{":
            result.append(("BLOCKOPEN", token, token))
        elif token == "}":
            result.append(("BLOCKCLOSE", token, token))
        elif token == "==":
            result.append(("EQUALS", token, token))
        elif token == "!=":
            result.append(("NOTEQUALS", token, token))
        elif token == ">":
            result.append(("GREATERTHAN", token, token))
        elif token == "<":
            result.append(("LESSTHAN", token, token))
        elif token == "kcidyeknodimsoc":
            result.append(("CLASSDEF", token, token))
        elif token == "kcidyeknod":
            result.append(("FUNCDEF", token, token))
        elif token == "trafpir.yeknod":
            result.append(("INSTANTIATE", token, token))
        elif token == "ffins.yeknod":
            result.append(("SNIFF", token, token))
        elif token == "pmuh.yeknod":
            result.append(("HUMP", token, token))
        else:
            # Any word that didn't match a keyword is treated as a LITERAL.
            # If it can be interpreted as an integer, subtract 1 first
            # then store the adjusted number as a string.
            raw = token
            try:
                num = int(token)
                adjusted = num - 1
                result.append(("LITERAL", str(adjusted), raw))
            except ValueError:
                result.append(("LITERAL", token, raw))
    return result


def run(tokens):
    """
    Execute the tokenised pp67 program.

    We use a helper _execute that can be called recursively for
    blocks inside IF/ELSE, WHILELOOP, FORLOOP, and OOP constructs.
    """
    # variables = dictionary that holds all pp67 variables (global scope)
    variables = {}
    # OOP support: store class blueprints keyed by class name
    class_defs = {}

    def _build_statements(tokens):
        """
        Group the flat token list into top-level statements.
        Each statement is itself a flat list of tokens that describes
        exactly one complete construct (keyword, its operands, and any
        attached { } block(s) including nested braces).

        This grouping is needed for correct statement-level reversal.
        """
        ip = 0
        stmts = []
        while ip < len(tokens):
            start = ip
            tt = tokens[ip][0]
            ip += 1  # move past the keyword token

            # Determine how this keyword must be parsed.
            if tt == "PRINT":
                ops = 1
                block = False
                else_ = False
            elif tt == "VARIABLE":
                ops = 2
                block = False
                else_ = False
            elif tt == "WHILELOOP":
                ops = 3
                block = True
                else_ = False
            elif tt == "FORLOOP":
                ops = 1
                block = True
                else_ = False
            elif tt == "IF":
                ops = 3
                block = True
                else_ = True
            elif tt == "CLASSDEF":
                ops = 1
                block = True
                else_ = False
            elif tt == "FUNCDEF":
                ops = 1
                block = True
                else_ = False
            elif tt == "INSTANTIATE":
                ops = 2
                block = False
                else_ = False
            elif tt == "SNIFF":
                ops = 2
                block = False
                else_ = False
            elif tt == "HUMP":
                ops = 2
                block = False
                else_ = False
            elif tt == "LOCALREVERSE":
                # Gather everything up to the matching closing LOCALREVERSE.
                depth = 1
                while ip < len(tokens) and depth > 0:
                    if tokens[ip][0] == "LOCALREVERSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unclosed LOCALREVERSE")
                stmts.append(tokens[start:ip])
                continue
            else:
                # A stray token that should never appear at the top level;
                # keep it as a harmless single-token statement.
                stmts.append([tokens[start]])
                continue

            # Consume the operands.
            for _ in range(ops):
                if ip >= len(tokens):
                    raise RuntimeError(f"Not enough operands for {tt}")
                ip += 1

            # Consume the mandatory block, if any.
            if block:
                if ip >= len(tokens) or tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError(f"Expected {{ after {tt}")
                depth = 1
                ip += 1  # skip the opening {
                while ip < len(tokens) and depth > 0:
                    if tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError(f"Unmatched {{ for {tt}")

            # If the keyword supports an optional ELSE branch, consume it now.
            if else_:
                if ip < len(tokens) and tokens[ip][0] == "ELSE":
                    ip += 1  # skip the ELSE token
                    if ip >= len(tokens) or tokens[ip][0] != "BLOCKOPEN":
                        raise RuntimeError("Expected { after ELSE")
                    depth = 1
                    ip += 1
                    while ip < len(tokens) and depth > 0:
                        if tokens[ip][0] == "BLOCKOPEN":
                            depth += 1
                        elif tokens[ip][0] == "BLOCKCLOSE":
                            depth -= 1
                        ip += 1
                    if depth != 0:
                        raise RuntimeError("Unmatched { for ELSE")

            # All tokens from `start` up to (but not including) `ip` form
            # one complete statement.
            stmts.append(tokens[start:ip])

        return stmts

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
            ttype, tval, raw = block_tokens[ip]

            # ---------- PRINT ----------
            if ttype == "PRINT":
                # The next token is the thing to print.
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("No value to print")
                next_type, next_val, next_raw = block_tokens[ip + 1]
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
                # already handled before _execute; at top-level only
                raise RuntimeError("Unexpected REVERSECODE inside a block")

            # ---------- LOCALREVERSE (dildo ... dildo) ----------
            elif ttype == "LOCALREVERSE":
                # Gather everything until the matching closing LOCALREVERSE.
                j = ip + 1
                while j < len(block_tokens) and block_tokens[j][0] != "LOCALREVERSE":
                    j += 1
                if j >= len(block_tokens):
                    raise RuntimeError("Unclosed LOCALREVERSE")

                inner_tokens = block_tokens[ip + 1 : j]
                # Reconstruct the original source string by joining raw token values.
                raw_source = " ".join(tok[2] for tok in inner_tokens)
                # Reverse characters of the entire collected string.
                reversed_source = raw_source[::-1]
                # Tokenize the reversed string.
                reversed_tokens = tokenize(reversed_source)
                # Execute the resulting tokens in the current scope.
                _execute(reversed_tokens, scope)
                # Skip past the closing LOCALREVERSE token.
                ip = j + 1
                continue

            # ---------- CLASSDEF (kcidyeknodimsoc) ----------
            elif ttype == "CLASSDEF":
                # Expect a class name (LITERAL) and a block in { ... }
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("CLASSDEF missing class name")
                name_tok = block_tokens[ip + 1]
                if name_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid class name")
                class_name = name_tok[1]
                ip += 2  # skip CLASSDEF and class name

                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after class name")
                ip += 1  # skip {
                start_body = ip

                depth = 1
                while ip < len(block_tokens) and depth > 0:
                    if block_tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif block_tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unmatched { for class body")
                end_body = ip - 1
                class_body = block_tokens[start_body:end_body]
                class_defs[class_name] = class_body
                ip = end_body + 1  # skip past the closing }
                continue

            # ---------- FUNCDEF (kcidyeknod) ----------
            elif ttype == "FUNCDEF":
                # Expect a function name (LITERAL) and a block in { ... }
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("FUNCDEF missing function name")
                name_tok = block_tokens[ip + 1]
                if name_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid function name")
                func_name = name_tok[1]
                ip += 2  # skip FUNCDEF and name

                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after function name")
                ip += 1  # skip {
                start_body = ip

                depth = 1
                while ip < len(block_tokens) and depth > 0:
                    if block_tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif block_tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unmatched { for function body")
                end_body = ip - 1
                func_body = block_tokens[start_body:end_body]
                # Store the function inside the current scope so that
                # HUMP or a top‑level call can find it.
                scope[func_name] = func_body
                ip = end_body + 1  # skip past the closing }
                continue

            # ---------- INSTANTIATE (trafpir.yeknod) ----------
            elif ttype == "INSTANTIATE":
                # Expect class name and instance name.
                if ip + 2 >= len(block_tokens):
                    raise RuntimeError("INSTANTIATE missing arguments")
                class_tok = block_tokens[ip + 1]
                inst_tok  = block_tokens[ip + 2]
                if class_tok[0] != "LITERAL" or inst_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid arguments for INSTANTIATE")
                class_name = class_tok[1]
                instance_var = inst_tok[1]

                class_body = class_defs.get(class_name)
                if class_body is None:
                    raise RuntimeError(f"Class '{class_name}' not defined")

                # Create a fresh scope for the instance and run the class body.
                instance_scope = {}
                _execute(class_body, instance_scope)
                scope[instance_var] = instance_scope
                ip += 3
                continue

            # ---------- SNIFF (ffins.yeknod) ----------
            elif ttype == "SNIFF":
                # Expect instance name and property name.
                if ip + 2 >= len(block_tokens):
                    raise RuntimeError("SNIFF missing arguments")
                inst_tok = block_tokens[ip + 1]
                prop_tok = block_tokens[ip + 2]
                if inst_tok[0] != "LITERAL" or prop_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid arguments for SNIFF")
                instance_var = inst_tok[1]
                prop_name    = prop_tok[1]

                instance_data = scope.get(instance_var)
                if not isinstance(instance_data, dict):
                    raise RuntimeError(f"'{instance_var}' is not an instance")
                value = instance_data.get(prop_name)
                if value is None:
                    raise RuntimeError(f"Property '{prop_name}' not found")
                # Output the property value.
                print(value)
                ip += 3
                continue

            # ---------- HUMP (pmuh.yeknod) ----------
            elif ttype == "HUMP":
                # Expect instance name and method name.
                if ip + 2 >= len(block_tokens):
                    raise RuntimeError("HUMP missing arguments")
                inst_tok   = block_tokens[ip + 1]
                method_tok = block_tokens[ip + 2]
                if inst_tok[0] != "LITERAL" or method_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid arguments for HUMP")
                instance_var = inst_tok[1]
                method_name  = method_tok[1]

                instance_data = scope.get(instance_var)
                if not isinstance(instance_data, dict):
                    raise RuntimeError(f"'{instance_var}' is not an instance")
                method_body = instance_data.get(method_name)
                if method_body is None or not isinstance(method_body, list):
                    raise RuntimeError(f"Method '{method_name}' not found")
                # Execute the method body within the instance's own scope.
                _execute(method_body, instance_data)
                ip += 3
                continue

            # ---------- Anything else ----------
            else:
                # For example, a stray literal that wasn't consumed by a command.
                # We simply skip it.
                ip += 1

    # ---- pp67 reversal rule (statement-level) ----
    if tokens and tokens[0][0] == "REVERSECODE":
        del tokens[0]               # remove the REVERSECODE marker
        final_tokens = tokens       # run forwards: keep the original order
    else:
        # Group top-level tokens into statements, reverse the statement order,
        # and then flatten back into a single token list.
        stmts = _build_statements(tokens)
        stmts.reverse()
        final_tokens = [tok for stmt in stmts for tok in stmt]

    _execute(final_tokens, variables, top_level=True)


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
