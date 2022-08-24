cimport cython
from .exception import KoiLangSyntaxError


DEF BUFFER_SIZE = 1 << 14

# token syn
S_CMD = CMD
S_CMD_N = CMD_N
S_TEXT = TEXT
S_LITERAL = LITERAL
S_STRING = STRING
S_NUM = NUM
S_NUM_H = NUM_H
S_NUM_B = NUM_B
S_NUM_F = NUM_F
S_CLN = CLN
S_CMA = CMA
S_SLP = SLP
s_SRP = SRP


@cython.final
cdef class Token:
    """
    Token used in lexer

    Don't instantiate this class directly unless you make
    sure enough arguments provided.
    """
    def __init__(
            self,
            TokenSyn syn,
            val = None,
            *,
            int lineno = 0,
            bytes raw_val = None
        ):
        self.syn = syn
        self.val = val

        self.lineno = lineno or yylineno
        self.raw_val = raw_val or PyBytes_FromStringAndSize(yytext, yyleng)
    
    cpdef int get_flag(self):
        if self.syn <= TEXT:
            return 0
        elif self.syn == LITERAL:
            return 1
        elif self.syn <= NUM_F:
            return 2
        else:
            return self.syn - CLN + 3 
    
    def __repr__(self):
        if self.val is None:
            return PyUnicode_FromFormat("<token %d>", self.syn)
        else:
            return PyUnicode_FromFormat("<token %d: %R>", self.syn, <void*>self.val)
    

cdef class BaseLexer:
    """
    KoiLang lexer reading from stdin
    """
    def __cinit__(self):
        self._filename = "<stdin>"
        self.buffer = yy_create_buffer(stdin, BUFFER_SIZE)
        self.lineno = 1
    
    def __dealloc__(self):
        self.close()
    
    cpdef void ensure(self):
        """
        synchronize buffer data in yylex
        """
        yy_switch_to_buffer(self.buffer)
        yylineno = self.lineno
    
    cpdef void close(self):
        yy_delete_buffer(self.buffer)
        self.buffer = NULL
    
    cdef void set_error(self) except *:
        cdef int errno = 1
        
        # correct lineno and set error
        cdef bint c = strchr(yytext, ord('\n')) != NULL
        cdef int lineno = self.lineno
        if c or yytext[0] == 0:
            lineno -= c
            errno = 10
        kola_set_error(KoiLangSyntaxError, errno, self._filename, lineno, yytext)
    
    cdef Token next_token(self):
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
        elif syn == CMD or syn == LITERAL:
            val = PyUnicode_FromStringAndSize(yytext, yyleng)
        elif syn == TEXT:
            val = PyUnicode_FromStringAndSize(yytext, yyleng).replace("\\\n", '').replace("\\\r\n", '')
        elif syn == STRING:
            val = PyUnicode_FromStringAndSize(yytext + 1, yyleng - 2).replace("\\\n", '').replace("\\\r\n", '')
        elif syn == 0:
            self.set_error()
        elif syn == EOF:
            return None
        return Token(syn, val)

    @property
    def filename(self):
        return self._filename.decode()
    
    @property
    def _cur_text(self):
        return PyUnicode_FromStringAndSize(yytext, yyleng)
    
    def __iter__(self):
        return self
    
    def __next__(self):
        token = self.next_token()
        if token is None:
            raise StopIteration
        return token
    
    def __repr__(self):
        return PyUnicode_FromFormat("<kola lexer in file \"%s\" line %d>", self._filename, self.lineno)


cdef class FileLexer(BaseLexer):
    """
    KoiLang lexer reading from file
    """
    def __cinit__(self, str filename not None):
        self._filenameo = filename.encode()
        self._filename = <char*>self._filenameo

        self.fp = fopen(self._filename, "r")
        if self.fp == NULL:
            PyErr_Format(OSError, "fail to open %s", self._filename)

        self.buffer = yy_create_buffer(self.fp, BUFFER_SIZE)
        self.lineno = 1
    
    cpdef void close(self):
        yy_delete_buffer(self.buffer)
        self.buffer = NULL
        if self.fp:
            fclose(self.fp)
            self.fp = NULL


cdef class StringLexer(BaseLexer):
    """
    KoiLang lexer reading from string provided
    """
    def __cinit__(self, str content not None):
        self._filename = "<string>"
        self.content = content.encode()
        self.buffer = yy_scan_bytes(self.content, len(self.content))
        self.lineno = 1