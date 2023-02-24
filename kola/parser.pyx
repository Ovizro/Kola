from .exception import KoiLangError, KoiLangSyntaxError, KoiLangCommandError


cdef class Parser:
    def __init__(self, BaseLexer lexer not None, command_set not None):
        self.lexer = lexer
        self.command_set = command_set
        self.t_cache = lexer.next_token()
    
    cpdef void push(self, Token n):
        n.next = self.stack_top
        self.stack_top = n
    
    cpdef Token pop(self):
        cdef Token n = self.stack_top
        if n is None:
            self.set_error(210)
        self.stack_top = n.next
        return n
    
    cdef void set_error(self, int errorno = 16, bint recovery = True) except *:
        cdef:
            int lineno = 1
            const char* text = ""
            Token cur = self.t_cache
        if not cur is None:
            lineno = self.t_cache.lineno
            if errorno == 16:
                errorno = (self.stat << 4) + cur.syn
            text = <const char*>cur.raw_val
        while recovery and not self.t_cache is None and not CMD <= self.t_cache.syn <= TEXT:
            self.t_cache = self.lexer.next_token()
        kola_set_error(KoiLangSyntaxError, errorno,
            self.lexer._filename, lineno, text)
    
    cpdef tuple parse_args(self):
        cdef:
            uint8_t stat = 1, action = 0
            
            list args = []
            dict kwds = {}
            object v
            Token i

        while True:
            self.stat = stat
            i = self.lexer.next_token()
            if i is None:
                stat = yy_goto[0][stat-1]
            else:
                stat = yy_goto[i.get_flag()][stat - 1]
            action = stat >> 4
            stat &= 0x0F

            if action == 1:
                args.append(i.val)
            elif action == 2:
                self.push(i)
            elif action == 3:
                args.append(self.pop().val)
            elif action == 4:
                v = self.pop().val
                i = self.pop()
                if not i.syn == LITERAL:
                    self.t_cache = i
                    self.set_error(201)
                kwds[i.val] = v
            elif action == 5:
                i = self.pop()
                if not i.syn == LITERAL:
                    self.t_cache = i
                    self.set_error(202)
                kwds[i.val] = v
            elif action == 6:
                v = [self.pop().val]
            elif action == 7:
                (<list>v).append(i.val)
            elif action == 8:
                v = {}
            elif action == 9:
                (<dict>v)[self.pop().val] = i.val
            elif action == 10:
                args.append(self.pop().val)
                self.push(i)

            if stat == 15:
                break
            elif stat == 0:
                self.t_cache = i
                self.set_error()
                
        if not self.stack_top is None:
            self.t_cache = self.stack_top
            self.stack_top = None
            self.set_error(16, False)

        self.t_cache = i
        return tuple(args), kwds
    
    cpdef object exec_once(self):
        cdef:
            str name
            tuple args
            dict kwds
            Token token

        token = self.t_cache
        if token is None:
            return
        
        args = self.parse_args()
        kwds = <dict>args[1]
        args = <tuple>args[0]

        if token.syn == CMD:
            name = <str>token.val
        elif token.syn == CMD_N:
            name = "@number"
            args = (token.val,) + args
        elif token.syn == TEXT:
            name = "@text"
            args = (token.val,)
        elif token.syn == ANNOTATION:
            name = "@annotation"
            args = (token.val,)

        try:
            cmd = self.command_set[name]
        except KeyError:
            if token.syn == ANNOTATION:
                return
            kola_set_errcause(KoiLangCommandError, 2, 
                self.lexer._filename, token.lineno, token.raw_val, None)
        
        try:
            return cmd(*args, **kwds)
        except KoiLangError:
            raise
        except Exception as e:
            if token.syn != TEXT:
                kola_set_errcause(KoiLangCommandError, 3, 
                    self.lexer._filename, token.lineno, token.raw_val, e)
            else:
                kola_set_errcause(KoiLangCommandError, 4, 
                    self.lexer._filename, token.lineno, token.raw_val, e)
    
    cpdef void exec(self) except *:
        while not self.t_cache is None:
            self.exec_once()

    def eof(self):
        return self.t_cache is None
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.t_cache is None:
            raise StopIteration
        ret = self.exec_once()
        return ret
    
    def __class_getitem__(cls, params):
        return cls
    
    def __repr__(self):
        return PyUnicode_FromFormat("<kola parser in file \"%s\">", self.lexer._filename)