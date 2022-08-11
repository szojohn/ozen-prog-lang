from runtime import *
from datatype import *
from errors import *
from tokens import *
from context import *
import os
from lexical_analysis import LexicalAnalyzer
from syntax_analysis import Parser

class Interpreter:
  def visit(self, node, context):
    method_name = f'visit_{type(node).__name__}'
    method = getattr(self, method_name, self.no_visit_method)
    return method(node, context)

  def no_visit_method(self, node, context):
    raise Exception(f'No visit_{type(node).__name__} method defined')

  ###################################

  def visit_NumberNode(self, node, context):
    return RunTimeResult().success(
      Number(node.tkn.value).set_context(context).set_position(node.start, node.end)
    )

  def visit_StringNode(self, node, context):
    return RunTimeResult().success(
      String(node.tkn.value).set_context(context).set_position(node.start, node.end)
    )

  def visit_ListNode(self, node, context):
    res = RunTimeResult()
    elements = []

    for element_node in node.element_nodes:
      elements.append(res.register(self.visit(element_node, context)))
      if res.should_return(): return res

    return res.success(
      List(elements).set_context(context).set_position(node.start, node.end)
    )

  def visit_VarAccessNode(self, node, context):
    res = RunTimeResult()
    var_name = node.var_name_tkn.value
    value = context.symbol_table.get(var_name)

    if not value:
      return res.failure(RunTimeError(
        node.start, node.end,
        f"'{var_name}' is not defined",
        context
      ))

    value = value.copy().set_position(node.start, node.end).set_context(context)
    return res.success(value)

  def visit_VarAssignNode(self, node, context):
    res = RunTimeResult()
    var_name = node.var_name_tkn.value
    value = res.register(self.visit(node.value_node, context))
    if res.should_return(): return res

    context.symbol_table.set(var_name, value)
    return res.success(value)

  def visit_BinOpNode(self, node, context):
    res = RunTimeResult()
    left = res.register(self.visit(node.left_node, context))
    if res.should_return(): return res
    right = res.register(self.visit(node.right_node, context))
    if res.should_return(): return res

    if node.op_tkn.type == TKN_PLUS:
      result, error = left.addition(right)
    elif node.op_tkn.type == TKN_MINUS:
      result, error = left.subtraction(right)
    elif node.op_tkn.type == TKN_MUL:
      result, error = left.multiply(right)
    elif node.op_tkn.type == TKN_DIV:
      result, error = left.divide(right)
    elif node.op_tkn.type == TKN_POW:
      result, error = left.powered_by(right)
    elif node.op_tkn.type == TKN_MODULO:
      result, error = left.remainder(right)
    elif node.op_tkn.type == TKN_EE:
      result, error = left.eq_compare(right)
    elif node.op_tkn.type == TKN_NE:
      result, error = left.neq_compare(right)
    elif node.op_tkn.type == TKN_LT:
      result, error = left.lt_compare(right)
    elif node.op_tkn.type == TKN_GT:
      result, error = left.gt_compare(right)
    elif node.op_tkn.type == TKN_LTE:
      result, error = left.lte_compare(right)
    elif node.op_tkn.type == TKN_GTE:
      result, error = left.gte_compare(right)
    elif node.op_tkn.matches(TKN_KEYWORD, 'AND'):
      result, error = left.anded_by(right)
    elif node.op_tkn.matches(TKN_KEYWORD, 'OR'):
      result, error = left.ored_by(right)

    if error:
      return res.failure(error)
    else:
      return res.success(result.set_position(node.start, node.end))

  def visit_UnaryOpNode(self, node, context):
    res = RunTimeResult()
    number = res.register(self.visit(node.node, context))
    if res.should_return(): return res

    error = None

    if node.op_tkn.type == TKN_MINUS:
      number, error = number.multiply(Number(-1))
    elif node.op_tkn.matches(TKN_KEYWORD, 'NOT'):
      number, error = number.notted()

    if error:
      return res.failure(error)
    else:
      return res.success(number.set_position(node.start, node.end))

  def visit_IfNode(self, node, context):
    res = RunTimeResult()

    for condition, expr, should_return_null in node.cases:
      condition_value = res.register(self.visit(condition, context))
      if res.should_return(): return res

      if condition_value.is_true():
        expr_value = res.register(self.visit(expr, context))
        if res.should_return(): return res
        return res.success(Number.null if should_return_null else expr_value)

    if node.else_case:
      expr, should_return_null = node.else_case
      expr_value = res.register(self.visit(expr, context))
      if res.should_return(): return res
      return res.success(Number.null if should_return_null else expr_value)

    return res.success(Number.null)

  def visit_ForNode(self, node, context):
    res = RunTimeResult()
    elements = []

    start_value = res.register(self.visit(node.start_value_node, context))
    if res.should_return(): return res

    end_value = res.register(self.visit(node.end_value_node, context))
    if res.should_return(): return res

    if node.step_value_node:
      step_value = res.register(self.visit(node.step_value_node, context))
      if res.should_return(): return res
    else:
      step_value = Number(1)

    i = start_value.value

    if step_value.value >= 0:
      condition = lambda: i < end_value.value
    else:
      condition = lambda: i > end_value.value
    
    while condition():
      context.symbol_table.set(node.var_name_tkn.value, Number(i))
      i += step_value.value

      value = res.register(self.visit(node.body_node, context))
      if res.should_return() and res.loop_continue == False and res.loop_break == False: return res
      
      if res.loop_continue:
        continue
      
      if res.loop_break:
        break

      elements.append(value)

    return res.success(
      Number.null if node.should_return_null else
      List(elements).set_context(context).set_position(node.start, node.end)
    )

  def visit_WhileNode(self, node, context):
    res = RunTimeResult()
    elements = []

    while True:
      condition = res.register(self.visit(node.condition_node, context))
      if res.should_return(): return res

      if not condition.is_true():
        break

      value = res.register(self.visit(node.body_node, context))
      if res.should_return() and res.loop_continue == False and res.loop_break == False: return res

      if res.loop_continue:
        continue
      
      if res.loop_break:
        break

      elements.append(value)

    return res.success(
      Number.null if node.should_return_null else
      List(elements).set_context(context).set_position(node.start, node.end)
    )

  def visit_FuncDefNode(self, node, context):
    res = RunTimeResult()

    func_name = node.var_name_tkn.value if node.var_name_tkn else None
    body_node = node.body_node
    arg_names = [arg_name.value for arg_name in node.arg_name_tkns]
    func_value = Function(func_name, body_node, arg_names, node.should_auto_return).set_context(context).set_position(node.start, node.end)
    
    if node.var_name_tkn:
      context.symbol_table.set(func_name, func_value)

    return res.success(func_value)

  def visit_CallNode(self, node, context):
    res = RunTimeResult()
    args = []

    value_to_call = res.register(self.visit(node.node_to_call, context))
    if res.should_return(): return res
    value_to_call = value_to_call.copy().set_position(node.start, node.end)

    for arg_node in node.arg_nodes:
      args.append(res.register(self.visit(arg_node, context)))
      if res.should_return(): return res

    return_value = res.register(value_to_call.execute(args))
    if res.should_return(): return res
    return_value = return_value.copy().set_position(node.start, node.end).set_context(context)
    return res.success(return_value)

  def visit_ReturnNode(self, node, context):
    res = RunTimeResult()

    if node.node_to_return:
      value = res.register(self.visit(node.node_to_return, context))
      if res.should_return(): return res
    else:
      value = Number.null
    
    return res.success_return(value)

  def visit_ContinueNode(self, node, context):
    return RunTimeResult().success_continue()

  def visit_BreakNode(self, node, context):
    return RunTimeResult().success_break()

  
class BaseFunction(Value):
  def __init__(self, name):
    super().__init__()
    self.name = name or "<anonymous>"

  def generate_new_context(self):
    new_context = Context(self.name, self.context, self.start)
    new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
    return new_context

  def check_args(self, arg_names, args):
    res = RunTimeResult()

    if len(args) > len(arg_names):
      return res.failure(RunTimeError(
        self.start, self.end,
        f"{len(args) - len(arg_names)} too many args passed into {self}",
        self.context
      ))
    
    if len(args) < len(arg_names):
      return res.failure(RunTimeError(
        self.start, self.end,
        f"{len(arg_names) - len(args)} too few args passed into {self}",
        self.context
      ))

    return res.success(None)

  def populate_args(self, arg_names, args, exec_ctx):
    for i in range(len(args)):
      arg_name = arg_names[i]
      arg_value = args[i]
      arg_value.set_context(exec_ctx)
      exec_ctx.symbol_table.set(arg_name, arg_value)

  def check_and_populate_args(self, arg_names, args, exec_ctx):
    res = RunTimeResult()
    res.register(self.check_args(arg_names, args))
    if res.should_return(): return res
    self.populate_args(arg_names, args, exec_ctx)
    return res.success(None)

class Function(BaseFunction):
  def __init__(self, name, body_node, arg_names, should_auto_return):
    super().__init__(name)
    self.body_node = body_node
    self.arg_names = arg_names
    self.should_auto_return = should_auto_return

  def execute(self, args):
    res = RunTimeResult()
    interpreter = Interpreter()
    exec_ctx = self.generate_new_context()

    res.register(self.check_and_populate_args(self.arg_names, args, exec_ctx))
    if res.should_return(): return res

    value = res.register(interpreter.visit(self.body_node, exec_ctx))
    if res.should_return() and res.func_return_value == None: return res

    ret_value = (value if self.should_auto_return else None) or res.func_return_value or Number.null
    return res.success(ret_value)

  def copy(self):
    copy = Function(self.name, self.body_node, self.arg_names, self.should_auto_return)
    copy.set_context(self.context)
    copy.set_position(self.start, self.end)
    return copy

  def __repr__(self):
    return f"<function {self.name}>"

class BuiltInFunction(BaseFunction):
  def __init__(self, name):
    super().__init__(name)

  def execute(self, args):
    res = RunTimeResult()
    exec_ctx = self.generate_new_context()

    method_name = f'execute_{self.name}'
    method = getattr(self, method_name, self.no_visit_method)

    res.register(self.check_and_populate_args(method.arg_names, args, exec_ctx))
    if res.should_return(): return res

    return_value = res.register(method(exec_ctx))
    if res.should_return(): return res
    return res.success(return_value)
  
  def no_visit_method(self, node, context):
    raise Exception(f'No execute_{self.name} method defined')

  def copy(self):
    copy = BuiltInFunction(self.name)
    copy.set_context(self.context)
    copy.set_position(self.start, self.end)
    return copy

  def __repr__(self):
    return f"<built-in function {self.name}>"

  #####################################

  def execute_print(self, exec_ctx):
    print(str(exec_ctx.symbol_table.get('value')))
    return RunTimeResult().success(Number.null)
  execute_print.arg_names = ['value']
  
  def execute_print_ret(self, exec_ctx):
    return RunTimeResult().success(String(str(exec_ctx.symbol_table.get('value'))))
  execute_print_ret.arg_names = ['value']
  
  def execute_input(self, exec_ctx):
    text = input()
    return RunTimeResult().success(String(text))
  execute_input.arg_names = []

  def execute_input_int(self, exec_ctx):
    while True:
      text = input()
      try:
        number = int(text)
        break
      except ValueError:
        print(f"'{text}' must be an integer. Try again!")
    return RunTimeResult().success(Number(number))
  execute_input_int.arg_names = []

  def execute_clear(self, exec_ctx):
    os.system('cls' if os.name == 'nt' else 'cls') 
    return RunTimeResult().success(Number.null)
  execute_clear.arg_names = []

  def execute_is_number(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), Number)
    return RunTimeResult().success(Number.true if is_number else Number.false)
  execute_is_number.arg_names = ["value"]

  def execute_is_string(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), String)
    return RunTimeResult().success(Number.true if is_number else Number.false)
  execute_is_string.arg_names = ["value"]

  def execute_is_list(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), List)
    return RunTimeResult().success(Number.true if is_number else Number.false)
  execute_is_list.arg_names = ["value"]

  def execute_is_function(self, exec_ctx):
    is_number = isinstance(exec_ctx.symbol_table.get("value"), BaseFunction)
    return RunTimeResult().success(Number.true if is_number else Number.false)
  execute_is_function.arg_names = ["value"]

  def execute_append(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    value = exec_ctx.symbol_table.get("value")

    if not isinstance(list_, List):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "First argument must be list",
        exec_ctx
      ))

    list_.elements.append(value)
    return RunTimeResult().success(Number.null)
  execute_append.arg_names = ["list", "value"]

  def execute_pop(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")
    index = exec_ctx.symbol_table.get("index")

    if not isinstance(list_, List):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(index, Number):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "Second argument must be number",
        exec_ctx
      ))

    try:
      element = list_.elements.pop(index.value)
    except:
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        'Element at this index could not be removed from list because index is out of bounds',
        exec_ctx
      ))
    return RunTimeResult().success(element)
  execute_pop.arg_names = ["list", "index"]

  def execute_extend(self, exec_ctx):
    listA = exec_ctx.symbol_table.get("listA")
    listB = exec_ctx.symbol_table.get("listB")

    if not isinstance(listA, List):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "First argument must be list",
        exec_ctx
      ))

    if not isinstance(listB, List):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "Second argument must be list",
        exec_ctx
      ))

    listA.elements.extend(listB.elements)
    return RunTimeResult().success(Number.null)
  execute_extend.arg_names = ["listA", "listB"]

  def execute_len(self, exec_ctx):
    list_ = exec_ctx.symbol_table.get("list")

    if not isinstance(list_, List):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "Argument must be list",
        exec_ctx
      ))

    return RunTimeResult().success(Number(len(list_.elements)))
  execute_len.arg_names = ["list"]

  def execute_to_int(self, exec_ctx):
    num = exec_ctx.symbol_table.get("value")
    try:
      final_num = int(num.value)
    except ValueError:
      print("Cannot convert to int")
    return RunTimeResult().success(Number(final_num))
  execute_to_int.arg_names = ["value"]

  def execute_to_float(self, exec_ctx):
    num = exec_ctx.symbol_table.get("value")
    try:
      final_num = float(num.value)
    except ValueError:
      print("Cannot convert to float")
    return RunTimeResult().success(Number(final_num))
  execute_to_float.arg_names = ["value"]

  def execute_to_string(self, exec_ctx):
    string_sample = exec_ctx.symbol_table.get("value")
    try:
      final_string = str(string_sample.value)
    except ValueError:
      print("Cannot convert to string")
    return RunTimeResult().success(String(final_string))
  execute_to_string.arg_names = ["value"]

  def execute_incr(self, exec_ctx):
    num = exec_ctx.symbol_table.get("value")

    if not isinstance(num, Number):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "Argument must be a number",
        exec_ctx
      ))

    final_num = num.value + 1
    return RunTimeResult().success(Number(final_num))
  execute_incr.arg_names = ["value"]

  def execute_decr(self, exec_ctx):
    num = exec_ctx.symbol_table.get("value")

    if not isinstance(num, Number):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "Argument must be a number",
        exec_ctx
      ))

    final_num = num.value - 1
    return RunTimeResult().success(Number(final_num))
  execute_decr.arg_names = ["value"]

  def execute_run(self, exec_ctx):
    fn = exec_ctx.symbol_table.get("fn")

    if not isinstance(fn, String):
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        "Second argument must be string",
        exec_ctx
      ))

    fn = fn.value

    try:
      with open(fn, "r") as f:
        script = f.read()
    except Exception as e:
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        f"Failed to load script \"{fn}\"\n" + str(e),
        exec_ctx
      ))

    _, error = run(fn, script)
    
    if error:
      return RunTimeResult().failure(RunTimeError(
        self.start, self.end,
        f"Failed to finish executing script \"{fn}\"\n" +
        error.arrow_string(),
        exec_ctx
      ))

    return RunTimeResult().success(Number.null)
  execute_run.arg_names = ["fn"]

BuiltInFunction.print       = BuiltInFunction("print")
BuiltInFunction.print_ret   = BuiltInFunction("print_ret")
BuiltInFunction.input       = BuiltInFunction("input")
BuiltInFunction.input_int   = BuiltInFunction("input_int")
BuiltInFunction.clear       = BuiltInFunction("clear")
BuiltInFunction.is_number   = BuiltInFunction("is_number")
BuiltInFunction.is_string   = BuiltInFunction("is_string")
BuiltInFunction.is_list     = BuiltInFunction("is_list")
BuiltInFunction.is_function = BuiltInFunction("is_function")
BuiltInFunction.append      = BuiltInFunction("append")
BuiltInFunction.pop         = BuiltInFunction("pop")
BuiltInFunction.extend      = BuiltInFunction("extend")
BuiltInFunction.len			= BuiltInFunction("len")
BuiltInFunction.run			= BuiltInFunction("run")
BuiltInFunction.incr    = BuiltInFunction("incr")
BuiltInFunction.decr    = BuiltInFunction("decr")
BuiltInFunction.to_int    = BuiltInFunction("to_int")
BuiltInFunction.to_float    = BuiltInFunction("to_float")
BuiltInFunction.to_string    = BuiltInFunction("to_string")


global_symbol_table = SymbolTable()
global_symbol_table.set("null", Number.null)
global_symbol_table.set("false", Number.false)
global_symbol_table.set("true", Number.true)
global_symbol_table.set("math_pi", Number.math_PI)
global_symbol_table.set("print", BuiltInFunction.print)
global_symbol_table.set("return_print", BuiltInFunction.print_ret)
global_symbol_table.set("user_in", BuiltInFunction.input)
global_symbol_table.set("num_user_in", BuiltInFunction.input_int)
global_symbol_table.set("clear", BuiltInFunction.clear)
global_symbol_table.set("cls", BuiltInFunction.clear)
global_symbol_table.set("is_num", BuiltInFunction.is_number)
global_symbol_table.set("is_string", BuiltInFunction.is_string)
global_symbol_table.set("is_list", BuiltInFunction.is_list)
global_symbol_table.set("is_func", BuiltInFunction.is_function)
global_symbol_table.set("append", BuiltInFunction.append)
global_symbol_table.set("pop", BuiltInFunction.pop)
global_symbol_table.set("extend", BuiltInFunction.extend)
global_symbol_table.set("length", BuiltInFunction.len)
global_symbol_table.set("run", BuiltInFunction.run)
global_symbol_table.set("incr", BuiltInFunction.incr)
global_symbol_table.set("decr", BuiltInFunction.decr)
global_symbol_table.set("to_int", BuiltInFunction.to_int)
global_symbol_table.set("to_float", BuiltInFunction.to_float)
global_symbol_table.set("to_string", BuiltInFunction.to_string)


def run(fn, text):
  lexer = LexicalAnalyzer(fn, text)
  tokens, error = lexer.init_tokens()
  if error: return None, error
  
  parser = Parser(tokens)
  pars = parser.parse()
  if pars.error: return None, pars.error

  interpreter = Interpreter()
  context = Context('<program>')
  context.symbol_table = global_symbol_table
  result = interpreter.visit(pars.node, context)

  return result.value, result.error