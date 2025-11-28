"""
Tests for DSL parser.
"""

import pytest
from app.core.dsl_parser import parse_dsl_to_ir
from app.core.ir import Part, Param, Feature, Chain


def test_parse_simple_part():
    """Test parsing a simple part with parameters."""
    dsl = """
    part test_part {
      param dia = 20 mm
      param length = 80 mm
    }
    """
    
    part = parse_dsl_to_ir(dsl)
    
    assert part.name == "test_part"
    assert len(part.params) == 2
    assert "dia" in part.params
    assert part.params["dia"].value == 20.0
    assert part.params["dia"].unit == "mm"
    assert part.params["length"].value == 80.0


def test_parse_with_tolerance():
    """Test parsing parameters with tolerance classes."""
    dsl = """
    part test_part {
      param dia = 20 mm tolerance g6
      param length = 80 mm
    }
    """
    
    part = parse_dsl_to_ir(dsl)
    
    assert part.params["dia"].tolerance_class == "g6"
    assert part.params["length"].tolerance_class is None


def test_parse_cylinder_feature():
    """Test parsing a cylinder feature."""
    dsl = """
    part test_part {
      param dia = 20 mm
      param length = 80 mm
      feature base = cylinder(dia_param=dia, length_param=length)
    }
    """
    
    part = parse_dsl_to_ir(dsl)
    
    assert len(part.features) == 1
    feature = part.features[0]
    assert feature.type == "cylinder"
    assert feature.name == "base"
    assert feature.params["dia_param"] == "dia"
    assert feature.params["length_param"] == "length"


def test_parse_chamfer_feature():
    """Test parsing a chamfer feature."""
    dsl = """
    part test_part {
      param size = 1 mm
      feature chamfer_end = chamfer(edge=end, size_param=size)
    }
    """
    
    part = parse_dsl_to_ir(dsl)
    
    assert len(part.features) == 1
    feature = part.features[0]
    assert feature.type == "chamfer"
    assert feature.params["size_param"] == "size"
    assert feature.params["edge"] == "end"


def test_parse_chain():
    """Test parsing a dimensional chain."""
    dsl = """
    part test_part {
      param length = 80 mm
      chain length_chain {
        terms = [length]
      }
    }
    """
    
    part = parse_dsl_to_ir(dsl)
    
    assert len(part.chains) == 1
    chain = part.chains[0]
    assert chain.name == "length_chain"
    assert chain.terms == ["length"]


def test_parse_complete_example():
    """Test parsing the default shaft example."""
    dsl = """
    part shaft {
      param dia = 20 mm tolerance g6
      param length = 80 mm

      feature base = cylinder(dia_param=dia, length_param=length)
      feature chamfer_end = chamfer(edge=end, size_param=1 mm)

      chain length_chain {
        terms = [length]
      }
    }
    """
    
    part = parse_dsl_to_ir(dsl)
    
    assert part.name == "shaft"
    assert len(part.params) == 2
    assert len(part.features) == 2
    assert len(part.chains) == 1

