"""
DSL (Domain Specific Language) parser for parametric CAD models.

Parses a simple text-based DSL into the IR (Intermediate Representation).
Uses Lark parser library for grammar definition and parsing.
"""

from typing import Any
from lark import Lark, Transformer, Token, Tree
from app.core.ir import Part, Param, Feature, Chain, Sketch, SketchEntity, SketchConstraint, SketchDimension


# DSL Grammar definition for Lark
DSL_GRAMMAR = """
start: part_def

part_def: "part" CNAME "{" part_body "}"

part_body: (param_def | feature_def | chain_def)*

param_def: "param" CNAME "=" NUMBER unit tolerance_spec?
unit: CNAME
tolerance_spec: "tolerance" CNAME

feature_def: "feature" CNAME "=" feature_type "(" feature_args ")" | sketch_feature_def
feature_type: SKETCH | EXTRUDE
# MVP: Only sketch and extrude supported
SKETCH: "sketch"
EXTRUDE: "extrude"
sketch_feature_def: "feature" CNAME "=" "sketch" "(" sketch_args ")" sketch_body
sketch_args: [sketch_arg ("," sketch_arg)*]
sketch_arg: CNAME "=" (CNAME | STRING)
sketch_body: "{" sketch_content "}"
sketch_content: (sketch_line | sketch_circle | sketch_rectangle | sketch_constraint | sketch_dim_length | sketch_dim_diameter)*
sketch_line: "line" CNAME "from" point "to" point
sketch_circle: "circle" CNAME "center" point "radius" NUMBER unit?
sketch_rectangle: "rectangle" CNAME "from" point "to" point
point: "(" NUMBER "," NUMBER ")"
sketch_constraint: CONSTRAINT_TYPE "(" entity_list ")"
CONSTRAINT_TYPE: "horizontal" | "vertical" | "coincident"
entity_list: CNAME ("," CNAME)*
sketch_dim_length: "dim_length" "(" CNAME "," NUMBER unit ")"
sketch_dim_diameter: "dim_diameter" "(" CNAME "," NUMBER unit ")"
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
        # MVP: Only SKETCH and EXTRUDE supported
        if len(args) > 0:
            token = args[0]
            if isinstance(token, Token):
                token_str = str(token).lower()
                # Only allow sketch and extrude
                if token.type in ['SKETCH', 'EXTRUDE']:
                    return token_str
                raise ValueError(f"Feature type '{token_str}' not supported in MVP. Only 'sketch' and 'extrude' are available.")
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
        # Check if this is already a processed sketch feature (from sketch_feature_def)
        if len(args) == 1 and isinstance(args[0], dict) and "feature" in args[0]:
            return args[0]
        
        name = str(args[0])
        
        # args structure: [name, feature_type_result, feature_args]
        if len(args) < 2:
            raise ValueError(f"Feature '{name}' missing type")
        
        feature_type_val = args[1]
        if isinstance(feature_type_val, Token):
            feature_type_val = str(feature_type_val).lower()
        else:
            feature_type_val = str(feature_type_val).lower()
        
        # MVP: Only sketch and extrude are supported
        if feature_type_val not in ["sketch", "extrude"]:
            raise ValueError(f"Feature type '{feature_type_val}' not supported in MVP. Only 'sketch' and 'extrude' are available.")
        
        feature_args = args[2] if len(args) > 2 else {}
        
        return {
            "feature": Feature(
                type=feature_type_val,
                name=name,
                params=feature_args
            )
        }
    
    def sketch_feature_def(self, args):
        """Parse a sketch feature definition.
        
        Args structure: [name, sketch_args, sketch_body]
        """
        name = str(args[0])
        sketch_args_dict = args[1] if len(args) > 1 else {}
        sketch_body_dict = args[2] if len(args) > 2 else {}
        
        # Extract plane from sketch_args (remove quotes if present)
        plane = sketch_args_dict.get("on_plane", "front_plane")
        if isinstance(plane, str) and plane.startswith('"') and plane.endswith('"'):
            plane = plane[1:-1]
        
        # Extract entities, constraints, dimensions from sketch_body
        entities = sketch_body_dict.get("entities", [])
        constraints = sketch_body_dict.get("constraints", [])
        dimensions = sketch_body_dict.get("dimensions", [])
        
        sketch = Sketch(
            name=name,
            plane=plane,
            entities=entities,
            constraints=constraints,
            dimensions=dimensions
        )
        
        return {
            "feature": Feature(
                type="sketch",
                name=name,
                params={"plane": plane},
                sketch=sketch
            )
        }
    
    def sketch_args(self, args):
        """Parse sketch arguments (e.g., on_plane="right_plane")."""
        result = {}
        for arg in args:
            if isinstance(arg, dict):
                result.update(arg)
        return result
    
    def sketch_arg(self, args):
        """Parse a single sketch argument."""
        key = str(args[0])
        value = args[1] if len(args) > 1 else ""
        if isinstance(value, Token):
            value = str(value)
        return {key: value}
    
    def sketch_body(self, args):
        """Parse sketch body content."""
        content = args[0] if args else {}
        return {
            "entities": content.get("entities", []),
            "constraints": content.get("constraints", []),
            "dimensions": content.get("dimensions", [])
        }
    
    def sketch_content(self, args):
        """Collect sketch content items."""
        entities = []
        constraints = []
        dimensions = []
        
        for item in args:
            if isinstance(item, dict):
                if "entity" in item:
                    entities.append(item["entity"])
                elif "constraint" in item:
                    constraints.append(item["constraint"])
                elif "dimension" in item:
                    dimensions.append(item["dimension"])
        
        return {
            "entities": entities,
            "constraints": constraints,
            "dimensions": dimensions
        }
    
    def sketch_line(self, args):
        """Parse a line entity."""
        # args: ["line", id, "from", point, "to", point]
        entity_id = str(args[0])
        from_point = args[2] if len(args) > 2 else (0.0, 0.0)
        to_point = args[4] if len(args) > 4 else (0.0, 0.0)
        return {
            "entity": SketchEntity(
                id=entity_id,
                type="line",
                start=from_point,
                end=to_point
            )
        }
    
    def sketch_circle(self, args):
        """Parse a circle entity."""
        # args: ["circle", id, "center", point, "radius", value, unit?]
        entity_id = str(args[0])
        center = args[2] if len(args) > 2 else (0.0, 0.0)
        radius = float(args[4]) if len(args) > 4 else 0.0
        return {
            "entity": SketchEntity(
                id=entity_id,
                type="circle",
                center=center,
                radius=radius
            )
        }
    
    def sketch_rectangle(self, args):
        """Parse a rectangle entity."""
        # args: ["rectangle", id, "from", point, "to", point]
        entity_id = str(args[0])
        corner1 = args[2] if len(args) > 2 else (0.0, 0.0)
        corner2 = args[4] if len(args) > 4 else (0.0, 0.0)
        return {
            "entity": SketchEntity(
                id=entity_id,
                type="rectangle",
                corner1=corner1,
                corner2=corner2
            )
        }
    
    def point(self, args):
        """Parse a point (x, y)."""
        x = float(args[0]) if len(args) > 0 else 0.0
        y = float(args[1]) if len(args) > 1 else 0.0
        return (x, y)
    
    def sketch_constraint(self, args):
        """Parse a sketch constraint."""
        constraint_type = str(args[0]).lower()
        entity_ids = args[1] if len(args) > 1 else []
        
        constraint_id = f"c_{len(args)}"  # Simple ID generation
        
        return {
            "constraint": SketchConstraint(
                id=constraint_id,
                type=constraint_type,
                entity_ids=entity_ids if isinstance(entity_ids, list) else [str(entity_ids)]
            )
        }
    
    def entity_list(self, args):
        """Parse a list of entity IDs."""
        return [str(arg) for arg in args]
    
    def sketch_dim_length(self, args):
        """Parse a length dimension: dim_length(entity_id, value unit)."""
        # args: [entity_id, value, unit?]
        entity_id = str(args[0]) if len(args) > 0 else ""
        value = float(args[1]) if len(args) > 1 else 0.0
        unit = str(args[2]) if len(args) > 2 else "mm"
        
        dim_id = f"d_length_{entity_id}"
        return {
            "dimension": SketchDimension(
                id=dim_id,
                type="length",
                entity_ids=[entity_id],
                value=value,
                unit=unit
            )
        }
    
    def sketch_dim_diameter(self, args):
        """Parse a diameter dimension: dim_diameter(entity_id, value unit)."""
        # args: [entity_id, value, unit?]
        entity_id = str(args[0]) if len(args) > 0 else ""
        value = float(args[1]) if len(args) > 1 else 0.0
        unit = str(args[2]) if len(args) > 2 else "mm"
        
        dim_id = f"d_diameter_{entity_id}"
        return {
            "dimension": SketchDimension(
                id=dim_id,
                type="diameter",
                entity_ids=[entity_id],
                value=value,
                unit=unit
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

