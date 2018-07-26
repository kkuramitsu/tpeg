from tpeg import *
import parsefunc

# ParserFunction

def nez2_setup():
    def emit(pe): return pe.emit()

    Empty.emit = lambda self: parsefunc.true
    Any.emit = lambda self: parsefunc.any
    Char.emit = parsefunc.emit_Byte
    Range.emit = parsefunc.emit_ByteRange

    Seq.emit = lambda pe: parsefunc.emit_Seq(pe,emit)
    Or.emit = lambda pe: parsefunc.emit_Or(pe,emit)
    Not.emit = lambda pe: parsefunc.emit_Not(pe, emit)
    And.emit = lambda pe: parsefunc.emit_And(pe, emit)
    Many.emit = lambda pe: parsefunc.emit_Many(pe, emit)
    Many1.emit = lambda pe: parsefunc.emit_Many1(pe, emit)

    TreeAs.emit = lambda pe: parsefunc.emit_TreeAs(pe,emit, ParseTree)
    LinkAs.emit = lambda pe: parsefunc.emit_LinkAs(pe,emit, TreeLink)
    FoldAs.emit = lambda pe: parsefunc.emit_FoldAs(pe,emit, ParseTree, TreeLink)
    Detree.emit = lambda pe: parsefunc.emit_Unit(pe,emit)

    # Ref
    Ref.emit = lambda pe: parsefunc.emit_Ref(pe.peg, pe.name, "_DAsm_", emit)
    Rule.emit = lambda pe: parsefunc.emit_Rule(pe, emit)

class DAsmContext:
    __slots__ = ['inputs', 'length', 'pos', 'headpos', 'ast']
    def __init__(self, inputs, pos = 0):
        self.inputs = bytes(inputs, 'utf-8') if isinstance(inputs, str) else bytes(inputs)
        self.length = len(self.inputs)
        self.pos = pos
        self.headpos = pos
        self.ast = None

def dasm(peg: PEG, name = None):
    if isinstance(peg, Pe):
        f = peg.emit()
    else:
        if name == None: name = "start"
        f = parsefunc.emit_Ref(peg, name, "_DAsm_", lambda pe: pe.emit())
    def parse(s, pos = 0):
        px = DAsmContext(s, pos)
        if not f(px):
            return ParseTree("err", s, px.pos, len(s), None)
        if px.ast == None:
            return ParseTree("", s, pos, px.pos, None)
        return px.ast
    return parse

dasm_setup()
