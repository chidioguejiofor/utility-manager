failure_edge_case_one = {  # ((a+b)+)
    "name":
    "Energy Consumed",
    "tokens": [{
        "type": "SYMBOL",
        "symbol": "("
    }, {
        "type": "SYMBOL",
        "symbol": "("
    }, {
        "type": "PARAMETER",
        "parameter_id": "a"
    }, {
        "type": "SYMBOL",
        "symbol": "+"
    }, {
        "type": "PARAMETER",
        "parameter_id": "b"
    }, {
        "type": "SYMBOL",
        "symbol": ")"
    }, {
        "type": "SYMBOL",
        "symbol": "+"
    }, {
        "type": "SYMBOL",
        "symbol": ")"
    }]
}

failure_edge_case_two = {  # ((a+)+)
    "name":
    "Energy Consumed",
    "tokens": [{
        "type": "SYMBOL",
        "symbol": "("
    }, {
        "type": "SYMBOL",
        "symbol": "("
    }, {
        "type": "PARAMETER",
        "parameter_id": "a"
    }, {
        "type": "SYMBOL",
        "symbol": "+"
    }, {
        "type": "SYMBOL",
        "symbol": ")"
    }, {
        "type": "SYMBOL",
        "symbol": "+"
    }, {
        "type": "SYMBOL",
        "symbol": ")"
    }]
}

failure_edge_case_three = {  # a+()b
    "name":
    "Energy Consumed",
    "tokens": [
        {
            "type": "PARAMETER",
            "parameter_id": "a"
        },
        {
            "type": "SYMBOL",
            "symbol": "+"
        },
        {
            "type": "SYMBOL",
            "symbol": "("
        },
        {
            "type": "SYMBOL",
            "symbol": ")"
        },
        {
            "type": "PARAMETER",
            "parameter_id": "b"
        },
    ]
}

failure_edge_case_four = {  # (a+b(
    "name":
    "Energy Consumed",
    "tokens": [
        {
            "type": "SYMBOL",
            "symbol": "("
        },
        {
            "type": "PARAMETER",
            "parameter_id": "a"
        },
        {
            "type": "SYMBOL",
            "symbol": "+"
        },
        {
            "type": "PARAMETER",
            "parameter_id": "b"
        },
        {
            "type": "SYMBOL",
            "symbol": "("
        },
    ]
}

ending_with_math_operation_edge_case = {  # (a+b(
    "name":
    "Energy Consumed",
    "tokens": [
        {
            "type": "SYMBOL",
            "symbol": "("
        },
        {
            "type": "PARAMETER",
            "parameter_id": "a"
        },
        {
            "type": "SYMBOL",
            "symbol": "+"
        },
        {
            "type": "FORMULA",
            "formula_id": "b"
        },
        {
            "type": "SYMBOL",
            "symbol": ")"
        },
        {
            "type": "SYMBOL",
            "symbol": "+"
        },
    ]
}

starting_with_closing_bracket_edge_case = {  # (a+b(
    "name":
    "Energy Consumed",
    "tokens": [
        {
            "type": "SYMBOL",
            "symbol": ")"
        },
        {
            "type": "PARAMETER",
            "parameter_id": "a"
        },
        {
            "type": "SYMBOL",
            "symbol": "+"
        },
        {
            "type": "FORMULA",
            "formula_id": "b"
        },
        {
            "type": "SYMBOL",
            "symbol": ")"
        },
    ]
}

parameter_with_parameter_id_with_missing_parameter_id = {  # (a+b(
    "name":
    "Energy Consumed",
    "tokens": [
        {
            "type": "SYMBOL",
            "symbol": "("
        },
        {
            "type": "PARAMETER",
            "formula_id": "a"
        },
        {
            "type": "SYMBOL",
            "symbol": "+"
        },
        {
            "type": "FORMULA",
            "formula_id": "b"
        },
        {
            "type": "SYMBOL",
            "symbol": ")"
        },
    ]
}

formula_with_parameter_id_with_missing_formula_id = {  # (a+b(
    "name":
    "Energy Consumed",
    "tokens": [
        {
            "type": "SYMBOL",
            "symbol": "("
        },
        {
            "type": "FORMULA"
        },
        {
            "type": "SYMBOL",
            "symbol": "+"
        },
        {
            "type": "FORMULA",
            "formula_id": "b"
        },
        {
            "type": "SYMBOL",
            "symbol": ")"
        },
    ]
}

symbol_with_with_missing_symbol_key = {
    "name":
    "Energy Consumed",
    "tokens": [
        {
            "type": "SYMBOL",
            "symbol": "("
        },
        {
            "type": "FORMULA",
            "formula_id": "formuals-id"
        },
        {
            "type": "SYMBOL",
        },
        {
            "type": "FORMULA",
            "formula_id": "b"
        },
        {
            "type": "SYMBOL",
            "symbol": ")"
        },
    ]
}

constant_with_missing_constant_key = {
    "name":
    "Energy Consumed",
    "tokens": [
        {
            "type": "SYMBOL",
            "symbol": "("
        },
        {
            "type": "CONSTANT",
        },
        {
            "type": "SYMBOL",
            "symbol": "+"
        },
        {
            "type": "FORMULA",
            "formula_id": "b"
        },
        {
            "type": "SYMBOL",
            "symbol": ")"
        },
    ]
}


def generate_formula_with_parameter_id_data(*, parameter_id, name=None):
    name = name if name else "Energy Consumed"
    return {
        "name":
        name,
        "tokens": [{
            "type": "PARAMETER",
            "parameter_id": parameter_id
        }, {
            "type": "SYMBOL",
            "symbol": "+"
        }, {
            "type": "PARAMETER",
            "parameter_id": parameter_id
        }]
    }


def generate_formula_with_formula_id_data(*, formula_id, name=None):
    name = name if name else "Energy Consumed"
    return {
        "name":
        name,
        "tokens": [{
            "type": "FORMULA",
            "formula_id": formula_id
        }, {
            "type": "SYMBOL",
            "symbol": "+"
        }, {
            "type": "FORMULA",
            "formula_id": formula_id
        }]
    }


failure_edge_cases = {
    '((a+b)+)': failure_edge_case_one,
    '((a+)+)': failure_edge_case_two,
    'a+()b': failure_edge_case_three,
    '(a+b(': failure_edge_case_four,
    '(a+b)+': ending_with_math_operation_edge_case,
    ')a+b)': starting_with_closing_bracket_edge_case,
    'missing_parameter_id':
    parameter_with_parameter_id_with_missing_parameter_id,
    'missing_formula_id': formula_with_parameter_id_with_missing_formula_id,
    'symbol_with_missing_symbol_key': symbol_with_with_missing_symbol_key,
    'missing_constant': constant_with_missing_constant_key,
}
