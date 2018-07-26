def lastIndexOf(e, delims):
    nested = 0
    i = len(e)-1
    while i > 0:
        c = e[i]
        if c == '(': nested += 1
        if c == ')': nested -= 1
        if nested == 0 and c in delims:
            return i
        i -= 1
    return -1

def calc(e: str):
    loc = lastIndexOf(e, '+-')
    if loc != -1:
        if e[loc] == '+':
            return calc(e[0:loc]) + calc(e[loc + 1:])
        else:
            return calc(e[0:loc]) - calc(e[loc + 1:])
    loc = lastIndexOf(e, '*/')
    if loc != -1:
        if e[loc] == '*':
            return calc(e[0:loc]) * calc(e[loc + 1:])
        else:
            return parse(e[0:loc]) / calc(e[loc + 1:])
    if e.startswith("(") and e.endswith(")"):
        return calc(e[1:-1])
    return int(e)

print(calc('1+2*3'))
print(calc('(1+2)*3'))
print(calc('1+2*3'))

class Expr(object):
    pass

class Val(Expr):
    __slots__ = ['val']
    def __init__(self, val):
        self.val = val
    def eval(self):
        return self.val

class Add(Expr):
    __slots__ = ['left', 'right']
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def eval(self):
        return self.left.eval() + self.right.eval()

class Sub(Expr):
    __slots__ = ['left', 'right']
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def eval(self):
        return self.left.eval() - self.right.eval()

class Mul(Expr):
    __slots__ = ['left', 'right']
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def eval(self):
        return self.left.eval() * self.right.eval()

class Div(Expr):
    __slots__ = ['left', 'right']
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def eval(self):
        return self.left.eval() / self.right.eval()

def parse(e: str):
    loc = lastIndexOf(e, '+-')
    if loc != -1:
        if e[loc] == '+':
            return Add(parse(e[0:loc]), parse(e[loc + 1:]))
        else:
            return Sub(parse(e[0:loc]), parse(e[loc + 1:]))
    loc = lastIndexOf(e, '*/')
    if loc != -1:
        if e[loc] == '*':
            return Mul(parse(e[0:loc]), parse(e[loc + 1:]))
        else:
            return Div(parse(e[0:loc]), parse(e[loc + 1:]))
    if e.startswith("(") and e.endswith(")"):
        return parse(e[1:-1])
    return Val(int(e))
