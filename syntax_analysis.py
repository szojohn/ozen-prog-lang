from tokens import *
from nodes import *
from errors import *

class ParseResult:
  def __init__(self):
    self.error = None
    self.node = None
    self.last_registered_next_count = 0
    self.next_count = 0
    self.to_reverse_count = 0

  def register_next(self):
    self.last_registered_next_count = 1
    self.next_count += 1

  def register(self, result):
    self.last_registered_next_count = result.next_count
    self.next_count += result.next_count
    if result.error: self.error = result.error
    return result.node

  def try_register(self, result):
    if result.error:
      self.to_reverse_count = result.next_count
      return None
    return self.register(result)

  def success(self, node):
    self.node = node
    return self

  def failure(self, error):
    if not self.error or self.last_registered_next_count == 0:
      self.error = error
    return self

# PARSER

class Parser:
  def __init__(self, tkns):
    self.tkns = tkns
    self.tkn_index = -1
    self.next()

  def next(self):
    self.tkn_index += 1
    self.update_current_tkn()
    return self.current_tkn

  def reverse(self, amount=1):
    self.tkn_index -= amount
    self.update_current_tkn()
    return self.current_tkn

  def update_current_tkn(self):
    if self.tkn_index >= 0 and self.tkn_index < len(self.tkns):
      self.current_tkn = self.tkns[self.tkn_index]

  def parse(self):
    result = self.statements()
    if not result.error and self.current_tkn.type != TKN_EOF:
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        "Token cannot appear after previous tokens"
      ))
    return result

  ###################################

  def statements(self):
    result = ParseResult()
    statements = []
    start = self.current_tkn.start.copy()

    while self.current_tkn.type == TKN_NEWLINE:
      result.register_next()
      self.next()

    statement = result.register(self.statement())
    if result.error: return result
    statements.append(statement)

    more_statements = True

    while True:
      newline_count = 0
      while self.current_tkn.type == TKN_NEWLINE:
        result.register_next()
        self.next()
        newline_count += 1
      if newline_count == 0:
        more_statements = False
      
      if not more_statements: break
      statement = result.try_register(self.statement())
      if not statement:
        self.reverse(result.to_reverse_count)
        more_statements = False
        continue
      statements.append(statement)

    return result.success(ListNode(
      statements,
      start,
      self.current_tkn.end.copy()
    ))

  def statement(self):
    result = ParseResult()
    start = self.current_tkn.start.copy()

    if self.current_tkn.matches(TKN_KEYWORD, 'return'):
      result.register_next()
      self.next()

      expr = result.try_register(self.expr())
      if not expr:
        self.reverse(result.to_reverse_count)
      return result.success(ReturnNode(expr, start, self.current_tkn.start.copy()))
    
    if self.current_tkn.matches(TKN_KEYWORD, 'continue'):
      result.register_next()
      self.next()
      return result.success(ContinueNode(start, self.current_tkn.start.copy()))
      
    if self.current_tkn.matches(TKN_KEYWORD, 'break'):
      result.register_next()
      self.next()
      return result.success(BreakNode(start, self.current_tkn.start.copy()))

    expr = result.register(self.expr())
    if result.error:
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        "Expected 'return', 'continue', 'break', 'let', 'if', 'for', 'while', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'not'"
      ))
    return result.success(expr)

  def expr(self):
    result = ParseResult()

    if self.current_tkn.matches(TKN_KEYWORD, 'let'):
      result.register_next()
      self.next()

      if self.current_tkn.type != TKN_IDENTIFIER:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          "Expected identifier"
        ))

      var_name = self.current_tkn
      result.register_next()
      self.next()

      if self.current_tkn.type != TKN_EQ:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          "Expected '='"
        ))

      result.register_next()
      self.next()

      expr = result.register(self.expr())
      if result.error: return result
      return result.success(VarAssignNode(var_name, expr))

    node = result.register(self.bin_op(self.comp_expr, ((TKN_KEYWORD, 'and'), (TKN_KEYWORD, 'or'))))

    if result.error:
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        "Expected 'let', 'if', 'for', 'while', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'not'"
      ))

    return result.success(node)

  def comp_expr(self):
    result = ParseResult()

    if self.current_tkn.matches(TKN_KEYWORD, 'not'):
      op_tkn = self.current_tkn
      result.register_next()
      self.next()

      node = result.register(self.comp_expr())
      if result.error: return result
      return result.success(UnaryOpNode(op_tkn, node))
    
    node = result.register(self.bin_op(self.arith_expr, (TKN_EE, TKN_NE, TKN_LT, TKN_GT, TKN_LTE, TKN_GTE)))
    
    if result.error:
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        "Expected int, float, identifier, '+', '-', '(', '[', 'if', 'for', 'while', 'FUN' or 'not'"
      ))

    return result.success(node)

  def arith_expr(self):
    return self.bin_op(self.term, (TKN_PLUS, TKN_MINUS))

  def term(self):
    return self.bin_op(self.factor, (TKN_MUL, TKN_DIV))

  def factor(self):
    result = ParseResult()
    tkn = self.current_tkn

    if tkn.type in (TKN_PLUS, TKN_MINUS):
      result.register_next()
      self.next()
      factor = result.register(self.factor())
      if result.error: return result
      return result.success(UnaryOpNode(tkn, factor))

    return self.power_or_modulo()

  def power_or_modulo(self):
    return self.bin_op(self.call, (TKN_POW, TKN_MODULO, ), self.factor)

  def call(self):
    result = ParseResult()
    atom = result.register(self.atom())
    if result.error: return result

    if self.current_tkn.type == TKN_LPAREN:
      result.register_next()
      self.next()
      arg_nodes = []

      if self.current_tkn.type == TKN_RPAREN:
        result.register_next()
        self.next()
      else:
        arg_nodes.append(result.register(self.expr()))
        if result.error:
          return result.failure(InvalidSyntaxError(
            self.current_tkn.start, self.current_tkn.end,
            "Expected ')', 'INT', 'FLOAT', 'STRING', 'if', 'for', 'while', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'not'"
          ))

        while self.current_tkn.type == TKN_COMMA:
          result.register_next()
          self.next()

          arg_nodes.append(result.register(self.expr()))
          if result.error: return result

        if self.current_tkn.type != TKN_RPAREN:
          return result.failure(InvalidSyntaxError(
            self.current_tkn.start, self.current_tkn.end,
            f"Expected ',' or ')'"
          ))

        result.register_next()
        self.next()
      return result.success(CallNode(atom, arg_nodes))
    return result.success(atom)

  def atom(self):
    result = ParseResult()
    tkn = self.current_tkn

    if tkn.type in (TKN_INT, TKN_FLOAT):
      result.register_next()
      self.next()
      return result.success(NumberNode(tkn))

    elif tkn.type == TKN_STRING:
      result.register_next()
      self.next()
      return result.success(StringNode(tkn))

    elif tkn.type == TKN_IDENTIFIER:
      result.register_next()
      self.next()
      return result.success(VarAccessNode(tkn))

    elif tkn.type == TKN_LPAREN:
      result.register_next()
      self.next()
      expr = result.register(self.expr())
      if result.error: return result
      if self.current_tkn.type == TKN_RPAREN:
        result.register_next()
        self.next()
        return result.success(expr)
      else:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          "Expected ')'"
        ))

    elif tkn.type == TKN_LSQUARE:
      list_expr = result.register(self.list_expr())
      if result.error: return result
      return result.success(list_expr)
    
    elif tkn.matches(TKN_KEYWORD, 'if'):
      if_expr = result.register(self.if_expr())
      if result.error: return result
      return result.success(if_expr)

    elif tkn.matches(TKN_KEYWORD, 'for'):
      for_expr = result.register(self.for_expr())
      if result.error: return result
      return result.success(for_expr)

    elif tkn.matches(TKN_KEYWORD, 'while'):
      while_expr = result.register(self.while_expr())
      if result.error: return result
      return result.success(while_expr)

    elif tkn.matches(TKN_KEYWORD, 'func'):
      func_def = result.register(self.func_def())
      if result.error: return result
      return result.success(func_def)

    return result.failure(InvalidSyntaxError(
      tkn.start, tkn.end,
      "Expected 'let', int, float, identifier, '+', '-', '(', '[', if', 'for', 'while', 'func'"
    ))

  def list_expr(self):
    result = ParseResult()
    element_nodes = []
    start = self.current_tkn.start.copy()

    if self.current_tkn.type != TKN_LSQUARE:
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected '['"
      ))

    result.register_next()
    self.next()

    if self.current_tkn.type == TKN_RSQUARE:
      result.register_next()
      self.next()
    else:
      element_nodes.append(result.register(self.expr()))
      if result.error:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          "Expected ']', 'let', 'if', 'for', 'while', 'FUN', int, float, identifier, '+', '-', '(', '[' or 'not'"
        ))

      while self.current_tkn.type == TKN_COMMA:
        result.register_next()
        self.next()

        element_nodes.append(result.register(self.expr()))
        if result.error: return result

      if self.current_tkn.type != TKN_RSQUARE:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          f"Expected ',' or ']'"
        ))

      result.register_next()
      self.next()

    return result.success(ListNode(
      element_nodes,
      start,
      self.current_tkn.end.copy()
    ))

  def if_expr(self):
    result = ParseResult()
    all_cases = result.register(self.if_expr_cases('if'))
    if result.error: return result
    cases, else_case = all_cases
    return result.success(IfNode(cases, else_case))

  def if_expr_b(self):
    return self.if_expr_cases('consider')
    
  def if_expr_c(self):
    result = ParseResult()
    else_case = None

    if self.current_tkn.matches(TKN_KEYWORD, 'last'):
      result.register_next()
      self.next()

      if self.current_tkn.type == TKN_NEWLINE:
        result.register_next()
        self.next()

        statements = result.register(self.statements())
        if result.error: return result
        else_case = (statements, True)

        if self.current_tkn.matches(TKN_KEYWORD, 'end'):
          result.register_next()
          self.next()
        else:
          return result.failure(InvalidSyntaxError(
            self.current_tkn.start, self.current_tkn.end,
            "Expected 'end'"
          ))
      else:
        expr = result.register(self.statement())
        if result.error: return result
        else_case = (expr, False)

    return result.success(else_case)

  def if_expr_b_or_c(self):
    result = ParseResult()
    cases, else_case = [], None

    if self.current_tkn.matches(TKN_KEYWORD, 'consider'):
      all_cases = result.register(self.if_expr_b())
      if result.error: return result
      cases, else_case = all_cases
    else:
      else_case = result.register(self.if_expr_c())
      if result.error: return result
    
    return result.success((cases, else_case))

  def if_expr_cases(self, case_keyword):
    result = ParseResult()
    cases = []
    else_case = None

    if not self.current_tkn.matches(TKN_KEYWORD, case_keyword):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected '{case_keyword}'"
      ))

    result.register_next()
    self.next()

    condition = result.register(self.expr())
    if result.error: return result

    if not self.current_tkn.matches(TKN_KEYWORD, 'do'):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected 'do'"
      ))

    result.register_next()
    self.next()

    if self.current_tkn.type == TKN_NEWLINE:
      result.register_next()
      self.next()

      statements = result.register(self.statements())
      if result.error: return result
      cases.append((condition, statements, True))

      if self.current_tkn.matches(TKN_KEYWORD, 'end'):
        result.register_next()
        self.next()
      else:
        all_cases = result.register(self.if_expr_b_or_c())
        if result.error: return result
        new_cases, else_case = all_cases
        cases.extend(new_cases)
    else:
      expr = result.register(self.statement())
      if result.error: return result
      cases.append((condition, expr, False))

      all_cases = result.register(self.if_expr_b_or_c())
      if result.error: return result
      new_cases, else_case = all_cases
      cases.extend(new_cases)

    return result.success((cases, else_case))

  def for_expr(self):
    result = ParseResult()

    if not self.current_tkn.matches(TKN_KEYWORD, 'for'):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected 'for'"
      ))

    result.register_next()
    self.next()

    if self.current_tkn.type != TKN_IDENTIFIER:
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected identifier"
      ))

    var_name = self.current_tkn
    result.register_next()
    self.next()

    if self.current_tkn.type != TKN_EQ:
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected '='"
      ))
    
    result.register_next()
    self.next()

    start_value = result.register(self.expr())
    if result.error: return result

    if not self.current_tkn.matches(TKN_KEYWORD, 'to'):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected 'to'"
      ))
    
    result.register_next()
    self.next()

    end_value = result.register(self.expr())
    if result.error: return result

    if self.current_tkn.matches(TKN_KEYWORD, 'change'):
      result.register_next()
      self.next()

      step_value = result.register(self.expr())
      if result.error: return result
    else:
      step_value = None

    if not self.current_tkn.matches(TKN_KEYWORD, 'do'):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected 'do'"
      ))

    result.register_next()
    self.next()

    if self.current_tkn.type == TKN_NEWLINE:
      result.register_next()
      self.next()

      body = result.register(self.statements())
      if result.error: return result

      if not self.current_tkn.matches(TKN_KEYWORD, 'end'):
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          f"Expected 'end'"
        ))

      result.register_next()
      self.next()

      return result.success(ForNode(var_name, start_value, end_value, step_value, body, True))
    
    body = result.register(self.statement())
    if result.error: return result

    return result.success(ForNode(var_name, start_value, end_value, step_value, body, False))

  def while_expr(self):
    result = ParseResult()

    if not self.current_tkn.matches(TKN_KEYWORD, 'while'):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected 'while'"
      ))

    result.register_next()
    self.next()

    condition = result.register(self.expr())
    if result.error: return result

    if not self.current_tkn.matches(TKN_KEYWORD, 'do'):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected 'do'"
      ))

    result.register_next()
    self.next()

    if self.current_tkn.type == TKN_NEWLINE:
      result.register_next()
      self.next()

      body = result.register(self.statements())
      if result.error: return result

      if not self.current_tkn.matches(TKN_KEYWORD, 'end'):
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          f"Expected 'end'"
        ))

      result.register_next()
      self.next()

      return result.success(WhileNode(condition, body, True))
    
    body = result.register(self.statement())
    if result.error: return result

    return result.success(WhileNode(condition, body, False))

  def func_def(self):
    result = ParseResult()

    if not self.current_tkn.matches(TKN_KEYWORD, 'func'):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected 'func'"
      ))

    result.register_next()
    self.next()

    if self.current_tkn.type == TKN_IDENTIFIER:
      var_name_tkn = self.current_tkn
      result.register_next()
      self.next()
      if self.current_tkn.type != TKN_LPAREN:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          f"Expected '('"
        ))
    else:
      var_name_tkn = None
      if self.current_tkn.type != TKN_LPAREN:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          f"Expected identifier or '('"
        ))
    
    result.register_next()
    self.next()
    arg_name_tkns = []

    if self.current_tkn.type == TKN_IDENTIFIER:
      arg_name_tkns.append(self.current_tkn)
      result.register_next()
      self.next()
      
      while self.current_tkn.type == TKN_COMMA:
        result.register_next()
        self.next()

        if self.current_tkn.type != TKN_IDENTIFIER:
          return result.failure(InvalidSyntaxError(
            self.current_tkn.start, self.current_tkn.end,
            f"Expected identifier"
          ))

        arg_name_tkns.append(self.current_tkn)
        result.register_next()
        self.next()
      
      if self.current_tkn.type != TKN_RPAREN:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          f"Expected ',' or ')'"
        ))
    else:
      if self.current_tkn.type != TKN_RPAREN:
        return result.failure(InvalidSyntaxError(
          self.current_tkn.start, self.current_tkn.end,
          f"Expected identifier or ')'"
        ))

    result.register_next()
    self.next()

    if self.current_tkn.type == TKN_ARROW:
      result.register_next()
      self.next()

      body = result.register(self.expr())
      if result.error: return result

      return result.success(FuncDefNode(
        var_name_tkn,
        arg_name_tkns,
        body,
        True
      ))
    
    if self.current_tkn.type != TKN_NEWLINE:
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected '->' or NEWLINE"
      ))

    result.register_next()
    self.next()

    body = result.register(self.statements())
    if result.error: return result

    if not self.current_tkn.matches(TKN_KEYWORD, 'end'):
      return result.failure(InvalidSyntaxError(
        self.current_tkn.start, self.current_tkn.end,
        f"Expected 'end'"
      ))

    result.register_next()
    self.next()
    
    return result.success(FuncDefNode(
      var_name_tkn,
      arg_name_tkns,
      body,
      False
    ))

  ###################################

  def bin_op(self, func_a, ops, func_b=None):
    if func_b == None:
      func_b = func_a
    
    result = ParseResult()
    left = result.register(func_a())
    if result.error: return result

    while self.current_tkn.type in ops or (self.current_tkn.type, self.current_tkn.value) in ops:
      op_tkn = self.current_tkn
      result.register_next()
      self.next()
      right = result.register(func_b())
      if result.error: return result
      left = BinOpNode(left, op_tkn, right)

    return result.success(left)