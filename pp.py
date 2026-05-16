open file "mainturd.pp"
read entire contents as a string
split string into words and symbols

create empty list called tokens

for each word/symbol in the string:
    if it equals 8==D
        add PRINT token to list
    if it equals (())
        add WHILELOOP token to list
    if it equals :3
        add IF token to list
    if it equals UwU
        add ELSE token to list
    if it equals ding dong
        add VARIABLE token to list
    if it equals peepee
        add FORLOOP token to list

return token list

---

for each token in token list:

    if token is PRINT
        look at next token
        print whatever it says

    if token is VARIABLE
        look at next two tokens
        first token is the name
        second token is the value
        store it

    if token is WHILELOOP
        keep looping the code inside
        until condition is false or program cancels

    if token is FORLOOP
        loop until it reaches the defined end
        then stop

    if token is IF
        check the condition
        if true run the code inside

    if token is ELSE
        if the IF was false run this instead