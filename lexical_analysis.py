from tokens import *
from errors import *

class LexicalAnalyzer:
  def __init__(self, fn, text):
    self.fn = fn
    self.text = text
    self.pos = Position(-1, 0, -1, fn, text)
    self.current_char = None
    self.next()
  
  def next(self):
    self.pos.next(self.current_char)
    self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None

  def init_tokens(self):
    tokens = []

    while self.current_char != None:
      if self.current_char in ' \t':
        self.next()
      elif self.current_char == '#':
        self.skip_comment()
      elif self.current_char in ';\n':
        tokens.append(Token(TKN_NEWLINE, start=self.pos))
        self.next()
      elif self.current_char in DIGITS:
        tokens.append(self.la_number())
      elif self.current_char in LETTERS:
        tokens.append(self.la_identifier())
      elif self.current_char == '"':
        tokens.append(self.la_string())
      elif self.current_char == '+':
        tokens.append(Token(TKN_PLUS, start=self.pos))
        self.next()
      elif self.current_char == '-':
        tokens.append(Token(TKN_MINUS, start=self.pos))
        self.next()
      elif self.current_char == '*':
        tokens.append(Token(TKN_MUL, start=self.pos))
        self.next()
      elif self.current_char == '/':
        tokens.append(Token(TKN_DIV, start=self.pos))
        self.next()
      elif self.current_char == '%':
        tokens.append(Token(TKN_MODULO, start=self.pos))
        self.next()
      elif self.current_char == '^':
        tokens.append(Token(TKN_POW, start=self.pos))
        self.next()
      elif self.current_char == '(':
        tokens.append(Token(TKN_LPAREN, start=self.pos))
        self.next()
      elif self.current_char == ')':
        tokens.append(Token(TKN_RPAREN, start=self.pos))
        self.next()
      elif self.current_char == '[':
        tokens.append(Token(TKN_LSQUARE, start=self.pos))
        self.next()
      elif self.current_char == ']':
        tokens.append(Token(TKN_RSQUARE, start=self.pos))
        self.next()
      elif self.current_char == '!':
        token, error = self.la_not_equals()
        if error: return [], error
        tokens.append(token)
      elif self.current_char == '=':
        tokens.append(self.la_equals())
      elif self.current_char == '<':
        tokens.append(self.la_less_than())
      elif self.current_char == '>':
        tokens.append(self.la_greater_than_or_arrow())
      elif self.current_char == ',':
        tokens.append(Token(TKN_COMMA, start=self.pos))
        self.next()
      else:
        start = self.pos.copy()
        char = self.current_char
        self.next()
        return [], IllegalCharError(start, self.pos, "'" + char + "'")

    tokens.append(Token(TKN_EOF, start=self.pos))
    return tokens, None

  def la_number(self):
    num_str = ''
    dot_count = 0
    start = self.pos.copy()

    while self.current_char != None and self.current_char in DIGITS + '.':
      if self.current_char == '.':
        if dot_count == 1: break
        dot_count += 1
      num_str += self.current_char
      self.next()

    if dot_count == 0:
      return Token(TKN_INT, int(num_str), start, self.pos)
    else:
      return Token(TKN_FLOAT, float(num_str), start, self.pos)

  def la_string(self):
    string = ''
    start = self.pos.copy()
    escape_character = False
    self.next()

    escape_characters = {
      'n': '\n',
      't': '\t'
    }

    while self.current_char != None and (self.current_char != '"' or escape_character):
      if escape_character:
        string += escape_characters.get(self.current_char, self.current_char)
      else:
        if self.current_char == '\\':
          escape_character = True
        else:
          string += self.current_char
      self.next()
      escape_character = False
    
    self.next()
    return Token(TKN_STRING, string, start, self.pos)

  def la_identifier(self):
    id_str = ''
    start = self.pos.copy()

    while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
      id_str += self.current_char
      self.next()

    tok_type = TKN_KEYWORD if id_str in KEYWORDS else TKN_IDENTIFIER
    return Token(tok_type, id_str, start, self.pos)

  def la_not_equals(self):
    start = self.pos.copy()
    self.next()

    if self.current_char == '=':
      self.next()
      return Token(TKN_NE, start=start, end=self.pos), None

    self.next()
    return None, ExpectedCharError(start, self.pos, "'=' (after '!')")
  
  def la_equals(self):
    tok_type = TKN_EQ
    start = self.pos.copy()
    self.next()

    if self.current_char == '=':
      self.next()
      tok_type = TKN_EE

    return Token(tok_type, start=start, end=self.pos)

  def la_less_than(self):
    tok_type = TKN_LT
    start = self.pos.copy()
    self.next()

    if self.current_char == '=':
      self.next()
      tok_type = TKN_LTE

    return Token(tok_type, start=start, end=self.pos)

  def la_greater_than_or_arrow(self):
    tok_type = TKN_GT
    start = self.pos.copy()
    self.next()

    if self.current_char == '=':
      self.next()
      tok_type = TKN_GTE
    elif self.current_char == '>':
      self.next()
      tok_type = TKN_ARROW

    return Token(tok_type, start=start, end=self.pos)

  def skip_comment(self):
    self.next()

    while self.current_char != '\n':
      self.next()

    self.next()