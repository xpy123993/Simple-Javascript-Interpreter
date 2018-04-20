# Simple JavaScript Interpreter
Simple JavaScript interpreter used for web scrapper

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
