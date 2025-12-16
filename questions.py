import random

def generate_mathematics_question() -> str:
    operands_num = random.randint(2, 5)
    #Needing to have at least one operand >= 90 wasn't in the spec?
    operands = [str(random.randint(1, 100)) for _ in range(operands_num - 1)]
    operands.append(str(random.randint(90, 100)))
    random.shuffle(operands)

    operators = random.choices(['+', '-'], k=operands_num - 1)

    expr_parts = []
    for i in range(operands_num - 1):
        expr_parts.append(operands[i])
        expr_parts.append(operators[i])
    expr_parts.append(operands[-1])
    return ' '.join(expr_parts)

def generate_roman_numerals_question() -> str:
    number = random.randint(1, 3999)

    vals = [
        (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
        (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
    ]

    roman_numeral = ""
    for (val, symbol) in vals:
        while number >= val:
            roman_numeral += symbol
            number -= val
    return roman_numeral
    
def generate_usable_addresses_question() -> str:
    base = [str(random.randint(1,223))] + [str(random.randint(0,255)) for _ in range(3)]
    prefix = random.randint(0, 32)
    return ".".join(base) + "/" + str(prefix)

def generate_network_broadcast_question() -> str:
    base = [str(random.randint(1,223))] + [str(random.randint(0,255)) for _ in range(3)]
    prefix = random.randint(0, 32)
    return ".".join(base) + "/" + str(prefix)