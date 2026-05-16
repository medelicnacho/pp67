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
        else:
            result.append(("LITERAL", token))
    return result

def run(tokens):
    """Execute the tokenised pp67 program."""
    ip = 0
    variables = {}
    while ip < len(tokens):
        ttype, tval = tokens[ip]

        if ttype == "PRINT":
            if ip + 1 >= len(tokens):
                raise RuntimeError("No value to print")
            next_type, next_val = tokens[ip + 1]
            # A literal after PRINT is either a plain string or a variable name.
            if next_type == "LITERAL":
                if next_val in variables:
                    print(variables[next_val])
                else:
                    print(next_val)
            else:
                raise RuntimeError("Invalid argument for PRINT")
            ip += 2

        elif ttype == "VARIABLE":
            if ip + 2 >= len(tokens):
                raise RuntimeError("Missing variable name or value")
            name_tok = tokens[ip + 1]
            val_tok = tokens[ip + 2]
            if name_tok[0] != "LITERAL" or val_tok[0] != "LITERAL":
                raise RuntimeError("Invalid variable definition")
            name = name_tok[1]
            # Try to convert the value to an integer for convenience
            try:
                value = int(val_tok[1])
            except ValueError:
                value = val_tok[1]
            variables[name] = value
            ip += 3

        elif ttype == "FORLOOP":
            # FORLOOP is defined but not yet implemented.
            # Skip it for now.
            ip += 1

        elif ttype == "WHILELOOP":
            ip += 1

        elif ttype == "IF":
            ip += 1

        elif ttype == "ELSE":
            ip += 1

        else:
            # Skip any stray literal that isn't consumed by a command.
            ip += 1

if __name__ == "__main__":
    filename = "mainturd.pp"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    with open(filename, "r") as f:
        source = f.read()
    tokens = tokenize(source)
    run(tokens)
