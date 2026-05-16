import sys

def tokenize(source):
    """Convert pp67 source into a list of token tuples."""
    # Merge multi‑word keywords so that they become single tokens
    source = source.replace("ding dong", "dingdong")
    result = []
    for token in source.split():
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
        elif token == "peepee":
            result.append(("FORLOOP", token))
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
            # LITERAL token: if it is a number, subtract 1 and store the result
            try:
                num = int(token)
                adjusted = num - 1
                result.append(("LITERAL", str(adjusted)))
            except ValueError:
                result.append(("LITERAL", token))
    return result


def run(tokens):
    """Execute the tokenised pp67 program."""
    variables = {}

    def _execute(block_tokens, scope):
        ip = 0

        def resolve_value(val):
            if val in scope:
                return scope[val]
            try:
                return int(val)
            except ValueError:
                return val

        while ip < len(block_tokens):
            ttype, tval = block_tokens[ip]

            if ttype == "PRINT":
                if ip + 1 >= len(block_tokens):
                    raise RuntimeError("No value to print")
                next_type, next_val = block_tokens[ip + 1]
                if next_type != "LITERAL":
                    raise RuntimeError("Invalid argument for PRINT")
                if next_val in scope:
                    print(scope[next_val])
                else:
                    print(next_val)
                ip += 2

            elif ttype == "VARIABLE":
                if ip + 2 >= len(block_tokens):
                    raise RuntimeError("Missing variable name or value")
                name_tok = block_tokens[ip + 1]
                val_tok = block_tokens[ip + 2]
                if name_tok[0] != "LITERAL" or val_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid variable definition")
                name = name_tok[1]
                try:
                    value = int(val_tok[1])
                except ValueError:
                    value = val_tok[1]
                scope[name] = value
                ip += 3

            elif ttype == "FORLOOP":
                # FORLOOP is defined but not yet implemented.
                ip += 1

            elif ttype == "WHILELOOP":
                # WHILELOOP is defined but not yet implemented.
                ip += 1

            elif ttype == "IF":
                # Condition occupies the next three tokens:
                # left operand, operator, right operand
                if ip + 3 >= len(block_tokens):
                    raise RuntimeError("IF missing condition")
                left_tok = block_tokens[ip + 1]
                op_tok   = block_tokens[ip + 2]
                right_tok = block_tokens[ip + 3]

                if left_tok[0] != "LITERAL" or right_tok[0] != "LITERAL":
                    raise RuntimeError("Invalid condition operands")

                left_val = resolve_value(left_tok[1])
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

                ip += 4  # skip past condition tokens

                # Expect opening brace
                if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                    raise RuntimeError("Expected { after IF condition")
                ip += 1  # skip {
                start_if = ip

                # Find matching closing brace
                depth = 1
                while ip < len(block_tokens) and depth > 0:
                    if block_tokens[ip][0] == "BLOCKOPEN":
                        depth += 1
                    elif block_tokens[ip][0] == "BLOCKCLOSE":
                        depth -= 1
                    ip += 1
                if depth != 0:
                    raise RuntimeError("Unmatched { for IF body")
                end_if = ip - 1  # index of the closing }
                if_block = block_tokens[start_if:end_if]

                # Optional ELSE branch
                else_block = None
                if ip < len(block_tokens) and block_tokens[ip][0] == "ELSE":
                    ip += 1  # consume UwU
                    if ip >= len(block_tokens) or block_tokens[ip][0] != "BLOCKOPEN":
                        raise RuntimeError("Expected { after else")
                    ip += 1  # skip {
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

                # Execute the appropriate branch
                if cond:
                    _execute(if_block, scope)
                elif else_block is not None:
                    _execute(else_block, scope)

                # ip already points just past the whole IF/ELSE construct
                continue

            elif ttype == "ELSE":
                # An ELSE token outside of an IF construct is illegal
                raise RuntimeError("Unexpected ELSE without matching IF")

            else:
                # Stray tokens (e.g. an unused literal) are ignored.
                ip += 1

    _execute(tokens, variables)


if __name__ == "__main__":
    filename = "mainturd.pp"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    with open(filename, "r") as f:
        source = f.read()
    tokens = tokenize(source)
    run(tokens)
