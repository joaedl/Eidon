"""
DSL (Domain Specific Language) parser for parametric CAD models.

Parses a simple text-based DSL into the IR (Intermediate Representation).
Uses Lark parser library for grammar definition and parsing.
"""

from typing import Any
from lark import Lark, Transformer, Token, Tree
from app.core.ir import Part, Param, Feature, Chain


# DSL Grammar definition for Lark
DSL_GRAMMAR = """
start: part_def

part_def: "part" CNAME "{" part_body "}"

part_body: (param_def | feature_def | chain_def)*

param_def: "param" CNAME "=" NUMBER unit tolerance_spec?
unit: CNAME
tolerance_spec: "tolerance" CNAME

feature_def: "feature" CNAME "=" feature_type "(" feature_args ")"
feature_type: CYLINDER | HOLE | CHAMFER | JOINT_INTERFACE | LINK_BODY | POCKET | FILLET
CYLINDER: "cylinder"
HOLE: "hole"
CHAMFER: "chamfer"
JOINT_INTERFACE: "joint_interface"
LINK_BODY: "link_body"
POCKET: "pocket"
FILLET: "fillet"
feature_args: [feature_arg ("," feature_arg)*]
feature_arg: CNAME "=" (CNAME | STRING | NUMBER | NUMBER unit)
STRING: /"[^"]*"/

chain_def: "chain" CNAME "{" chain_body "}"
chain_body: "terms" "=" "[" term_list "]"
term_list: [CNAME ("," CNAME)*]

%import common.CNAME
%import common.NUMBER
%import common.WS
%ignore WS
"""


class DSLTransformer(Transformer):
    """Transforms Lark parse tree into IR objects."""
    
    def feature_type(self, args):
        # Now feature_type should have a token child (CYLINDER, HOLE, or CHAMFER)
        if len(args) > 0:
            token = args[0]
            if isinstance(token, Token):
                token_str = str(token)
                # Map token type to feature type
                if token.type in ['CYLINDER', 'HOLE', 'CHAMFER']:
                    return token_str.lower()
                return token_str.lower()
            return str(token).lower()
        return ""
    
    def start(self, args):
        return args[0]
    
    def part_def(self, args):
        name = str(args[0])
        body = args[1]  # This is a Part object from part_body
        body.name = name
        return body
    
    def part_body(self, args):
        """Collects all param_def, feature_def, and chain_def into a structure."""
        params = {}
        features = []
        chains = []
        
        for item in args:
            if isinstance(item, dict):
                if "param" in item:
                    param_obj = item["param"]
                    params[param_obj.name] = param_obj
                elif "feature" in item:
                    features.append(item["feature"])
                elif "chain" in item:
                    chains.append(item["chain"])
        
        # Create Part object
        return Part(
            name="",  # Will be set from part_def
            params=params,
            features=features,
            chains=chains
        )
    
    def param_def(self, args):
        name = str(args[0])
        value = float(args[1])
        unit = str(args[2]) if len(args) > 2 else "mm"
        tolerance = None
        if len(args) > 3:
            tolerance = str(args[3])
        
        return {
            "param": Param(
                name=name,
                value=value,
                unit=unit,
                tolerance_class=tolerance
            )
        }
    
    def unit(self, args):
        return str(args[0])
    
    def tolerance_spec(self, args):
        return str(args[0])
    
    def feature_def(self, args):
        name = str(args[0])
        
        # args structure: [name, feature_type_result, feature_args]
        if len(args) < 2:
            raise ValueError(f"Feature '{name}' missing type")
        
        feature_type_val = args[1]
        if isinstance(feature_type_val, Token):
            feature_type_val = str(feature_type_val).lower()
        else:
            feature_type_val = str(feature_type_val).lower()
        
        # Validate it's one of the allowed types
        if feature_type_val not in ["cylinder", "hole", "chamfer"]:
            raise ValueError(f"Feature '{name}' has invalid type: {feature_type_val}")
        
        feature_args = args[2] if len(args) > 2 else {}
        
        return {
            "feature": Feature(
                type=feature_type_val,
                name=name,
                params=feature_args
            )
        }
    
    
    def feature_args(self, args):
        """Parse feature arguments into a dict."""
        params = {}
        for arg in args:
            if isinstance(arg, dict):
                params.update(arg)
        return params
    
    def feature_arg(self, args):
        """Parse a single feature argument: name = value."""
        key = str(args[0])
        value = args[1]
        
        # Value can be:
        # - A parameter name (CNAME) - Token
        # - A string literal (STRING) - Token with quotes
        # - A number (NUMBER) - Token or float
        # - A number with unit (NUMBER unit) - tuple or list
        if isinstance(value, Token):
            token_str = str(value)
            # Check if it's a string literal (with quotes)
            if token_str.startswith('"') and token_str.endswith('"'):
                # Remove quotes
                return {key: token_str[1:-1]}
            # Check if it's a number
            try:
                num_val = float(token_str)
                return {key: num_val}
            except ValueError:
                # It's a parameter reference (CNAME)
                return {key: token_str}
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            # It's a number with unit: (number, unit)
            num, unit = value
            num_val = float(num) if isinstance(num, Token) else num
            return {key: f"{num_val} {unit}"}
        elif isinstance(value, (int, float)):
            return {key: float(value)}
        else:
            # Try to convert to string
            return {key: str(value)}
    
    def chain_def(self, args):
        name = str(args[0])
        terms = args[1]
        
        return {
            "chain": Chain(
                name=name,
                terms=terms
            )
        }
    
    def chain_body(self, args):
        return args[0]  # Return the term_list
    
    def term_list(self, args):
        """Extract list of parameter names."""
        return [str(arg) for arg in args]


def parse_dsl_to_ir(dsl_text: str) -> Part:
    """
    Parse DSL text into a Part IR object.
    
    Args:
        dsl_text: The DSL source code as a string
        
    Returns:
        Part: The parsed part representation
        
    Raises:
        Exception: If parsing fails
    """
    parser = Lark(DSL_GRAMMAR, start="start", parser="lalr")
    transformer = DSLTransformer()
    
    tree = parser.parse(dsl_text)
    part = transformer.transform(tree)
    
    return part

