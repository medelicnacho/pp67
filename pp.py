# pp67 interpreter
#
# Pipeline:  preprocess (flip) -> tokenize (label) -> resolve_dildos (unwrap OOP) -> run (execute)
# Reversal:  lines bottom-to-top, words right-to-left.  No opt-out.
# Number offset:  you write N, pp67 stores N-1.  Not a bug.

import sys
import re


def preprocess(source):
    """Reverse line order and word order.

    pp67 reads code backwards: the last line executes first and words on
    each line are read right-to-left.  The programmer writes normally.
    This flips both axes so the tokeniser sees normal top-to-bottom,
    left-to-right order.
    """
    lines = source.split('\n')
    lines.reverse()
    result = []
    for line in lines:
        tokens = line.split()
        result.append(' '.join(reversed(tokens)) if tokens else '')
    return '\n'.join(result)


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
        LOCALREVERSE,
        BLOCKOPEN, BLOCKCLOSE,
        EQUALS, NOTEQUALS, GREATERTHAN, LESSTHAN,
        PLUS, MINUS, MULTIPLY, DIVIDE,
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
    source = source.replace("))<>((", "forloop")
    

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
        elif token == "deeznutz":
            result.append(("EQUALS", token, token))
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
        elif token == "diarea":
            result.append(("PLUS", token, token))
        elif token == "farticles":
            result.append(("MINUS", token, token))
        elif token == "ballzdeep":
            result.append(("MULTIPLY", token, token))
        elif token == "analcannon9000":
            result.append(("DIVIDE", token, token))
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


def resolve_dildo_tokens(tokens):
    """
    Pre‑pass that consumes every LOCALREVERSE token **before** the
    statement‑builder sees them.

    For each opening LOCALREVERSE token the function finds its closing
    partner (the very next LOCALREVERSE token).  The tokens *between*
    the two markers are joined into a single string using their raw
    representations, the string is character‑reversed, re‑tokenised,
    and inserted in place of the whole `dildo … dildo` span.

    After this pass the returned token list contains no LOCALREVERSE
    tokens at all, and the original LOCALREVERSE handling logic inside
    `_execute` and `_build_statements` is no longer needed.
    """
    out = []
    i = 0
    while i < len(tokens):
        if tokens[i][0] == "LOCALREVERSE":
            # Find the matching closing LOCALREVERSE token.
            j = i + 1
            while j < len(tokens) and tokens[j][0] != "LOCALREVERSE":
                j += 1
            if j >= len(tokens):
                raise RuntimeError("Unclosed LOCALREVERSE")
            # Everything between the two markers is the text to reverse.
            inner = tokens[i+1:j]
            # Reconstruct the original raw text so that we can
            # character‑reverse it exactly.
            raw = " ".join(tok[2] for tok in inner)
            rev_raw = raw[::-1]
            # Tokenise the character‑reversed segment.
            rev_tokens = tokenize(rev_raw)
            out.extend(rev_tokens)
            i = j + 1
        else:
            out.append(tokens[i])
            i += 1
    return out


def run(tokens):
    """Set up storage and hand control to the executor.

    What: creates the global variable dictionary and class blueprint
    dictionary, then calls _execute with the full token list.
    Why: initialises program memory before execution.
    """
    # variables = dictionary that holds all pp67 variables (global scope)
    variables = {}
    # OOP support: store class blueprints keyed by class name.
    # Each entry is now a dict with keys:
    #   'body'   : list of tokens forming the class body
    #   'parent' : str | None  (name of the parent class, if any)
    class_defs = {}



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

            # --- MATH ---  + - * //  (diarea / farticles / ballzdeep / analcannon9000)
            elif ttype in ("PLUS", "MINUS", "MULTIPLY", "DIVIDE"):
                if ip + 3 >= len(block_tokens):
                    raise RuntimeError(f"{ttype} missing operands")
                result_tok = block_tokens[ip + 1]
                left_tok   = block_tokens[ip + 2]
                right_tok  = block_tokens[ip + 3]
                if result_tok[0] != "LITERAL" or left_tok[0] != "LITERAL" or right_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid math operands")
                result_name = result_tok[1]
                left_val    = resolve_value(left_tok[1])
                right_val   = resolve_value(right_tok[1])
                if not isinstance(left_val, int) or not isinstance(right_val, int):
                    raise RuntimeError("Math operands must be numbers")
                if ttype == "PLUS":
                    scope[result_name] = left_val + right_val
                elif ttype == "MINUS":
                    scope[result_name] = left_val - right_val
                elif ttype == "MULTIPLY":
                    scope[result_name] = left_val * right_val
                elif ttype == "DIVIDE":
                    if right_val == 0:
                        raise RuntimeError("analcannon9000 by zero")
                    scope[result_name] = left_val // right_val
                ip += 4
                continue

            # ============================================================
            #   CLASSDEF (keyword: kcidyeknodimsoc)
            # ------------------------------------------------------------
            # Reads a class name (LITERAL) and a `{ }` block.
            # The class body is stored as a blueprint inside `class_defs`,
            # together with an optional parent name.
            #
            # *Inheritance detection*:
            #   While scanning the body tokens we look for a LITERAL
            #   token that contains a dot.  Its character‑reversed
            #   form should match `<Parent>.<Child>` where `<Child>`
            #   equals the current `class_name`.  If found we record
            #   `Parent` and strip the token from the stored body so
            #   it is not executed during instantiation.
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

                # --- inherit detection ---
                parent = None
                filtered_body = []
                for tok in class_body:
                    if tok[0] == "LITERAL" and "." in tok[1]:
                        # The token may be a character‑reversed
                        # inherit line such as `goD.laminA`.
                        rev = tok[1][::-1]          # e.g. "Animal.Dog"
                        if "." in rev and rev.split(".")[-1] == class_name:
                            if parent is not None:
                                raise RuntimeError(
                                    "Multiple inheritance lines for class "
                                    + class_name
                                )
                            parent = rev.split(".")[0]
                            # Do NOT keep this token in the body.
                            continue
                    filtered_body.append(tok)

                class_defs[class_name] = {
                    "body": filtered_body,
                    "parent": parent,
                }
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
            # resolves the parent chain (if any), and executes the
            # bodies from root ancestor to child in order, each
            # inside the same fresh scope, so that properties and
            # methods defined in ancestors are inherited.
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

                class_rec = class_defs.get(class_name)
                if class_rec is None:
                    raise RuntimeError(f"Class '{class_name}' not defined")
                if not isinstance(class_rec, dict):
                    raise RuntimeError("Class definition is corrupted")

                # Build the ancestor chain (root first, child last)
                def _chain(name, seen):
                    if name in seen:
                        raise RuntimeError("Circular inheritance detected")
                    rec = class_defs.get(name)
                    if rec is None:
                        raise RuntimeError(f"Class '{name}' not found")
                    chain = []
                    parent = rec.get("parent")
                    if parent:
                        chain = _chain(parent, seen | {name})
                    chain.append(rec)
                    return chain

                chain = _chain(class_name, set())

                instance_scope = {}
                for rec in chain:
                    _execute(rec["body"], instance_scope)

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
    # TOP‑LEVEL EXECUTION – pp67 reversal rule (double‑reversal for peepee)
    # ====================================================================
    # 1. Always group into statements and reverse once (run from bottom).
    _execute(tokens, variables, top_level=True)


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

    source = preprocess(source)

    tokens = tokenize(source)

    # Resolve all dildo (LOCALREVERSE) pairs at the token level
    # so that later stages see a clean stream without LOCALREVERSE
    # tokens.  This handles OOP keywords that appear inside dildo
    # blocks exactly the same as every other keyword.
    tokens = resolve_dildo_tokens(tokens)

    run(tokens)
