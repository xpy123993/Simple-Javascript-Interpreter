'''

args:   (expression, expression, ..., expression)
        ()

expression:
            variable = expression
            variable += expression
            variable -= expression
            variable *= expression
            variable /= expression
            variable = variable

            bool_expression && bool_expression
            bool_expression || bool_expression
            bool_expression

bool_expression:
            bool_factor == bool_factor
            bool_factor != bool_factor
            bool_factor <= bool_factor
            bool_factor >= bool_factor
            bool_factor < bool_factor
            bool_factor > bool_factor
            bool_factor

bool_factor:
            number_factor + number_factor
            number_factor - number_factor

number_factor:
            element_suffix * element_suffix
            element_suffix / element_suffix
            element_suffix

element:    (expression)
            variable
            string
            number
            - element
            ! element

element_suffix:
            element(args)
            element[expr]
            element

variable:   id.id
            id
'''
line_number = 0

class TokenUtils:

    def _dump_error_message(self, message):
        print('[TOKEN] Error: %s' % message)
        print(line_number)
        exit(0)

    def _dump_warning_message(self, message):
        print('[TOKEN] Warning: %s' % message)
        return

    def string_token(self, value):
        return {'type': 'string', 'value': value, 'toString': self.variable_token('toString')}

    def number_token(self, value):
        return {'type': 'number', 'value': float(value), 'toString': self.variable_token('toString')}

    def boolean_token(self, value):
        return {'type': 'boolean', 'value': value, 'toString': self.variable_token('toString')}

    def variable_token(self, value):
        return {'type': 'id', 'value': value}

    def regrex_token(self, value, mode):
        return {'type': 'regrex', 'value': value, 'mode': mode}

    def none_token(self):
        return {'type': 'none', 'value': 'none'}

    def if_token(self, expression, true_stmt, false_stmt):
        return {'type': 'if',
                'expression': expression,
                'true_stmt': true_stmt,
                'false_stmt': false_stmt}

    def operator_token(self, value, priority, args):
        token = {'type': 'operator'}
        token['value'] = value
        token['priority'] = priority
        token['args'] = args
        return token

    def function_token(self, function_name, args, code):
        token = {'type': 'function_def'}
        token['name'] = function_name
        token['args'] = args
        token['code'] = code
        token['caller'] = self.none_token()
        return token

    def convert_to_string(self, value):
        return self.string_token(self.value(value))

    def convert_to_boolean(self, value):
        val_type = self.type(value)
        if val_type == 'boolean':
            return value
        if val_type == 'string':
            return True
        if val_type == 'number':
            return self.boolean_token(self.value(value) != 0)
        if val_type == 'none':
            return self.boolean_token(False)

        print('Cannot convert %s to boolean' % val_type)
        return self.boolean_token(False)

    def type(self, value):
        if isinstance(value, dict) and value.get('type') is not None:
            return value['type']
        if isinstance(value, str):
            return 'string'
        if isinstance(value, float):
            return 'number'
        if value is None:
            return 'none'
        self._dump_error_message('Cannot decide the type of %s' % value)

    def is_string(self, value): return self.type(value) == 'string'

    def is_number(self, value): return self.type(value) == 'number'

    def is_operator(self, value): return self.type(value) == 'operator'

    def value(self, value):
        if value is None:
            return self.none_token()
        if isinstance(value, dict) and value.get('value') is not None:
            return value['value']
        # Guess the type of value to avoid critical error
        if isinstance(value, str) or isinstance(value, float):
            return value
        if isinstance(value, dict) and self.type(value) == 'function_def':
            return value['name']
        return value
        self._dump_error_message('Cannot get the true value of %s' % value)

    def _string_add_rule(self, val_1, val_2, operator):
        if self.is_operator(operator) and self.value(operator) == '+':
            if self.is_string(val_1) or self.is_string(val_2):
                s1 = str(self.value(val_1))
                s2 = str(self.value(val_2))
                return self.string_token(s1 + s2)
        return None

    def _number_arth_rule(self, val_1, val_2, operator):
        if self.is_operator(operator) and self.value(operator) in '+-*/':
            if self.is_number(val_1) and self.is_number(val_2):
                ope = self.value(operator)
                n1 = self.value(val_1)
                n2 = self.value(val_2)
                if ope == '+':
                    return self.number_token(n1 + n2)
                if ope == '-':
                    return self.number_token(n1 - n2)
                if ope == '*':
                    return self.number_token(n1 * n2)
                if ope == '/':
                    return self.number_token(n1 / n2)
        return None

    def _boolean_and_or_rule(self, val_1, val_2, operator):
        if self.is_operator(operator):
            ope = self.value(operator)
            if ope in ['&&', '||']:
                b1 = self.value(self.convert_to_boolean(val_1))
                b2 = self.value(self.convert_to_boolean(val_2))
                if ope == '&&':
                    return self.boolean_token(b1 and b2)
                return self.boolean_token(b1 or b2)
        return None

    def _boolean_expression_rule(self, val_1, val_2, operator):
        if self.is_operator(operator):
            ope = self.value(operator)
            t1 = self.type(val_1)
            t2 = self.type(val_2)
            v1 = self.value(val_1)
            v2 = self.value(val_2)
            if ope in ['==', '<=', '>=', '!=']:
                if t1 != t2:
                    self._dump_error_message(
                        'Cannot use %s on different type: %s and %s' % (ope, t1, t2))
                result = False
                if ope == '==':
                    result = v1 == v2
                if ope == '<=':
                    result = v1 <= v2
                if ope == '>=':
                    result = v1 >= v2
                if ope == '!=' or ope == '<>':
                    result = v1 != v2
                return self.boolean_token(result)

        return None

    def double_operator(self, val_1, val_2, operator):
        token = self._string_add_rule(val_1, val_2, operator)
        if token is None:
            token = self._number_arth_rule(val_1, val_2, operator)
        if token is None:
            token = self._boolean_and_or_rule(val_1, val_2, operator)
        if token is None:
            token = self._boolean_expression_rule(val_1, val_2, operator)
        if token is None:
            self._dump_error_message(
                'Unknown operation %s on %s, %s' % (operator, val_1, val_2))
        return token

    def is_none(self, val):
        return self.type(val) == 'none'


token_utils = TokenUtils()


class Interpreter:

    keyword_table = ['function', 'var', 'if', 'while', 'else', 'return']

    def __init__(self, block_name='base', current_function=None):
        self.text = ''
        self.position = self.max_position = self.line_number = 0
        self.variables_table = {}
        self.global_variables_table = {}
        self.block_name = block_name
        self.current_function = current_function
        if current_function is None:
            self.current_function = token_utils.none_token()
            self.current_function['name'] = ''

    def dump_error_message(self, message):
        print('[Interpreter] Error: %s' % message)
        print('In line %d' % self.line_number)
        self.dump_variable_table()
        exit(0)

    def dump_warning_message(self, message):
        print('[Interpreter] Warning: %s' % message)
        print('In line %d' % self.line_number)
        return

    def current_val(self, offset=0):
        if self.position + offset >= len(self.text):
            return '<EOF>'
        return self.text[self.position + offset]

    def erase_blank(self, ignore_new_line=True):
        last_position = self.position
        while (self.current_val() in [' ', '\t']) or (ignore_new_line and self.current_val() in ['\n', '\r']):
            if ignore_new_line:
                if self.current_val() == '\n' and self.max_position < self.position:
                    self.line_number += 1
                    global line_number
                    line_number = self.line_number
            self.position += 1
        self.max_position = max(self.max_position, self.position)
        if self.current_val() == '/':
            if self.current_val(1) == '/':
                while self.current_val() != '\n':
                    if self.current_val() == '<EOF>':
                        break
                    self.position += 1
                self.position += 1
                self.erase_blank()
            if self.current_val(1) == '*':
                while not (self.current_val(0) == '*' and self.current_val(1) == '/'):
                    self.position += 1
                    if self.current_val() == '<EOF>':
                        self.dump_error_message(
                            'expect the end symbol of comments')
                self.position += 2
                self.erase_blank()
        return last_position != self.position

    def parse_keyword(self, keyword):
        self.erase_blank()

        parse_size = len(keyword)
        if self.position + parse_size > len(self.text):
            return False
        truncated_text = self.text[self.position: self.position + parse_size]
        if truncated_text == keyword:
            self.position += parse_size
            return True
        return False

    def parse_keyword_id(self, keyword):
        self.erase_blank()
        backup = self.position
        if self.parse_id() is None and self.parse_keyword(keyword):
            return True
        self.position = backup
        return False

    def eval_string(self):
        # CANNOT USE PARSE_KEYWORD
        self.erase_blank()
        token_string = ''
        is_shift = False
        if self.current_val() == '"':
            self.position += 1
            while self.current_val() != '"' or is_shift:
                if self.current_val() == '\\':
                    is_shift = not is_shift
                else:
                    is_shift = False
                token_string += self.current_val()
                if self.current_val() in '\r\n' and not is_shift:
                    self.dump_error_message('expect " while parsing string')
                self.position += 1
            self.position += 1

            return token_utils.string_token(token_string)
        if self.current_val() == "'":
            self.position += 1
            while self.current_val() != "'" or is_shift:
                if self.current_val() == '\\':
                    is_shift = not is_shift
                else:
                    is_shift = False
                token_string += self.current_val()
                if self.current_val() in '\r\n' and not is_shift:
                    self.dump_error_message('expect " while parsing string')
                self.position += 1
            self.position += 1
            return token_utils.string_token(token_string)
        if self.current_val() == '/':
            self.position += 1
            token_string = ''
            while self.current_val() != '/':
                if self.current_val() == '<EOF>' or self.current_val() == '\n':
                    self.dump_error_message('Expect the end symbol /')
                token_string += self.current_val()
                self.position += 1
            self.position += 1
            mode = None
            if self.current_val() in 'gim':
                mode = self.current_val()
            token = token_utils.string_token(token_string)
            token['regex_mode'] = mode
            return token
        return None

    def eval_number(self):
        
        token_number = ''
        is_float = False
        self.erase_blank()
        while self.current_val().isnumeric() or self.current_val() == '.':
            if self.current_val() == '.':
                if is_float:
                    break
                is_float = True
            token_number += self.current_val()
            self.position += 1
        if token_number == '.':
            return None
        return token_utils.number_token(float(token_number)) if len(token_number) > 0 else None

    def parse_id(self):
        self.erase_blank()
        if self.current_val().isnumeric():
            return None
        token = ''
        backup = self.position
        while self.current_val().isnumeric() or self.current_val().isalpha() or self.current_val() == '_':
            token += self.current_val()
            self.position += 1
        if len(token) > 0 and token in self.keyword_table:
            self.position = backup
            return None
        return token if len(token) > 0 else None

    def eval_basic_token(self):
        token = self.eval_string()
        if token is not None:
            return token
        token = self.eval_number()
        if token is not None:
            return token
        token = self.parse_id()
        if token is not None:
            return token_utils.variable_token(token)
        return None

    def eval_variable(self):
        # safe rollback

        backup = self.position

        next_token = self.parse_id()

        if next_token is not None:
            parent_s = []
            next_token = token_utils.variable_token(next_token)

            has_next = self.parse_keyword('.')

            if has_next:
                if token_utils.type(next_token) == 'id':
                    parent = self.get_variable(token_utils.value(next_token), [])
                else:
                    parent = next_token

            if token_utils.type(next_token) == 'id' or has_next:
            
                while has_next:
                    if token_utils.type(next_token) == 'id':
                        next_token = self.get_variable(token_utils.value(next_token), parent_s)
                    parent_s.append(next_token)
                    next_token = token_utils.variable_token(self.parse_id())
                    if parent.get(token_utils.value(next_token)) == None:
                        self.dump_error_message(
                            '%s has no propery called %s' % (parent_s.pop(), token_utils.value(next_token)))
                    parent = parent.get(token_utils.value(next_token))


                    has_next = self.parse_keyword('.')

                next_token['parents'] = parent_s

                
                return next_token



        self.position = backup

        token = self.parse_function()
        if token is not None:
            token['parents'] = []
            return token

        self.position = backup

        return None

    def eval_args(self):
        if self.parse_keyword('('):
            last_arg_position = self.position
            args = []
            if self.parse_keyword(')'):
                return args
            args.append(self.eval_expression())
            while self.parse_keyword(','):
                args.append(self.eval_expression())
            if not self.parse_keyword(')'):
                print('while parsing args in %s' %
                      self.text[last_arg_position: self.position])
                self.dump_error_message('Expect ) while evalulating args')
            return args
        return None

    def _is_id_symbol(self, value): return value.isnumeric(
    ) or value.isalpha() or value == '_'

    def parse_function(self):

        backup = self.position
        if self.parse_keyword_id('function'):
            function_name = self.parse_id()
            if function_name is None:
                function_name = ''
            if self.parse_keyword('('):
                args = []
                if not self.parse_keyword(')'):
                    args.append(self.parse_id())
                    while self.parse_keyword(','):
                        args.append(self.parse_id())

                    if not self.parse_keyword(')'):
                        self.dump_error_message(
                            'right bracket expect, but found %s' % self.current_val())
            begin_position = self.position
            self.skip_one_statement()

            end_position = self.position
            return token_utils.function_token(function_name, args, self.text[begin_position: end_position])

        # safe rollback
        self.position = backup
        return None

    def eval_element(self):
        backup = self.position
        token = self.eval_args()
        if token is not None:
            if len(token) > 0:
                return token.pop()
            self.dump_error_message(
                'recongnized a bracket, but nothing inside')

        token = self.eval_variable()
        if token is not None:
            if token_utils.type(token) == 'id':
                variable_name = token_utils.value(token)
                parents = token['parents']
                token = self.get_variable(variable_name, parents)
                if token is None:
                    self.dump_error_message(
                        'variable %s undefined while evaluating element, parent: %s' % (variable_name, token))
            return token

        token = self.eval_string()
        if token is not None:
            return token
        token = self.eval_number()
        if token is not None:
            return token
        if self.parse_keyword('-'):
            expr = self.eval_element()
            if token_utils.is_number(expr):
                expr['value'] = -expr['value']
                return expr
            self.dump_error_message('Invalid negative symbol')
        if self.parse_keyword('!'):
            expr = self.eval_element()
            b_result = token_utils.convert_to_boolean(expr)
            b_result['value'] = not b_result['value']
            return expr

        self.position = backup
        return None

    def _find_variable_in_table(self, parents, table):
        parent = table
        for next_token in parents:
            if token_utils.type(next_token) == 'id':
                if parent.get(token_utils.value(next_token)) is None:
                    return None
                parent = parent.get(token_utils.value(next_token))
            else:
                parent = next_token
        return parent

    def register_variable(self, name, token, parents):
        parent = self._find_variable_in_table(
                parents, self.variables_table)
        if parent is None:
            parent = self._find_variable_in_table(parents, self.global_variables_table)

        if parent is None:
            self.dump_error_message(
                'object location %s does not exist' % ('->'.join(parents)))

        parent[name] = token

        # print('%5s <-\t%s' % (name, token_utils.value(token)))

    def get_variable(self, name, parents):

        if len(parents) > 0:

            parent = self._find_variable_in_table(parents, self.variables_table)
            if parent is None:
                parent = self._find_variable_in_table(parents, self.global_variables_table)

            token = parent.get(token_utils.value(name))
            # print(token, parent)
            if token is not None and isinstance(token, dict):
                token['self'] = parent

            return token

        token = self.variables_table.get(name)

        if token is None:
            token = self.global_variables_table.get(name)

        if token is None:
            self.dump_error_message("%s undefined @!!" % name)

        return token

    def eval_function_call(self, function, args):
        # print('Call function %s with args %s' % (function['name'], args))

        if len(function['args']) < len(args):
            self.dump_error_message(
                'too much arguments for function %s' % function['name'])

        function_name = function.get('name')

        if function_name == 'alert':
            args = [token_utils.value(x) for x in args]
            if len(args) == 0:
                print()
            elif len(args) == 1:
                print(args.pop())
            else:
                print(args)
            return token_utils.none_token()
        if function_name == 'toString':
            return token_utils.convert_to_string(function.get('self'))

        interpreter = Interpreter(block_name=str(
            function_name), current_function=function)

        function_variables_table = self.variables_table.copy()
        function_variables_table['returned_value'] = token_utils.none_token()

        caller_function = self.current_function

        if caller_function is None:
            caller_token = token_utils.none_token()
            caller_token['name'] = token_utils.none_token()
        else:
            caller_token = caller_function

        function['caller'] = caller_token

        for i in range(min(len(function['args']), len(args))):
            function_variables_table[function['args'][i]] = args[i]

        interpreter.load(function['code'], variables_table=function_variables_table,
                         global_variables_table=self.global_variables_table)

        # function_i.dump_variable_table()

        interpreter.eval_statement()

        # interpreter.dump_variable_table()
        result = interpreter.get_variable('returned_value', [])
        # print('function %s returned value: %s' % (function, result))
        # interpreter.dump_variable_table()
        if token_utils.type(result) != 'none':
            argument = ''
            if len(args) > 0:
                argument = '("%s"' % token_utils.value(args[0])
                for i in range(len(args)):
                    argument += ', "%s"' % token_utils.value(args[i])
            print('call %8s(%15s), return "%s"' % (function.get('name'), argument, token_utils.value(result)))
        return result

    def eval_bool_expression(self):
        token = self.eval_bool_factor()
        can_continue = True
        if token is not None:
            while can_continue:
                can_continue = False
                for operator_prefix in ['==', '!=', '<>', '<=', '>=', '<', '>']:
                    if self.parse_keyword(operator_prefix):
                        left_expression = token
                        right_expression = self.eval_bool_factor()
                        if right_expression is None:
                            self.dump_error_message(
                                'Unexpected end of expression')
                        operator = token_utils.operator_token(
                            operator_prefix, 0, None)
                        token = token_utils.double_operator(
                            left_expression, right_expression, operator)
                        can_continue = True
            return token
        return None

    def eval_bool_factor(self):
        token = self.eval_number_factor()
        can_continue = True
        if token is not None:
            while can_continue:
                can_continue = False
                for operator_prefix in '+-':
                    if self.parse_keyword(operator_prefix):
                        left_expression = token
                        right_expression = self.eval_number_factor()
                        if right_expression is None:
                            self.dump_error_message(
                                'Unexpected end of expression')
                        operator = token_utils.operator_token(
                            operator_prefix, 0, None)
                        token = token_utils.double_operator(
                            left_expression, right_expression, operator)
                        can_continue = True

            return token
        return None

    def eval_element_suffix(self):

        token = self.eval_element()
        if token is not None:
            args = self.eval_args()
            if args is not None:
                    # this is a function, feature: variable ()
                if token_utils.type(token) == 'function_def':
                    return self.eval_function_call(token, args)

                if token_utils.type(token) == 'id':
                    function_name = token_utils.value(token)
                    function = self.get_variable(
                        function_name, [token.get('self') if token.get('self') is not None else []])
                    return self.eval_function_call(function, args)

            if self.parse_keyword('['):
                expr = self.eval_expression()
                if not self.parse_keyword(']'):
                    self.dump_error_message('Expect end symbol of index ]')
                if not self.is_number(expr):
                    self.dump_error_message('Index must be integer')
                if self.is_string(token):
                    target = token_utils.value(token)
                    index = int(token_utils.value(token))
                    if index < len(target):
                        return token_utils.string_token(target[index])
                    else:
                        self.dump_error_message(
                            'index out of range: %d > %d' % (index, len(target)))

            return token

    # TAG*/
    def eval_number_factor(self):
        token = self.eval_element_suffix()
        can_continue = True
        if token is not None:
            while can_continue:
                can_continue = False
                for operator_prefix in '*/':
                    if self.parse_keyword(operator_prefix):
                        left_expression = token
                        right_expression = self.eval_element_suffix()
                        if right_expression is None:
                            self.dump_error_message(
                                'Unexpected end of expression')
                        operator = token_utils.operator_token(
                            operator_prefix, 0, None)
                        token = token_utils.double_operator(
                            left_expression, right_expression, operator)
                        can_continue = True
            return token

        return None

    def eval_expression(self):
        # eval expression only if we are sure there exists an expression
        backup = self.position
        token = self.eval_variable()
        if token is not None and token_utils.type(token) == 'id':
            variable_name = token_utils.value(token)
            
            if self.parse_keyword('='):
                self.register_variable(
                    variable_name, self.eval_expression(), token['parents'])
                return self.get_variable(variable_name, token['parents'])
            variable_value = self.get_variable(variable_name, token['parents'])
            if variable_value is not None:
                for operator_prefix in '+-*/':
                    operator = operator_prefix + '='
                    if self.parse_keyword(operator):
                        operator = token_utils.operator_token(
                            operator_prefix, 0, None)
                        left_expression = variable_value
                        right_expression = self.eval_expression()
                        return token_utils.double_operator(left_expression, right_expression, operator)

        # safe rollback, since not call any function by just parsing a variable
        self.position = backup
        token = self.eval_bool_expression()
        if token is not None:
            for operator in ['&&', '||']:
                if self.parse_keyword(operator):
                    right = self.eval_bool_expression()
                    if right is None:
                        self.dump_error_message(
                            'Unexpected end symbol of expression')

                    left_expression = token_utils.convert_to_boolean(token)
                    right_expression = token_utils.convert_to_boolean(right)
                    operator = token_utils.operator_token(operator, 0, None)
                    return token_utils.double_operator(left_expression, right_expression, operator)
            return token
        return None

    def skip_one_statement(self):

        self.erase_blank()
        if self.parse_keyword('{'):
            balanced_bracket = 1

            while balanced_bracket != 0:
                self.erase_blank()
                if self.eval_string() is None:
                    if self.current_val() == '{':
                        balanced_bracket += 1
                    if self.current_val() == '}':
                        balanced_bracket -= 1
                    self.position += 1
                if self.current_val() == '<EOF>':
                    self.dump_error_message('expect statement block end }')
        else:
            while not self.parse_keyword(';'):
                if self.current_val() == '<EOF>':
                    self.dump_error_message('unexpected statement end')
                if self.eval_string() is None:
                    self.position += 1
                self.erase_blank()

    def eval_statement(self):

        backup = self.position

        if self.parse_keyword_id('return'):
            self.register_variable(
                'returned_value', self.eval_expression(), [])
            return True

        self.position = backup

        if self.parse_keyword_id('var'):
            has_next = True
            while has_next:
                variable_name = self.parse_id()
                self.register_variable(
                    variable_name, token_utils.none_token(), [])
                if self.parse_keyword('='):
                    self.register_variable(
                        variable_name, self.eval_expression(), [])
                has_next = self.parse_keyword(',')
            self.parse_keyword(';')
            return

        self.position = backup

        token = self.parse_function()
        if token is not None:
            self.global_variables_table[token['name']] = token
            return

        last_position = -1
        if self.parse_keyword('{'):
            while not self.parse_keyword('}'):
                if last_position == self.position:
                    print(self.current_val())
                    self.dump_error_message('infinite loop found')
                last_position = self.position
                if self.eval_statement():
                    return
            return

        if self.parse_keyword_id('if'):
            expr = token_utils.convert_to_boolean(self.eval_element())
            if not token_utils.value(expr):
                self.skip_one_statement()
                self.parse_keyword_id('else')
            return

        self.eval_expression()
        self.parse_keyword(';')
        return

    def is_completed(self):
        self.erase_blank()
        return self.position >= len(self.text)

    def dump_variable_table(self):
        if len(self.block_name) > 0:
            print('Variable table for %s' % self.block_name)
        else:
            print('Variable table')
        for key in self.variables_table:
            print('"%s":\t%s' % (key, self.variables_table[key]))

    def load(self, script_text, variables_table={}, global_variables_table={}):
        self.text = script_text
        self.max_position = self.position = self.line_number = 0
        self.variables_table = variables_table.copy()
        self.global_variables_table = global_variables_table

    def run(self):
        last_position = -1
        while not self.is_completed():
            if last_position == self.position:
                self.dump_error_message('find infinite loop')
            last_position = self.position
            self.eval_statement()

        # self.dump_variable_table()
        return

def script_text(script_text):

    global_variables_table = {}
    global_variables_table['false'] = token_utils.boolean_token(False)
    global_variables_table['true'] = token_utils.boolean_token(True)
    global_variables_table['alert'] = token_utils.function_token('alert', [
                                                                 'message'], '')
    global_variables_table[
        'toString'] = token_utils.function_token('toString', [], '')

    location = {'type': 'trap', 'value': 'window.location',
                'href': token_utils.none_token()}
    window = {'type': 'trap', 'value': 'window', 'location': location, 'href': token_utils.string_token('')}

    global_variables_table['location'] = location
    global_variables_table['window'] = window

    interpreter = Interpreter()
    interpreter.load(
        script_text, global_variables_table=global_variables_table)
    interpreter.run()

    # interpreter.dump_variable_table()
    # find the redirect url
    # print('redirect to', token_utils.value(location['href']))
    return token_utils.value(location['href'])


def run_script_file(filename):
    with open(filename, 'r') as txt:
        text = re.sub('<[^>]*>', '', txt.read())
        with open('output.js', 'w') as output:
            output.write(text.replace('\n', ' '))

    return script_text(text)

'''
use_custom_test_file = False



test_text = 'var a, b=11, c;a=1.1;c=dhello \\\" world!";c=-1+10+2*3*(-4);;var f=a+b+c;c(f);'
unit_test()
'''
import sys, re
if len(sys.argv) == 2:
    url = run_script_file(sys.argv[1])
    print()
    print('redirect url: %s' % url)
