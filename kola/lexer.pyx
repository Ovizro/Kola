# distutils: sources = kola/lex.yy.c
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
S_SRP = SRP


@cython.final
cdef class Token:
    """
    Token used in lexer

    Don't instantiate this class directly unless you make
    sure enough arguments provided.
    """
    def __cinit__(
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
    
    def __eq__(self, other):
        return self is other or self.syn == other
    
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
    def __cinit__(self, *args, uint8_t stat = 0):
        if type(self) is BaseLexer:
            if args:
                PyErr_Format(TypeError, "__cinit__() takes exactly 0 positional arguments (%d given)", len(args))
            self.buffer = yy_create_buffer(stdin, BUFFER_SIZE)
        self._filename = "<stdin>"
        self.lineno = 1
        if stat > 2:
            raise ValueError("lexer state must be between 0 and 2")
        self.stat = stat
    
    def __dealloc__(self):
        self.close()
    
    cpdef void ensure(self):
        """
        synchronize buffer data in yylex
        """
        global yylineno
        yy_switch_to_buffer(self.buffer)
        yylineno = self.lineno
        set_stat(self.stat)
    
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
        if self.buffer == NULL:
            raise OSError("operation on closed lexer")

        self.ensure()
        cdef:
            int syn = yylex()
            object val = None
        self.lineno = yylineno
        self.stat = get_stat()
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
            val = PyUnicode_FromStringAndSize(yytext, yyleng)
            val = <str>filter_text(val)
        elif syn == STRING:
            try:
                val = decode_string(yytext + 1, yyleng - 2)
            except Exception as e:
                kola_set_errcause(KoiLangSyntaxError, 4, self._filename, self.lineno, yytext, e)
        elif syn == 0:
            self.set_error()
        elif syn == EOF:
            return None
        return Token(syn, val)

    @property
    def filename(self):
        return self._filename.decode()
    
    @property
    def closed(self):
        return self.buffer == NULL
    
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
    def __cinit__(self, str filename not None, *, uint8_t stat = 0):
        self._filenameo = filename.encode()
        self._filename = <char*>self._filenameo

        self.fp = fopen(self._filename, "r")
        if self.fp == NULL:
            PyErr_Format(OSError, "fail to open %s", self._filename)

        self.buffer = yy_create_buffer(self.fp, BUFFER_SIZE)
    
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
    def __cinit__(self, str content not None, *, uint8_t stat = 0):
        self._filename = "<string>"
        self.content = content.encode()
        self.buffer = yy_scan_bytes(self.content, len(self.content))