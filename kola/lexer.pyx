from .exception import KoiLangCompileError


DEF BUFFER_SIZE = 1 << 14

# token syn
S_CMD = CMD
S_CMD_N = CMD_N
S_TEXT = TEXT
S_LITERAL = LITERAL


cdef class Token:
    def __init__(self, TokenSyn syn, val = None):
        self.syn = syn
        self.val = val
    
    def __repr__(self):
        if self.val is None:
            return PyUnicode_FromFormat("<token %d>", self.syn)
        else:
            return PyUnicode_FromFormat("<token %d: %R>", self.syn, <void*>self.val)
    

cdef class BaseLexer:
    def __cinit__(self):
        self._filename = "<stdin>"
        self.buffer = yy_create_buffer(stdin, BUFFER_SIZE)
        self.lineno = 1
    
    def __dealloc__(self):
        self.close()
    
    cpdef void ensure(self):
        yy_switch_to_buffer(self.buffer)
        yylineno = self.lineno
    
    cpdef void close(self):
        yy_delete_buffer(self.buffer)
        self.buffer = NULL
    
    cdef void set_error(self) except *:
        kola_set_error(KoiLangCompileError, self._filename, self.lineno, yytext)
    
    cdef Token next_koken(self):
        self.ensure()
        cdef:
            int syn = yylex()
            object val = None
        self.lineno = yylineno
        if syn == NUM or syn == CMD_N:
            val = PyLong_FromString(yytext, NULL, 10)
        elif syn == NUM_H:
            val = PyLong_FromString(yytext, NULL, 16)
        elif syn == NUM_B:
            val = PyLong_FromString(yytext, NULL, 2)
        elif syn == NUM_F:
            val = PyFloat_FromString(yytext)
        elif syn == CMD or syn == LITERAL or syn == TEXT or syn == STR:
            val = PyUnicode_FromStringAndSize(yytext, yyleng)
        elif syn == 0:
            self.set_error()
        elif syn == EOF:
            return None
        return Token(syn, val)

    @property
    def filename(self):
        return self._filename.decode()
    
    def __iter__(self):
        return self
    
    def __next__(self):
        token = self.next_koken()
        if token is None:
            raise StopIteration
        return token
    
    def __repr__(self):
        return PyUnicode_FromFormat("<kola lexer in file \"%s\" line %d>", self._filename, self.lineno)