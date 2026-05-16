# pp67 interpreter
# ========================================================================
# This program reads a source file written in the ***pp67*** toy language
# and executes it.  pp67 is designed for learning: every instruction is a
# quirky keyword and the whole language runs in a simple while‑loop with a
# variable‑scope dictionary.
#
# The interpreter does three things in order:
#   1. tokenize  – turn the source text into a flat list of token tuples
#   2. group top‑level tokens into **statements** (one keyword plus its
#      operands and any attached `{ }` block, treated as an atomic unit)
#   3. execute   – walk the token list (possibly reversed) and perform
#      the actions defined by each keyword
#
# Execution order rule (the *pp67 reversal rule*):
#   • If the very first token is `peepee` (the REVERSECODE marker),
#     that marker is removed and the program runs **forwards**
#     (top‑to‑bottom in the source file).
#   • If the first token is **not** `peepee`, the statement order is
#     **reversed** first, then executed.  Reversing at the statement
#     level keeps each `{ }` block together, so the logic inside a block
#     stays in its original order.
#
# All the existing keywords, the `peepee` reversal system, and the
# OOP additions are explained with comments inside the functions below.

import sys


def tokenize(source):
    """
    Convert pp67 source text into a list of token tuples.

    Each token is a triple: (type, value, raw_string).
    - 'type'       is a string like "PRINT", "VARIABLE", "EQUALS", …
    - 'value'      is the string we actually use during execution.
    - 'raw_string' is the original token before any adjustment (used
                   for LOCALREVERSE, which rebuilds the original text).

    Recognised token types (case‑sensitive):
        PRINT, WHILELOOP, IF, ELSE, VARIABLE, FORLOOP,
        REVERSECODE, LOCALREVERSE,
        BLOCKOPEN, BLOCKCLOSE,
        EQUALS, NOTEQUALS, GREATERTHAN, LESSTHAN,
        CLASSDEF, FUNCDEF, INSTANTIATE, SNIFF, HUMP,
        LITERAL  (everything else)

    Special behaviour for LITERAL:
    If a literal looks like a plain integer, we **subtract 1** from it
    before storing it in the token list.  This is a deliberate quirk of
    pp67 (e.g. the number 5 becomes 4).
    """
    # ----------------------------------------------------------------
    # 1. Replace multi‑word keywords with single‑token aliases so that
    #    a simple whitespace split() can find them.
    # ----------------------------------------------------------------
    source = source.replace("ding dong", "dingdong")
    source = source.replace("))<>>((", "forloop")
    source = source.replace("deeznutz", "EQUALS")

    result = []
    # ----------------------------------------------------------------
    # 2. Split on any whitespace → each piece becomes a candidate token.
    # ----------------------------------------------------------------
    for token in source.split():
        # Check whether the piece matches a known pp67 keyword.
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
        # ---------- OOP keywords (written character‑by‑character backwards) ----------
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
            # ---------- Anything else is a LITERAL ----------
            raw = token
            try:
                # If it looks like an integer, subtract 1 (the pp67 quirk)
                num = int(token)
                adjusted = num - 1
                result.append(("LITERAL", str(adjusted), raw))
            except ValueError:
                result.append(("LITERAL", token, raw))
    return result


def run(tokens):
    """
    Execute the tokenised pp67 program.

    The execution happens in three stages:
      1. Determine whether to reverse the program (pp67 reversal rule).
      2. Group the tokens into top‑level **statements** so that the
         reversal is applied statement‑by‑statement, keeping each
         `{ }` block intact.
      3. Call the recursive helper `_execute` on the resulting
         flat token list.

    The helper `_execute` may call itself for blocks inside
    IF/ELSE, WHILELOOP, FORLOOP, and OOP constructs.
    """
    # variables = dictionary that holds all pp67 variables (global scope)
    variables = {}
    # OOP support: store class blueprints keyed by class name
    class_defs = {}

    def _build_statements(tokens):
        """
        Group the flat token list into top‑level **statements**.

        A "statement" is one keyword together with all its operands AND
        any attached `{ }` block (including nested braces).  We need
        this grouping because the reversal rule works on statements,
        not on individual tokens.  Reversing tokens directly would flip
        `{` and `}` which would corrupt the program.

        For each keyword we know how many **operand** tokens follow
        and whether it expects a mandatory `{ }` block and an
        optional ELSE branch.
        """
        ip = 0
        stmts = []
        while ip < len(tokens):
            start = ip
            tt = tokens[ip][0]
            ip += 1  # move past the keyword token

            # Determine how many operands this keyword expects
            # and whether it needs a block.
            if tt == "PRINT":
                ops = 1            # one operand (what to print)
                block = False
                else_ = False
            elif tt == "VARIABLE":
                ops = 2            # variable name, value
                block = False
                else_ = False
            elif tt == "WHILELOOP":
                ops = 3            # left, operator, right (condition)
                block = True
                else_ = False
            elif tt == "FORLOOP":
                ops = 1            # count variable
                block = True
                else_ = False
            elif tt == "IF":
                ops = 3            # left, operator, right
                block = True
                else_ = True       # may have an ELSE branch
            elif tt == "CLASSDEF":
                ops = 1            # class name
                block = True
                else_ = False
            elif tt == "FUNCDEF":
                ops = 1            # function name
                block = True
                else_ = False
            elif tt == "INSTANTIATE":
                ops = 2            # class name, instance name
                block = False
                else_ = False
            elif tt == "SNIFF":
                ops = 2            # instance name, property name
                block = False
                else_ = False
            elif tt == "HUMP":
                ops = 2            # instance name, method name
                block = False
                else_ = False
            elif tt == "LOCALREVERSE":
                # Gather everything up to the matching closing LOCALREVERSE
                # token.  The whole stretch becomes one statement.
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
                # Any token that we don't recognise as a keyword is
                # treated as a stray literal.  We keep it as a
                # single‑token statement so that the reversal step
                # still sees it.
                stmts.append([tokens[start]])
                continue

            # ------------------------------------------------------------
            # Consume operands (just skip over them – they are validated
            # later during execution).
            # ------------------------------------------------------------
            for _ in range(ops):
                if ip >= len(tokens):
                    raise RuntimeError(f"Not enough operands for {tt}")
                ip += 1

            # ------------------------------------------------------------
            # Consume the mandatory `{ }` block, if any.
            # ------------------------------------------------------------
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

            # ------------------------------------------------------------
            # If the keyword supports an optional ELSE branch,
            # consume it now so that IF+ELSE stays as **one** statement.
            # ------------------------------------------------------------
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

            # All tokens from `start` up to (but not including) `ip`
            # form one complete statement.
            stmts.append(tokens[start:ip])

        return stmts

    def _execute(block_tokens, scope, top_level=False):
        """
        Walk through a list of tokens and execute them one by one.

        This is the heart of the interpreter.  It processes a flat
        sequence of tokens and performs the corresponding actions.

        Parameters:
        - block_tokens : the list of tokens for the current block
        - scope        : a dictionary of variable/function values
        - top_level    : True only for the outermost call; used to
                         catch illegal inter‑block tokens like
                         REVERSECODE.

        The function uses an instruction pointer `ip` that moves
        through the token list.  For keywords that contain their own
        bodies (IF, WHILE, FOR, CLASSDEF, FUNCDEF) the function
        *recursively* calls itself with the extracted body tokens.
        """
        ip = 0   # instruction pointer – where we are in the token list

        def resolve_value(val):
            """
            Interpret a token value string.

            If the string is a variable name that exists in 'scope',
            return its stored value.
            Otherwise, try to convert it to an integer.
            Otherwise, keep it as a string (used for LITERAL strings).
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

            # ============================================================
            #   PRINT (keyword: 8==D)
            # ------------------------------------------------------------
            # Prints the value of a variable or a literal string.
            # The next token is what to print.
            # ============================================================
            if ttype == "PRINT":
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("No value to print")
                next_type, next_val, next_raw = block_tokens[ip + 1]
                if next_type != "LITERAL":
                    raise RuntimeError("Invalid argument for PRINT")
                if next_val in scope:
                    print(scope[next_val])
                else:
                    print(next_val)
                ip += 2

            # ============================================================
            #   VARIABLE (keyword: ding dong / dingdong)
            # ------------------------------------------------------------
            # Creates or updates a variable.  The next token is the
            # variable name, the token after that is the value.
            # `resolve_value` is used so that `ding dong y x` copies
            # the *current value* of `x`, not the literal string "x".
            # ============================================================
            elif ttype == "VARIABLE":
                if ip + 2 >= len(block_tokens):
                    raise RuntimeError("Missing variable name or value")
                name_tok = block_tokens[ip + 1]
                val_tok  = block_tokens[ip + 2]
                if name_tok[0] != "LITERAL" or val_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid variable definition")
                name = name_tok[1]
                scope[name] = resolve_value(val_tok[1])
                ip += 3

            # ============================================================
            #   WHILELOOP (keyword: (()))
            # ------------------------------------------------------------
            # The condition is three tokens: left, operator, right.
            # The body is between { and }.
            # The condition is re‑evaluated before every iteration;
            # the loop stops when the condition becomes false.
            # ============================================================
            elif ttype == "WHILELOOP":
                if ip + 3 >= len(block_tokens):
                    raise RuntimeError("WHILELOOP missing condition")
                left_tok  = block_tokens[ip + 1]
                op_tok    = block_tokens[ip + 2]
                right_tok = block_tokens[ip + 3]
                if left_tok[0] != "LITERAL" or right_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid condition operands")
                ip += 4  # move past condition tokens

                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after WHILE condition")
                ip += 1
                start_body = ip
                depth = 1
                while ip < len(block_tokens) and depth > 0:
                    if block_tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif block_tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unmatched { for WHILE body")
                end_body = ip - 1
                while_body = block_tokens[start_body:end_body]

                # Repeatedly execute the body while the condition holds.
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
                continue

            # ============================================================
            #   FORLOOP (keyword: ))<>>((  -> forloop)
            # ------------------------------------------------------------
            # The next token is a variable whose value determines how
            # many times the body (inside { }) is repeated.
            # ============================================================
            elif ttype == "FORLOOP":
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("FORLOOP missing variable")
                var_tok = block_tokens[ip + 1]
                if var_tok[0] != "LITERAL":
                    raise RuntimeError("FORLOOP variable must be a literal")
                var_name = var_tok[1]
                count_val = resolve_value(var_name)
                if not isinstance(count_val, int):
                    raise RuntimeError("FORLOOP count must be an integer")
                ip += 2

                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after FORLOOP variable")
                ip += 1
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

                for _ in range(count_val):
                    _execute(for_body, scope)
                continue

            # ============================================================
            #   IF / ELSE (keyword: :3 / UwU)
            # ------------------------------------------------------------
            # The condition is three tokens: left, operator, right.
            # The IF body is between { and }.  An optional ELSE branch
            # starts with UwU and has its own { } block.
            # Exactly one branch is executed.
            # ============================================================
            elif ttype == "IF":
                if ip + 3 >= len(block_tokens):
                    raise RuntimeError("IF missing condition")
                left_tok  = block_tokens[ip + 1]
                op_tok    = block_tokens[ip + 2]
                right_tok = block_tokens[ip + 3]
                if left_tok[0] != "LITERAL" or right_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid condition operands")
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

                ip += 4
                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after IF condition")
                ip += 1
                start_if = ip
                depth = 1
                while ip < len(block_tokens) and depth > 0:
                    if block_tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif block_tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unmatched { for IF body")
                end_if = ip - 1
                if_block = block_tokens[start_if:end_if]

                # Optional ELSE part
                else_block = None
                if ip < len(block_tokens) and block_tokens[ip][0] == "ELSE":
                    ip += 1
                    if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                        raise RuntimeError("Expected { after else")
                    ip += 1
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

                if cond:
                    _execute(if_block, scope)
                elif else_block is not None:
                    _execute(else_block, scope)
                continue

            # ============================================================
            #   ELSE (UwU) outside an IF is illegal.
            # ============================================================
            elif ttype == "ELSE":
                raise RuntimeError("Unexpected ELSE without matching IF")

            # ============================================================
            #   REVERSECODE (keyword: peepee) – only allowed at top level.
            #   Inside a block it is an error.
            # ============================================================
            elif ttype == "REVERSECODE":
                raise RuntimeError("Unexpected REVERSECODE inside a block")

            # ============================================================
            #   LOCALREVERSE (keyword: dildo ... dildo)
            # ------------------------------------------------------------
            # Collects every token between two `dildo` markers as a raw
            # string, reverses the *characters* of that whole string,
            # re‑tokenizes it, and executes the result.
            # This is a *character‑level* reversal, not statement‑level.
            # ============================================================
            elif ttype == "LOCALREVERSE":
                j = ip + 1
                while j < len(block_tokens) and block_tokens[j][0] != "LOCALREVERSE":
                    j += 1
                if j >= len(block_tokens):
                    raise RuntimeError("Unclosed LOCALREVERSE")
                inner_tokens = block_tokens[ip + 1 : j]
                # Reconstruct the original source text from raw token strings.
                raw_source = " ".join(tok[2] for tok in inner_tokens)
                reversed_source = raw_source[::-1]
                reversed_tokens = tokenize(reversed_source)
                _execute(reversed_tokens, scope)
                ip = j + 1
                continue

            # ============================================================
            #   CLASSDEF (keyword: kcidyeknodimsoc)
            # ------------------------------------------------------------
            # Reads a class name (LITERAL) and a `{ }` block.
            # The class body is stored as a blueprint in `class_defs`.
            # When an instance is later created with INSTANTIATE,
            # this blueprint gets executed inside a fresh scope.
            # ============================================================
            elif ttype == "CLASSDEF":
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("CLASSDEF missing class name")
                name_tok = block_tokens[ip + 1]
                if name_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid class name")
                class_name = name_tok[1]
                ip += 2
                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after class name")
                ip += 1
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
                ip = end_body + 1
                continue

            # ============================================================
            #   FUNCDEF (keyword: kcidyeknod)
            # ------------------------------------------------------------
            # Defines a function (method) by storing its body inside the
            # current scope.  This body can later be called by HUMP.
            # ============================================================
            elif ttype == "FUNCDEF":
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("FUNCDEF missing function name")
                name_tok = block_tokens[ip + 1]
                if name_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid function name")
                func_name = name_tok[1]
                ip += 2
                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after function name")
                ip += 1
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
                scope[func_name] = func_body
                ip = end_body + 1
                continue

            # ============================================================
            #   INSTANTIATE (keyword: trafpir.yeknod)
            # ------------------------------------------------------------
            # Creates an instance of a previously defined class.
            # It looks up the class blueprint in `class_defs`,
            # executes it inside a fresh scope (so that variables
            # defined in the class become instance properties), and
            # stores that scope under the instance name.
            # ============================================================
            elif ttype == "INSTANTIATE":
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
                instance_scope = {}
                _execute(class_body, instance_scope)
                scope[instance_var] = instance_scope
                ip += 3
                continue

            # ============================================================
            #   SNIFF (keyword: ffins.yeknod)
            # ------------------------------------------------------------
            # Reads a property of an object.
            # First argument is the instance variable name,
            # second is the property name.  The value is printed.
            # ============================================================
            elif ttype == "SNIFF":
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
                print(value)
                ip += 3
                continue

            # ============================================================
            #   HUMP (keyword: pmuh.yeknod)
            # ------------------------------------------------------------
            # Calls a method on an object.
            # First argument is the instance variable name,
            # second is the method name.  The method body (stored as
            # a token list) is executed inside the instance's own scope.
            # ============================================================
            elif ttype == "HUMP":
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
                _execute(method_body, instance_data)
                ip += 3
                continue

            # ============================================================
            #   Stray token
            # ------------------------------------------------------------
            # If we encounter a token that was not consumed by any
            # recognised keyword, we just skip it (it is treated as
            # a no‑operation).  This can happen when a program contains
            # a mistyped keyword or a literal that wasn't meant to be used.
            # ============================================================
            else:
                ip += 1

    # ====================================================================
    # TOP‑LEVEL EXECUTION – pp67 reversal rule
    # ====================================================================
    if tokens and tokens[0][0] == "REVERSECODE":
        # The program starts with "peepee" → run forwards.
        del tokens[0]               # remove the REVERSECODE marker
        final_tokens = tokens       # keep the original order
    else:
        # No "peepee" → first group into statements,
        # then reverse the statement order, then flatten.
        stmts = _build_statements(tokens)
        stmts.reverse()
        final_tokens = [tok for stmt in stmts for tok in stmt]

    # Everything is ready – hand the final token list to the recursive executor.
    _execute(final_tokens, variables, top_level=True)


if __name__ == "__main__":
    # ---------------------------------------------------------------
    # Entry point.  By default, read "mainturd.pp".  You can pass a
    # different filename on the command line.
    # ---------------------------------------------------------------
    filename = "mainturd.pp"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    with open(filename, "r") as f:
        source = f.read()
    tokens = tokenize(source)
    run(tokens)
