# pp67 Tutorial

> pp67 executes **backwards on two axes**: lines bottom-to-top, words
> right-to-left.  You write normally (top-to-bottom, left-to-right).
> The interpreter flips both.  Numbers are always off by 1.
> This is all correct behavior.

---

## 1. Hello, pp67

```
pp67 8==D
```

Word reversal turns this into `8==D pp67` (print "pp67"):

```
$ python3 pp.py
pp67
```

---

## 2. How Reversal Works — Two Axes

pp67 flips **both** the line order and the word order.  Every example
in this tutorial shows three stages: what you write, what the interpreter
sees after flipping, and the execution steps.

```
You write:                  Interpreter sees:        Execution:
donkey 8==D                 ding dong donkey poop    1. declare donkey = "poop"
poop donkey dong ding       8==D donkey              2. print donkey  -> poop
```

**Line axis:**  bottom line becomes top (runs first).
**Word axis:**  rightmost word on a line runs first.

Multi-word tokens (`ding dong`) reverse as a unit.  You write `dong ding`,
reversal puts them back together, tokenizer recognizes `ding dong`.

---

## 3. Variables

```
You write:                  Interpreter sees:        Execution:
donkey 8==D                 ding dong donkey poop    1. declare donkey = "poop"
poop donkey dong ding       8==D donkey              2. print donkey  -> poop
```

Copy a variable (uses the same reversal — `y` gets `x`'s value):

```
y 8==D
x y dong ding
poop x dong ding
```
-> prints **poop**

### Number Offset

**You write N.  pp67 stores N-1.**

```
lives 8==D
6 lives dong ding
```
-> stored as 5, prints **5**

---

## 4. Printing

`8==D` prints whatever comes after it (after reversal):

```
greeting 8==D
hello greeting dong ding
```
-> prints **hello**

```
count 8==D
7 count dong ding
```
-> prints **6**  (offset: 7 -> stored 6)

---

## 5. Math

Four prefix operators.  After reversal the keyword comes first,
then the result variable, then the two operands.

| Token | Op | You write | Means |
|-------|----|-----------|-------|
| `diarea` | + | `3 5 r diarea` | r = 5 + 3 |
| `farticles` | - | `3 8 r farticles` | r = 8 - 3 |
| `ballzdeep` | * | `3 4 r ballzdeep` | r = 4 * 3 |
| `analcannon9000` | // | `3 10 r analcannon9000` | r = 10 // 3 |

All integer math, floor division.  Division by stored-zero (write `1` as
divisor) raises an error.

```
You write:                  Interpreter sees:        Execution:
result 8==D                 diarea result 5 3        1. result = 4 + 2 = 6
3 5 result diarea           8==D result              2. print result -> 6
```
(5 stored as 4, 3 stored as 2 -> 4 + 2 = 6)

Chaining:
```
result 8==D
2 sum result ballzdeep
3 5 sum diarea
```
-> sum = 6, result = 6 * 2 = 12, prints **12**

---

## 6. Comparisons

| Token | Meaning |
|-------|---------|
| `deeznutz` | == |
| `!=` | != |
| `>` | > |
| `<` | < |

Used in `:3` (if) and `(())` (while) conditions.  After reversal the operator
sits between the two values.

---

## 7. If / Else

`if` = `:3`.  `else` = `UwU`.

### If (true branch)

```
You write:                  Interpreter sees:        Execution:
}                           ding dong x 5            1. x = 5 (stored 4)
x 8==D                      :3 x deeznutz 5 {        2. if 4 == 4 -> true
{ 5 deeznutz x :3           8==D x                   3. print x -> 4
5 x dong ding
```
Output: **4**

### If/else (false -> else branch)

```
You write:                  Interpreter sees:        Execution:
}                           ding dong x 5            1. x = 5 (stored 4)
yes 8==D                    :3 x deeznutz 4 {        2. if 4 == 3 -> false
{ UwU                       8==D no                  3. else: print yes -> yes
}                           UwU {
no 8==D                     8==D yes
{ 4 deeznutz x :3           }
5 x dong ding
```
Output: **yes**

Change `4` to `5` in the condition -> if-branch runs -> prints **no**.
(The names look swapped because bottom-to-top reaches the if-body
before the else-body in the source.)

### Structure rule — both axes matter

The `{` must be on the **same line** as `:3` (word axis).
The declaration must be **below** the if (line axis).

```
GOOD (both axes correct):               BAD (broken on different axes):
}                                        {
x 8==D                                   x 8==D
{ 5 deeznutz x :3                        }
5 x dong ding                            { 5 deeznutz x :3
                                         5 x dong ding

Why GOOD works:                          Why BAD breaks:
- { on same line as :3                   - { on its own line ->
  -> word reversal: :3 ... {               word reversal: { alone
- declaration at bottom                    then :3 on next line
  -> line reversal: runs first             -> IF can't find its {
```

---

## 8. While Loop

`(())` = while.  `{` must be on the same line as the condition.

```
You write:                  Interpreter sees:        Execution:
}                           ding dong count go       1. count = "go"
count 8==D                  (()) count != stop {     2. while "go" != "stop":
}                           8==D count                3.   count = "stop"
stop count dong ding        ding dong count stop     4.   print count -> stop
{ stop != count (())        }                        5. "stop" != "stop" -> exit
go count dong ding
```
Output: **stop**

---

## 9. For Loop

`))<>((` = repeat N times (N from a variable).  `{` on the same line.

```
You write:                  Interpreter sees:        Execution:
}                           ding dong x 4            1. x = 4 (stored 3)
}                           forloop x {              2. repeat 3 times:
loop 8==D                   8==D loop                 3.   print loop
{ x ))<>((                  }                        4.   print loop
4 x dong ding                                         5.   print loop
```
Output: **loop** (3 times)

Write `4` to loop 3 times (offset: 4 -> stored 3).

---

## 10. OOP — Classes and Objects

OOP keywords are character-reversed internally.  You wrap them in
`dildo ... dildo` to write them forward.  The interpreter flips the
characters between the markers.

### Define a class
```
dildo cosmicdonkeydick Entity dildo {
    name dong ding
    value health dong ding
}
```
`cosmicdonkeydick` -> `kcidyeknodimsoc` (CLASSDEF)

### Define a method
```
dildo donkeydick takeDamage dildo {
    damage 8==D
}
```
`donkeydick` -> `kcidyeknod` (FUNCDEF)

### Instantiate
```
dildo donkey.ripfart Entity dildo
```
`donkey.ripfart` -> `trafpir.yeknod` (INSTANTIATE)

### Read a property (sniff)
```
dildo donkey.sniff e health dildo
```
`donkey.sniff` -> `ffins.yeknod` (SNIFF) — prints the property value

### Call a method (hump)
```
dildo donkey.hump e takeDamage dildo
```
`donkey.hump` -> `pmuh.yeknod` (HUMP) — runs the method body

### Inheritance
```
dildo cosmicdonkeydick Dog dildo {
    dildo Animal.Dog dildo
    ...
}
```
The token `goD.laminA` (character-reversed `Animal.Dog`) is detected
and `Animal` is recorded as the parent.

### Full OOP example — what you write
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

### Full OOP example — what the interpreter sees (after dildo reversal)
```
pmuh.yeknod player takeDamage
ffins.yeknod player health
trafpir.yeknod Player

kcidyeknodimsoc Player {
    goD.laminA
    ding dong name PlayerOne

    kcidyeknod takeDamage {
        8==D ouch
    }
}

kcidyeknodimsoc Entity {
    ding dong position 0
    ding dong health 11
}
```
After word+line reversal: defines Entity, defines Player (inherits Entity),
creates Player instance, prints health, calls takeDamage -> prints **ouch**.

---

## 11. Cheat Sheet

| You write | Token | What |
|-----------|-------|------|
| `8==D` | PRINT | Print a value |
| `dong ding` | VARIABLE | Declare (`ding dong`) |
| `:3` | IF | If |
| `UwU` | ELSE | Else |
| `(())` | WHILELOOP | While |
| `))<>((` | FORLOOP | For |
| `deeznutz` | EQUALS | == |
| `diarea` | PLUS | + |
| `farticles` | MINUS | - |
| `ballzdeep` | MULTIPLY | * |
| `analcannon9000` | DIVIDE | // |

| OOP (inside dildo) | Raw | What |
|---------------------|-----|------|
| `cosmicdonkeydick` | `kcidyeknodimsoc` | Class |
| `donkeydick` | `kcidyeknod` | Method |
| `donkey.ripfart` | `trafpir.yeknod` | New |
| `donkey.sniff` | `ffins.yeknod` | Get |
| `donkey.hump` | `pmuh.yeknod` | Call |

---

## Remember

1. **Both axes reverse**: lines bottom-to-top AND words right-to-left
2. **Bottom = first**: put declarations and setup at the bottom of the file
3. **Same line = together**: put `{` on the same line as its keyword
4. **Numbers are off by 1**: you write N, it stores N-1
5. **OOP uses dildo**: wrap OOP keywords in `dildo ... dildo`
