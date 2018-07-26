class Pe(object):
    def __repr__(self):
        return self.__str__()
    def __or__(self,right):
        return Or(self,pe(right))
    def __and__(self,right):
        return seq(self,pe(right))
    def __xor__(self,right):
        return seq(self,lfold("", pe(right)))
    def __rand__(self,left):
        return seq(pe(left), self)
    def __add__(self,right):
        return seq(Many1(self),pe(right))
    def __mul__(self,right):
        return seq(Many(self),pe(right))
    def __truediv__ (self, right):
        return Or(self,pe(right))
    def __invert__(self):
        return Not(self)
    def __neq__(self):
        return Not(self)
    def __pos__(self):
        return And(self)
    def setg(self, peg):
        if hasattr(self, 'inner'):
            self.inner.setg(peg)
        if hasattr(self, 'left'):
            self.left.setg(peg)
            self.right.setg(peg)

cEmpty = 0
class Empty(Pe):
    __slots__ = ['ctag']
    def __init__(self):
        self.ctag = cEmpty
    def __str__(self):
        return "''"
EMPTY = Empty()

cChar  = 1
cRange = 2
cAny   = 3
class Char(Pe):
    __slots__ = ['ctag','a']
    def __init__(self, a):
        self.ctag = cChar
        self.a = a
    def __str__(self):
        return "'" + quote_str(self.a) + "'"

class Range(Pe):
    __slots__ = ['ctag', 'chars', 'ranges']
    def __init__(self, *ss):
        self.ctag = cRange
        chars = []
        ranges = []
        for s in ss :
            if len(s) == 3 and s[1] is '-':
                ranges.append((s[0], s[2]))
            else:
                for c in s:
                    chars.append(c)
        self.chars = tuple(chars)
        self.ranges = tuple(ranges)
    def __str__(self):
        l = tuple(map(lambda x: quote_str(x[0], ']')+'-'+quote_str(x[1], ']'), self.ranges))
        return "[" + ''.join(l) + quote_str(self.chars, ']') + "]"

class Any(Pe):
    __slots__ = ['ctag']
    def __init__(self):
        self.ctag = cAny
    def __str__(self):
        return '.'
ANY = Any()

cRef   = 4
class Ref(Pe):
    __slots__ = ['ctag', 'peg', 'name']
    def __init__(self, name, peg = None):
        self.ctag = cRef
        self.name = name
        self.peg = peg
    def __str__(self):
        return str(self.name)
    def setg(self, peg):
        self.peg = peg
    def isNonTerminal(self):
        return hasattr(self.peg, self.name)
    def getmemo(self,prefix):
        return self.peg.getmemo(prefix+self.name)
    def setmemo(self,prefix,value):
        return self.peg.setmemo(prefix+self.name,value)
    def deref(self):
        return getattr(self.peg, self.name).inner
    def prop(self):
        return getattr(self.peg, self.name)

cSeq   = 5
cOre   = 6
cAlt   = 7

class Seq(Pe):
    __slots__ = ['ctag', 'left', 'right']
    def __init__(self, left, right):
        self.ctag = cSeq
        self.left = pe(left)
        self.right = pe(right)
    def __str__(self):
        return quote_pe(self.left, inSeq) + ' ' + quote_pe(self.right, inSeq)
    def flatten(self, ls):
        if isinstance(self.left, Seq):
            self.left.flatten(ls)
        else:
            ls.append(self.left)
        if isinstance(self.right, Seq):
            self.right.flatten(ls)
        else:
            ls.append(self.right)
        return ls

class Or(Pe):
    __slots__ = ['ctag', 'left', 'right']
    def __init__(self, left, right):
        self.ctag = cOre
        self.left = pe(left)
        self.right = pe(right)
    def __str__(self):
        if self.right == EMPTY:
            return quote_pe(self.left, inUnary) + '?'
        return str(self.left) + ' / ' + str(self.right)
    def flatten(self, ls):
        if isinstance(self.left, Or):
            self.left.flatten(ls)
        else:
            ls.append(self.left)
        if isinstance(self.right, Or):
            self.right.flatten(ls)
        else:
            ls.append(self.right)
        return ls

cAnd = 8
cNot = 9

class And(Pe):
    __slots__ = ['ctag', 'inner']
    def __init__(self, inner):
        self.ctag = cAnd
        self.inner = pe(inner)
    def __str__(self):
        return '&' + quote_pe(self.inner, inUnary)

class Not(Pe):
    __slots__ = ['ctag', 'inner']
    def __init__(self, inner):
        self.ctag = cNot
        self.inner = pe(inner)
    def __str__(self):
        return '!' + quote_pe(self.inner, inUnary)

cMany = 10
cMany1 = 11

class Many(Pe):
    __slots__ = ['ctag', 'inner']
    def __init__(self, inner):
        self.ctag = cMany
        self.inner = pe(inner)
    def __str__(self):
        return quote_pe(self.inner, inUnary) + '*'

class Many1(Pe):
    __slots__ = ['ctag', 'inner']
    def __init__(self, inner):
        self.ctag = cMany1
        self.inner = pe(inner)
    def __str__(self):
        return quote_pe(self.inner, inUnary) + '+'

def quote_pe(e, f): return '(' + str(e) + ')' if f(e) else str(e)
def inSeq(e): return isinstance(e, Or)
def inUnary(e): return (isinstance(e, Or) and e.right != EMPTY) or isinstance(e, Seq)
def quote_str(e, esc = "'"):
    sb = []
    for c in e:
        if c == '\n' : sb.append(r'\n')
        elif c == '\t' : sb.append(r'\t')
        elif c == '\\' : sb.append(r'\\')
        elif c == '\r' : sb.append(r'\r')
        elif c in esc : sb.append('\\' + c)
        else: sb.append(c)
    return "".join(sb)

def pe(x):
    if x == 0 : return EMPTY
    if isinstance(x, str):
        if len(x) == 0:
            return EMPTY
        return Char(x)
    return x

def ref(name):
    if name.find('/') != -1:
        return lor(list(map(ref, name.split('/'))))
    if name.find(' ') != -1:
        return lseq(list(map(ref, name.split(' '))))
    if name.startswith('$'):
        return LinkAs("", Ref(name[1:]))
    return Ref(name)

def seq(x,y):
    if isinstance(y, Empty): return x
    return Seq(x, y)

def lseq(ls):
    if len(ls) > 1:
        return seq(ls[0], lseq(ls[1:]))
    if len(ls) == 1: return ls[0]
    return EMPTY

def lor(ls):
    if len(ls) > 1:
        return Or(ls[0], lor(ls[1:]))
    if len(ls) == 1: return ls[0]
    return EMPTY

def lfold(ltag,e):
    if isinstance(e, Many) and isinstance(e.inner, TreeAs):
        return Many(lfold(ltag, e.inner))
    if isinstance(e, Many1) and isinstance(e.inner, TreeAs):
        return Many1(lfold(ltag, e.inner))
    if isinstance(e, Or):
        return Or(lfold(ltag, e.left), lfold(ltag, e.right))
    if isinstance(e, TreeAs):
        return FoldAs(ltag, e.tag, pe(e.inner))
    return e

## Tree Construction

cTree = 12
cLink = 13
cFold = 14
cUnit = 15
cTAGs = 16

class TreeAs(Pe):
    __slots__ = ['ctag', 'tag', 'inner']
    def __init__(self, tag, inner):
        self.ctag = cTree
        self.tag = tag
        self.inner = pe(inner)
    def __str__(self):
        return self.tag + '{ ' + str(self.inner) + ' }'

class LinkAs(Pe):
    __slots__ = ['ctag', 'tag', 'inner']
    def __init__(self, tag, inner=None):
        self.ctag = cLink
        self.tag = tag
        self.inner = pe(inner)
    def __str__(self):
        if self.tag == '':
            return '$' + quote_pe(self.inner, inUnary)
        return '(' + self.tag + '=>' + str(self.inner) + ')'
    def __le__(self, right):
        return LinkAs(self.tag, right)
    def __ge__(self, right):
        return LinkAs(self.tag, right)
    def __mod__(self, right):
        return ref(right)
    def __xor__(self,right):
        return lfold(self.tag, pe(right))
N = LinkAs("")

class FoldAs(Pe):
    __slots__ = ['ctag', 'ltag', 'tag', 'inner']
    def __init__(self, ltag, tag, inner):
        self.ctag = cFold
        self.inner = pe(inner)
        self.ltag = ltag
        self.tag = tag
    def __str__(self):
        return self.ltag + '^' + self.tag +'{ ' + str(self.inner) + ' }'

class Detree(Pe):
    __slots__ = ['ctag', 'inner']
    def __init__(self, inner):
        self.ctag = cUnit
        self.inner = pe(inner)
    def __str__(self):
        return '@unit(' + str(self.inner) + ')'

class ParserContext:
    __slots__ = ['inputs', 'pos', 'headpos', 'ast']
    def __init__(self, inputs, pos = 0):
        self.inputs = inputs
        self.pos = pos
        self.headpos = pos
        self.ast = None

class ParseTree(object):
    __slots__ = ['tag', 'inputs', 'spos', 'epos', 'child']

    def __init__(self, tag, inputs, spos, epos, child):
        self.tag = tag
        self.inputs = inputs
        self.spos = spos
        self.epos = epos
        self.child = child

    def __str__(self):
        sb = []
        self.strOut(sb)
        return "".join(sb)

    def strOut(self, sb):
        sb.append("[#")
        sb.append(self.tag)
        c = len(sb)
        cur = self.child
        while cur != None:
            cur.strOut(sb)
            cur = cur.prev
        if c == len(sb):
            s = self.inputs[self.spos:self.epos]
            if isinstance(s, str):
                sb.append(" '")
                sb.append(s)
                sb.append("'")
            else:
                sb.append(" ")
                sb.append(str(s))
        sb.append("]")

    def asString(self):
        s = self.inputs[self.spos:self.epos]
        return s.decode('utf-8') if isinstance(s, bytes) else s

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        c = 0
        while(cur is not None):
            c += 1
            cur = cur.prev
        return c

    def __eq__(self, other):
        return self.tag == other

    def __getitem__(self, label):
        cur = self.child
        if isinstance(label, int):
            c = 0
            while (cur is not None):
                if c == label: return cur.child
                c += 1
                cur = cur.prev
        else :
            while(cur is not None):
                if label is cur.tag :return cur.child
                cur = cur.prev
        return None

    def asArray(self):
        a = []
        if self.child is not None:
            self.child.toArray(a)
        return a

class TreeLink(object):
    __slots__ = ['tag', 'child', 'prev']
    def __init__(self, tag, child, prev):
        self.tag = tag
        self.child = child
        self.prev = prev
    def strOut(self, sb):
        if self.child != None:
            if self.tag != None:
                ttag = '' if self.tag == '' else self.tag + "="
                sb.append(" " + ttag)
            self.child.strOut(sb)
    def toArray(self, a):
        if self.child != None:
            if self.prev != None:
                self.prev.toArray(a)
            if self.tag != None:
                a.append(self.child)

# Rule

class Rule(object):
    def __init__(self, name, inner):
        self.name = name
        self.inner = pe(inner)
        self.checked = False
    def __str__(self):
        return str(self.inner)
    def isConsumed(self):
        if not hasattr(self, 'nonnull'):
            self.nonnull = not isNullable(self.inner)
        return self.nonnull
    def treeState(self):
        if not hasattr(self, 'ts'):
            self.ts = treeState(self.inner)
        return self.ts
    def checkRule(self):
        if not self.checked:
            s0 = str(self.inner)
            if isRec(self.inner, self.name, {}):
                checkRec(self.inner, self.name, {})
            ts = treeState(self.inner)
            ts = treeCheck(self.inner, ts)
            s1 = str(self.inner)
            if s0 != s1:
                print(self.name, s0, s1)

## Grammar

class PEG(object):
    def __init__(self, ns = None):
        self.ns77 = ns
        self.memo77 = {}
        self.example77 = []
    def __getitem__(self, item):
        return getattr(self, item, None)
    def __setattr__(self, key, value):
        if isinstance(value, Pe):
            value.setg(self)
            if not isinstance(value, Rule):
                value = Rule(key, value)
            super().__setattr__(key, value)
            print(key, '=', value)
            if not hasattr(self, "start"):
                setattr(self, "start", value)
        else:
            super().__setattr__(key, value)

    def ns(self): return self.ns77
    def hasmemo(self, key): return key in self.memo77
    def getmemo(self, key): return self.memo77[key] if key in self.memo77 else None
    def setmemo(self, key, value): self.memo77[key] = value

    def example(self, prod, input, output = None):
        for name in prod.split(','):
            self.example77.append((name, input, output))
    def testAll(self, combinator):
        p = {}
        test = 0
        ok = 0
        for testcase in self.example77:
            name, input, output = testcase
            if not name in p: p[name] = combinator(self, name)
            res = p[name](input)
            t = str(res).replace(" b'", " '")
            if output == None:
                print(name, input, '=>', t)
            else:
                test += 1
                if t == output:
                    print('OK', name, input)
                    ok += 1
                else:
                    print('NG', name, input, output, '!=', t)
        if test > 0:
            print('OK', ok, 'FAIL', test - ok, ok / test * 100.0, '%')

## Properties

def isRec(pe: Pe, name: str, visited) -> bool:
    if isinstance(pe, Ref):
        if pe.name == name: return True
        if not pe.name in visited:
            visited[pe.name] = True
            return isRec(pe.deref(), name, visited)
    if hasattr(pe, 'inner'):
        return isRec(pe.inner, name, visited)
    if hasattr(pe, 'left'):
        res = isRec(pe.left, name, visited)
        return res if res == True else isRec(pe.right, name, visited)
    return False

def checkRec(pe: Pe, name: str, visited) -> bool:
    ctag = pe.ctag
    if ctag in (cChar,cRange,cAny):
        return False
    if ctag is Empty:
        return True
    if ctag is cSeq:
        return checkRec(pe.left, name, visited) and checkRec(pe.right, name, visited)
    if ctag in (cOre, cAlt):
        c0 = checkRec(pe.left, name, visited)
        c1 = checkRec(pe.right, name, visited)
        return c0 or c1
    if ctag in (cMany1, cTree, cFold, cLink, cUnit):
        return checkRec(pe.inner, name, visited)
    if ctag in (cNot, cMany, cAnd):
        checkRec(pe.inner, name, visited)
        return True
    if ctag is cRef:
        if pe.name == name:
            print("left recursion")
        if not pe.name in visited:
            visited[pe.name] = True
            checkRec(pe.deref(), name, visited)
        return not pe.prop().isConsumed()

Fnul = None
def isNullable(pe):
    global Fnul
    if Fnul is None:
        Fnul = [lambda x: False] * cTAGs
        def match(*ctags):
            def _match(func):
                global Fnul
                for ctag in ctags:
                    Fnul[ctag] = func
                return func
            return _match

        @match(cChar,cAny,cRange)
        def consumed(pe) : return True
        @match(cMany1, cLink, cTree, cFold, cUnit)
        def unary(pe) :
            return isNullable(pe.inner)
        @match(cSeq)
        def seq(pe) :
            if not isNullable(pe.left): return False
            return isNullable(pe.right)
        @match(cOre,cAlt)
        def ore(pe) :
            return isNullable(pe.left) and isNullable(pe.right)
        @match(cRef)
        def memo(pe: Ref) :
            if not pe.isNonTerminal():
                return True
            key = 'null'+pe.name
            memoed = pe.getmemo('null')
            if memoed == None:
                pe.setmemo('null', True)
                memoed = isNullable(pe.deref())
                pe.setmemo('null', memoed)
            return memoed
    return Fnul[pe.ctag](pe)

## TreeState
Fts = None
TUnit = 0
TTree = 1
TMut = 2
TFold = 3

def treeState(pe):
    global Fts
    if Fts is None:
        Fts = [lambda x: TUnit] * cTAGs
        def match(*ctags):
            def _match(func):
                global Fts
                for ctag in ctags:
                    Fts[ctag] = func
                return func
            return _match

        @match(cChar, cAny, cRange, cNot, cUnit)
        def stateUnit(pe): return TUnit
        @match(cTree)
        def stateTree(pe): return TTree
        @match(cLink)
        def stateMut(pe): return TMut
        @match(cFold)
        def stateFold(pe): return TFold
        @match(cSeq)
        def stateSeq(pe):
            ts0 = treeState(pe.left)
            return ts0 if ts0 != TUnit else treeState(pe.right)
        @match(cOre, cAlt)
        def stateAlt(pe):
            ts0 = treeState(pe.left)
            if ts0 != TUnit : return ts0
            ts1 = treeState(pe.right)
            return TMut if ts1 == TTree else ts1

        @match(cMany, cMany1, cAnd)
        def stateAlt(pe):
            ts0 = treeState(pe.inner)
            return TMut if ts0 == TTree else ts0

        @match(cRef)
        def memo(pe: Ref):
            if not pe.isNonTerminal(): return TUnit
            memoed = pe.getmemo('ts')
            if memoed == None:
                pe.setmemo('ts', TUnit)
                memoed = treeState(pe.deref())
                pe.setmemo('ts', memoed)
            return memoed

    return Fts[pe.ctag](pe)

Ftc = None
def treeCheck(pe, ts):
    global Ftc
    if Ftc is None:
        Ftc = [lambda e, ts: e] * cTAGs
        def match(*ctags):
            def _match(func):
                global Ftc
                for ctag in ctags:
                    Ftc[ctag] = func
                return func
            return _match

        @match(cTree)
        def checkTree(pe, ts):
            if ts == TUnit:
                return treeCheck(pe.inner, TUnit)
            if ts == TTree:
                pe.inner = treeCheck(pe.inner, TMut)
                return pe
            if ts == TMut:
                pe.inner = treeCheck(pe.inner, TMut)
                return LinkAs('', pe)
            if ts == TFold:
                pe.inner = treeCheck(pe.inner, TMut)
                return FoldAs('', pe.tag, pe.inner)

        @match(cLink)
        def checkLink(pe, ts):
            if ts == TUnit or ts == TFold:
                return treeCheck(pe.inner, TUnit)
            if ts == TTree:
                return treeCheck(pe.inner, TTree)
            if ts == TMut:
                ts0 = treeState(pe.inner)
                if ts0 == TUnit or ts0 == TFold: pe.inner = TreeAs('', treeCheck(pe.inner, TUnit))
                if ts0 == TTree: pe.inner = treeCheck(pe.inner, TTree)
                if ts0 == TMut: pe.inner = TreeAs('', treeCheck(pe.inner, TMut))
                return pe

        @match(cFold)
        def checkFold(pe, ts):
            if ts == TUnit:
                return treeCheck(pe.inner, TUnit)
            if ts == TTree:
                pe.inner = treeCheck(pe.inner, TMut)
                return TreeAs(pe.tag, pe.inner)
            if ts == TMut:
                pe.inner = treeCheck(pe.inner, TMut)
                return LinkAs(pe.ltag, pe.inner)
            if ts == TFold:
                pe.inner = treeCheck(pe.inner, TMut)
                return pe

        @match(cSeq)
        def checkSeq(pe, ts):
            if ts == TUnit or ts == TMut or ts == TFold:
                pe.left = treeCheck(pe.left, ts)
                pe.right = treeCheck(pe.right, ts)
                return pe
            ts0 = treeState(pe.left)
            if ts0 == TUnit:
                pe.left = treeCheck(pe.left, TUnit)
                pe.right = treeCheck(pe.right, ts)
                return pe
            if ts0 == TTree:
                pe.left = treeCheck(pe.left, TTree)
                pe.right = treeCheck(pe.right, TFold)
                return pe

        @match(cOre, cAlt)
        def checkAlt(pe, ts):
            pe.left = treeCheck(pe.left, ts)
            pe.right = treeCheck(pe.right, ts)
            return pe

        @match(cMany, cMany1)
        def checkMany(pe, ts):
            if ts == TUnit:
                pe.inner = treeCheck(pe.inner, TUnit)
                return pe
            if ts == TTree:
                pe.inner = treeCheck(pe.inner, TUnit)
                return TreeAs('', pe)
            if ts == TMut:
                ts0 = treeState(pe.inner)
                if ts0 == TUnit or ts0 == TFold: pe.inner = treeCheck(pe.inner, TUnit)
                if ts0 == TTree or ts0 == TMut: pe.inner = treeCheck(pe.inner, TMut)
                return pe
            if ts == TFold:
                pe.inner = treeCheck(pe.inner, TFold)
                return pe

        @match(cRef)
        def checkRef(pe: Ref, ts):
            if not pe.isNonTerminal(): return pe
            ts0 = treeState(pe)
            if ts == ts0: return pe
            if ts == TUnit: Detree(pe)
            if ts == TTree:
                if ts0 == TUnit or ts0 == TMut: return TreeAs('', pe)
                if ts0 == TFold: return seq(TreeAs('', EMPTY), pe)
            if ts == TMut:
                if ts0 == TUnit: return pe
                if ts0 == TTree: return LinkAs('', pe)
                if ts0 == TFold: return LinkAs('', seq(TreeAs('', EMPTY), pe))
            if ts == TFold:
                if ts0 == TUnit: return pe
                if ts0 == TTree: return FoldAs('', '', pe)
                if ts0 == TMut: return FoldAs('', '', TreeAs('', pe))

    return Ftc[pe.ctag](pe,ts)

def testRules(g: PEG):
    for name in dir(g):
        if not name[0].isupper(): continue
        p = getattr(g, name)
        p.checkRule()


## TPEG

def TPEGGrammar(g = None):
    if g == None: g = PEG('tpeg')

    # Preliminary
    __ = N % '__'
    _ = N % '_'
    EOS = N % 'EOS'

    g.Start = N%'__ Source EOF'
    g.EOF = ~ANY
    g.EOL = pe('\n') | pe('\r\n') | N%'EOF'
    g.COMMENT = '/*' & (~pe('*/') & ANY)* 0 & '*/' | '//' & (~(N%'EOL') & ANY)* 0
    g._ = (Range(' \t') | N%'COMMENT')* 0
    g.__ = (Range(' \t\r\n') | N%'COMMENT')* 0
    g.S = Range(' \t')

    g.Source = TreeAs('Source', (N%'$Statement')*0)
    "EOS = _ (';' _ / EOL (S/COMMENT) _ / EOL )*"
    g.EOS = N%'_' & (';' & N%'_' | N%'EOL' & (N%'S' | N%'COMMENT') & N%'_' | N%'EOL')* 0

    g.Statement = N%'Example/Production'

    g.Production = TreeAs('Production', N%'$Identifier __' & '=' & __ & (Range('/|') & __ |0) & N%'$Expression') & EOS

    g.Name = TreeAs('Name', N%'NAME')
    g.NAME = '"' & (pe(r'\"') | ~Range('\\"\n') & ANY)*0 & '"' | (~Range(' \t\r\n(,){};<>[|/*+?=^\'`') & ANY)+0

    g.Example = TreeAs('Example', 'example' & N%'S _ $Names $Doc') & EOS
    g.Names = TreeAs('', N%'$Identifier _' & (Range(',&') & N%'_ $Identifier _')*0)
    Doc1 = TreeAs("Doc", (~(N%'DELIM EOL') & ANY)* 0)
    Doc2 = TreeAs("Doc", (~Range('\r\n') & ANY)*0)
    g.Doc = N%'DELIM' & (N%'S'*0) & N%'EOL' & Doc1 & N % 'DELIM' | Doc2
    g.DELIM = pe("'''")

    g.Expression = N%'Choice' ^ (TreeAs('Alt', __ & '|' & _ & N%'$Expression')|0)
    g.Choice = N%'Sequence' ^ (TreeAs('Or', __ & '/' & _ & N%'$Choice')|0)
    g.SS = N%'S _' & ~(N%'EOL') | (N%'_ EOL')+0 & N%'S _'
    g.Sequence = N%'Predicate' ^ (TreeAs('Seq', N%'SS $Sequence')|0)

    g.Predicate = TreeAs('Not', '!' & N%'$Predicate') | TreeAs('And', '&' & N%'$Predicate') | TreeAs('Append', '$' & N%'_ $Predicate') | N%'Suffix'
    g.Suffix = N%'Term' ^ (TreeAs('Many', '*') | TreeAs('OneMore', '+') | TreeAs('Option', '?') | 0)

    g.Term = N%'Group/Char/Class/Any/Tree/Fold/BindFold/Bind/Func/Ref'
    g.Group = '(' & __ & N%'Expression/Empty' & __ & ')'

    g.Empty = TreeAs('Empty', EMPTY)
    g.Any = TreeAs('Any', '.')
    g.Char = "'" & TreeAs('Char', (r'\\' & ANY | ~Range("'\n") & ANY)*0) & "'"
    g.Class = '[' & TreeAs('Class', (r'\\' & ANY | ~Range("]") & ANY)*0) & ']'
    g.Tree = TreeAs('Tree', N%'Tag __' & (N%'$Expression __' | N%'$Empty') & '}' )
    g.Fold = '^' & _ & TreeAs('Fold', N%'Tag __' & (N%'$Expression __' | N%'$Empty') & '}' )
    g.Tag = (N%'$Identifier'|0) & '{'
    g.Identifier = TreeAs('Name', Range('A-Z', 'a-z', '@') & Range('A-Z', 'a-z', '0-9', '_.')*0)

    g.Bind = TreeAs('Bind', N%'$Var _' & '=>' & N%'_ $Expression')
    g.BindFold = TreeAs('Fold', N%'$Var _' & '^' & _ & N%'Tag __' & (N%'$Expression __' | N%'$Empty') & '}')
    g.Var = TreeAs('Name', Range('a-z', '$') & Range('A-Z', 'a-z', '0-9', '_')*0)

    g.Func = TreeAs('Func', N%'$Identifier' & '(' & (N%'$Expression _' & ',' & __)* 0 & N%'$Expression _' & ')')
    g.Ref = N%'Name'

    # Example
    g.example("Name", "abc")
    g.example("Name", '"abc"')
    g.example("COMMENT", "/*hoge*/hoge", "[# '/*hoge*/']")
    g.example("COMMENT", "//hoge\nhoge", "[# '//hoge']")

    g.example("Ref,Term,Expression", "a", "[#Name 'a']")

    g.example("Char,Expression", "''", "[#Char '']")
    g.example("Char,Expression", "'a'", "[#Char 'a']")
    g.example("Name,Expression", "\"a\"", "[#Name '\"a\"']")
    g.example("Class,Expression", "[a]", "[#Class 'a']")
    g.example("Func", "f(a)", "[#Func [#Name 'a'] [#Name 'f']]")
    g.example("Func", "f(a,b)", "[#Func [#Name 'b'] [#Name 'a'] [#Name 'f']]")
    g.example("Predicate,Expression", "&a", "[#And [#Name 'a']]")
    g.example("Predicate,Expression", "!a", "[#Not [#Name 'a']]")
    g.example("Suffix,Expression", "a?", "[#Option [#Name 'a']]")
    g.example("Suffix,Expression", "a*", "[#Many [#Name 'a']]")
    g.example("Suffix,Expression", "a+", "[#OneMore [#Name 'a']]")
    g.example("Expression", "{}", "[#Tree [#Empty '']]")
    g.example("Expression", "{ a }", "[#Tree [#Name 'a']]")
    g.example("Expression", "{ }", "[#Tree [#Empty '']]")
    g.example("Expression", "()", "[#Empty '']")
    g.example("Expression", "&'a'", "[#And [#Char 'a']]")

    g.example("Expression", "{a}", "[#Tree [#Name 'a']]")
    g.example("Expression", "Int{a}", "[#Tree [#Name 'a'] [#Name 'Int']]")
    g.example("Expression", "^{a}", "[#Fold [#Name 'a']]")
    g.example("Expression", "^Int{a}", "[#Fold [#Name 'a'] [#Name 'Int']]")
    g.example("Expression", "name^{a}", "[#Fold [#Name 'a'] [#Name 'name']]")
    g.example("Expression", "name^Int{a}", "[#Fold [#Name 'a'] [#Name 'Int'] [#Name 'name']]")
    g.example("Expression", "$a", "[#Append [#Name 'a']]")
    g.example("Expression", "name=>a", "[#Bind [#Name 'a'] [#Name 'name']]")
    g.example("Expression", "name => a", "[#Bind [#Name 'a'] [#Name 'name']]")

    g.example("Expression", "a a", "[#Seq [#Name 'a'] [#Name 'a']]")
    g.example("Expression", "a b c", "[#Seq [#Seq [#Name 'c'] [#Name 'b']] [#Name 'a']]")
    g.example("Expression", "a/b / c", "[#Or [#Or [#Name 'c'] [#Name 'b']] [#Name 'a']]")
    g.example("Statement", "A=a", "[#Production [#Name 'a'] [#Name 'A']]")
    g.example("Statement", "example A,B abc \n", "[#Example [#Doc 'abc '] [# [#Name 'B'] [#Name 'A']]]")
    g.example("Statement", "A = a\n  b", "[#Production [#Seq [#Name 'b'] [#Name 'a']] [#Name 'A']]")
    g.example("Start", "A = a; B = b;;",
                  "[#Source [#Production [#Name 'b'] [#Name 'B']] [#Production [#Name 'a'] [#Name 'A']]]")
    g.example("Start", "A = a\nB = b",
                  "[#Source [#Production [#Name 'b'] [#Name 'B']] [#Production [#Name 'a'] [#Name 'A']]]")
    g.example("Start", "A = a //hoge\nB = b",
                  "[#Source [#Production [#Name 'b'] [#Name 'B']] [#Production [#Name 'a'] [#Name 'A']]]")

    return g


class TreeConv(object):
    def parse(self, t:ParseTree):
        f = getattr(self, t.tag)
        return f(t)

class TPEGConv(TreeConv):
    def __init__(self, peg:PEG):
        self.peg = peg
    def load(self, path):
        self.peg = PEG(path)
        f = open(path, 'r')
        data = f.read()
        f.close()
        return self.peg
    def Source(self,t:ParseTree):
        for stmt in t.asArray():
            self.parse(stmt)
    def Example(self, t:ParseTree):
        names, input = t.asArray()
        for name in names:
            self.peg.example(name.asString(), input.asString())
    def Production(self, t:ParseTree):
        name, expr = t.asArray()
        setattr(self.peg, name.asString(), self.parse(expr))
    def Name(self, t:ParseTree):
        return Ref(t.asString())
    def Char(self, t:ParseTree):
        return pe(t.asString())
    def Class(self, t:ParseTree):
        return pe(t.asString())
    def Any(self, t:ParseTree):
        return ANY
    def Or(self,t:ParseTree):
        return lor(list(map(lambda x: self.parse(x), t.asArray())))
    def Seq(self,t:ParseTree):
        return lseq(list(map(lambda x: self.parse(x), t.asArray())))
    def Many(self,t:ParseTree):
        return Many(self.parse(t[0]))
    def Many1(self,t:ParseTree):
        return Many1(self.parse(t[0]))
    def Option(self,t:ParseTree):
        return Or(self.parse(t[0]), EMPTY)
    def And(self,t:ParseTree):
        return And(self.parse(t[0]))
    def Not(self,t:ParseTree):
        return Not(self.parse(t[0]))
    def Append(self,t:ParseTree):
        return LinkAs('', self.parse(t[0]))
    def Tree(self,t:ParseTree):
        if len(t) == 2:
            return TreeAs(t[0].asString(), self.parse(t[1]))
        return TreeAs('', self.parse(t[0]))
    def Link(self,t:ParseTree):
        if len(t) == 2:
            return LinkAs(t[0].asString(), self.parse(t[1]))
        return LinkAs('', self.parse(t[0]))
    def Fold(self,t:ParseTree):
        if len(t) == 3:
            return FoldAs(t[0].asString(), t[1].asString(), self.parse(t[3]))
        if len(t) == 2:
            return FoldAs('', t[0].asString(), self.parse(t[1]))
        return FoldAs('', '', self.parse(t[0]))

    def unquote(self, s):
        sb = []
        while len(s) > 0:
            if s.startswith('\\') and len(s) > 1:
                s = self.unesc(s, sb)
            else:
                sb.append(s[0])
                s = s[1:]
        return ''.join(sb)

