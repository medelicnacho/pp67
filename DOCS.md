# pp67 Language Reference

## Fundamental Rule

pp67 executes **backwards on two axes**:

| Axis | Direction | What flips |
|------|-----------|------------|
| Lines | Bottom-to-top | Last line in the file runs first |
| Words | Right-to-left | Last word on a line runs first |

You write normally (top-to-bottom, left-to-right). The interpreter reverses both
axes before executing. There is no opt-out.

---

## Two Kinds of Reversal

### 1. Default — Word-Level Reversal

Every line has its words reversed. Every program uses this. Keywords like
`8==D`, `ding dong`, `deeznutz` are written with their words in the order
they'll appear after reversal.

```
You write:           After word reversal:     Execution order:
donkey 8==D          8==D donkey              (bottom line first ->
poop donkey dong ding ding dong donkey poop    ding dong donkey poop
                                               then 8==D donkey)
```

### 2. OOP — Character-Level Reversal (`dildo` blocks)

OOP keywords are written **character-by-character backwards**. Inside a
`dildo ... dildo` block, the characters are reversed so you can write them
in readable forward form.

| Forward (in dildo) | Backward (raw internal) | Meaning |
|---|---|---|
| `cosmicdonkeydick` | `kcidyeknodimsoc` | Class definition |
| `donkeydick` | `kcidyeknod` | Method definition |
| `donkey.ripfart` | `trafpir.yeknod` | Instantiate |
| `donkey.sniff` | `ffins.yeknod` | Property access |
| `donkey.hump` | `pmuh.yeknod` | Method call |

**Without `dildo` (raw — you never write this):**
```
kcidyeknodimsoc Entity {
    ...
}
```

**With `dildo` (readable — what you actually write):**
```
dildo cosmicdonkeydick Entity dildo {
    ...
}
```

The convention: always wrap OOP keywords in `dildo ... dildo` so the code
stays readable. The interpreter character-reverses the text between the
markers, re-tokenizes it, and the raw reversed forms become valid keywords.

---

## Number Offset

**You write N. pp67 stores N−1. Always.**

| You write | Stored | Printed |
|-----------|--------|---------|
| `1` | `0` | `0` |
| `5` | `4` | `4` |
| `6` | `5` | `5` |

This applies to variable values, math operands, loop counts, and comparison
operands. It is not a bug.

---

## Token Reference

### Print

| Token | Syntax (you write) | Behavior |
|-------|-------------------|----------|
| `8==D` | `name 8==D` | Prints the value stored in `name` |

```
donkey 8==D
poop donkey dong ding
```
-> declares donkey = "poop", then prints **poop**

---

### Variables

| Token | Syntax (you write) | Behavior |
|-------|-------------------|----------|
| `ding dong` | `value name dong ding` | Stores `value` in `name` |

Multi-word — you write `dong ding` so reversal restores `ding dong`.

```
poop donkey dong ding
```
-> declares variable `donkey` with value `"poop"`

Copy a variable:
```
x y dong ding
```
-> `y` gets the current value of `x`

---

### Math

Prefix notation — keyword comes first after reversal. You write operands
in reverse order.

| Token | Operation | Syntax (you write) | Meaning |
|-------|-----------|-------------------|---------|
| `diarea` | `+` | `right left result diarea` | result = left + right |
| `farticles` | `-` | `right left result farticles` | result = left - right |
| `ballzdeep` | `*` | `right left result ballzdeep` | result = left * right |
| `analcannon9000` | `/` | `right left result analcannon9000` | result = left / right |

All integer math with floor division. Division by stored-zero (write `1` as
divisor) raises an error.

```
sum 8==D
3 5 sum diarea
```
-> 5 stored as 4, 3 stored as 2. 4 + 2 = 6. Prints **6**.

---

### Comparisons

| Token | Meaning |
|-------|---------|
| `deeznutz` | `==` |
| `!=` | `!=` |
| `>` | `>` |
| `<` | `<` |

Used in `:3` (if) and `(())` (while) conditions.

---

### If / Else

| Token | Meaning |
|-------|---------|
| `:3` | If |
| `UwU` | Else |

The `{` opening the if-body must be on the **same line** as the `:3`
condition. Word reversal keeps same-line tokens together.

**If without else:**
```
}
x 8==D
{ 5 deeznutz x :3
5 x dong ding
```
-> x = 5 (stored 4), if 4 == 4 -> true, prints **4**

**If with else:**
```
}
yes 8==D
{ UwU
}
no 8==D
{ 4 deeznutz x :3
5 x dong ding
```
-> x = 5 (stored 4), if 4 == 3 -> false, else runs, prints **yes**

---

### While Loop

| Token | Meaning |
|-------|---------|
| `(())` | While |

Body repeats while condition is true. `{` must be on the same line as the
condition.

```
}
count 8==D
}
stop count dong ding
{ stop != count (())
go count dong ding
```
-> count starts as "go", body sets it to "stop", loop exits, prints **stop**

---

### For Loop

| Token | Meaning |
|-------|---------|
| `))<>((` | For (repeat N times) |

Takes a variable name. Loops N times where N is the variable's value.
`{` must be on the same line as `))<>((`.

```
}
}
loop 8==D
{ x ))<>(( 
4 x dong ding
```
-> x = 4 (stored 3), runs 3 times, prints **loop** three times

---

## OOP System

All OOP tokens are character-reversed internally. Always wrap them in
`dildo ... dildo` to write forward.

### Class Definition
```
dildo cosmicdonkeydick ClassName dildo {
    body
}
```
Raw internal: `kcidyeknodimsoc ClassName { body }`

### Method Definition
```
dildo donkeydick methodName dildo {
    body
}
```
Raw internal: `kcidyeknod methodName { body }`

### Instantiation
```
dildo donkey.ripfart ClassName dildo
```
Raw internal: `trafpir.yeknod ClassName instanceName`

Creates an object from a class blueprint. Runs ancestor class bodies in
inheritance order.

### Property Access (sniff)
```
dildo donkey.sniff instanceName propertyName dildo
```
Raw internal: `ffins.yeknod instanceName propertyName`

Reads and prints a property value from an instance.

### Method Call (hump)
```
dildo donkey.hump instanceName methodName dildo
```
Raw internal: `pmuh.yeknod instanceName methodName`

Calls a method on an instance, running its saved body.

### Inheritance

Inside a class body, write `Parent.Child` in reversed form inside `dildo`:
```
dildo cosmicdonkeydick Dog dildo {
    dildo Animal.Dog dildo
    ...
}
```
The interpreter detects `goD.laminA` (character-reversed from `Animal.Dog`),
records `Animal` as parent of `Dog`.

### Full OOP Example — What You Write (forward, with dildo)
```
dildo donkey.hump player takeDamage dildo
dildo donkey.sniff player health dildo
dildo donkey.ripfart Player dildo

dildo cosmicdonkeydick Player dildo {
    dildo Entity.Player dildo
    PlayerOne name dong ding

    dildo donkeydick takeDamage dildo {
        ouch 8==D
    }
}

dildo cosmicdonkeydick Entity dildo {
    0 position dong ding
    11 health dong ding
}
```

### Full OOP Example — What The Interpreter Sees (after dildo reversal)
```
pmuh.yeknod player takeDamage    -> call takeDamage on player
ffins.yeknod player health       -> print player's health
trafpir.yeknod Player            -> create Player instance

kcidyeknodimsoc Player {         -> define Player class
    goD.laminA                   -> inherits Entity
    ding dong name PlayerOne     -> property: name

    kcidyeknod takeDamage {      -> method: takeDamage
        8==D ouch                -> print "ouch"
    }
}

kcidyeknodimsoc Entity {         -> define Entity class
    ding dong position 0         -> property: position
    ding dong health 11          -> property: health (stored 10)
}
```

---

## Cheat Sheet

### Standard tokens
| You write | Token | What |
|-----------|-------|------|
| `8==D` | PRINT | Print a value |
| `dong ding` | VARIABLE | Declare (`ding dong`) |
| `:3` | IF | If condition |
| `UwU` | ELSE | Else branch |
| `(())` | WHILELOOP | While loop |
| `))<>((` | FORLOOP | For loop |
| `deeznutz` | EQUALS | `==` |
| `diarea` | PLUS | `+` |
| `farticles` | MINUS | `-` |
| `ballzdeep` | MULTIPLY | `*` |
| `analcannon9000` | DIVIDE | `/` |

### OOP tokens (inside dildo blocks)
| You write | Raw internal | What |
|-----------|-------------|------|
| `cosmicdonkeydick` | `kcidyeknodimsoc` | Define class |
| `donkeydick` | `kcidyeknod` | Define method |
| `donkey.ripfart` | `trafpir.yeknod` | Create instance |
| `donkey.sniff` | `ffins.yeknod` | Read property |
| `donkey.hump` | `pmuh.yeknod` | Call method |

---

## Rules

1. Lines execute bottom-to-top -- put what runs first at the bottom
2. Words execute right-to-left -- write tokens in reverse order per line
3. Numbers offset by -1 -- you write N, it stores N-1
4. `{` stays on the same line as its keyword
5. OOP always uses `dildo ... dildo` wrappers to stay readable
