"""
Semantic operations on Part IR.

This module defines operations that can be applied to a Part to modify it.
Operations are immutable - they return a new Part instance rather than
modifying the existing one. This makes it easy to validate, undo/redo,
and apply operations from LLM agents.
"""

from typing import Protocol, Literal, Union
from pydantic import BaseModel, Field
from app.core.ir import Part, Param, Feature


# Pydantic models for JSON-serializable operations (for LLM)
class SetParameterOperation(BaseModel):
    """Operation to set a parameter value."""
    type: Literal["set_parameter"] = "set_parameter"
    name: str
    value: float


class UpdateParameterToleranceOperation(BaseModel):
    """Operation to update a parameter's tolerance class."""
    type: Literal["update_parameter_tolerance"] = "update_parameter_tolerance"
    name: str
    tolerance_class: str | None = None


class AddFeatureOperation(BaseModel):
    """Operation to add a new feature."""
    type: Literal["add_feature"] = "add_feature"
    feature: Feature


class UpdateFeatureOperation(BaseModel):
    """Operation to update an existing feature."""
    type: Literal["update_feature"] = "update_feature"
    feature_name: str
    params: dict[str, float | str] = Field(default_factory=dict)


# Union type for all operations
Operation = Union[
    SetParameterOperation,
    UpdateParameterToleranceOperation,
    AddFeatureOperation,
    UpdateFeatureOperation,
]

# Legacy classes for backward compatibility (used internally)
class SetParameter:
    """Operation to set a parameter value."""
    
    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value


class UpdateParameterTolerance:
    """Operation to update a parameter's tolerance class."""
    
    def __init__(self, name: str, tolerance_class: str | None):
        self.name = name
        self.tolerance_class = tolerance_class


class AddFeature:
    """Operation to add a new feature."""
    
    def __init__(self, feature: Feature):
        self.feature = feature


class UpdateFeature:
    """Operation to update an existing feature."""
    
    def __init__(self, name: str, feature: Feature):
        self.name = name
        self.feature = feature


class RemoveFeature:
    """Operation to remove a feature (placeholder for future use)."""
    
    def __init__(self, name: str):
        self.name = name


def apply_operations(part: Part, ops: list[Union[SetParameter, UpdateParameterTolerance, AddFeature, UpdateFeature, Operation]]) -> Part:
    """
    Apply a list of operations to a Part, returning a new Part instance.
    
    Operations are applied in order. Each operation creates a new Part,
    so the original is never modified.
    
    Args:
        part: The original Part
        ops: List of operations to apply
        
    Returns:
        A new Part with operations applied
        
    Raises:
        ValueError: If an operation is invalid (e.g., parameter doesn't exist)
    """
    current_part = part.model_copy(deep=True)
    
    for op in ops:
        # Convert Pydantic operations to legacy classes if needed
        if isinstance(op, (SetParameterOperation, UpdateParameterToleranceOperation, AddFeatureOperation, UpdateFeatureOperation)):
            if isinstance(op, SetParameterOperation):
                op = SetParameter(name=op.name, value=op.value)
            elif isinstance(op, UpdateParameterToleranceOperation):
                op = UpdateParameterTolerance(name=op.name, tolerance_class=op.tolerance_class)
            elif isinstance(op, AddFeatureOperation):
                op = AddFeature(feature=op.feature)
            elif isinstance(op, UpdateFeatureOperation):
                # Find existing feature and create updated version
                existing_feature = None
                for f in current_part.features:
                    if f.name == op.feature_name:
                        existing_feature = f
                        break
                if not existing_feature:
                    raise ValueError(f"Feature '{op.feature_name}' does not exist")
                # Merge params
                updated_params = existing_feature.params.copy()
                updated_params.update(op.params)
                updated_feature = Feature(
                    type=existing_feature.type,
                    name=existing_feature.name,
                    params=updated_params,
                    critical=existing_feature.critical
                )
                op = UpdateFeature(name=op.feature_name, feature=updated_feature)
        
        if isinstance(op, SetParameter):
            if op.name not in current_part.params:
                raise ValueError(f"Parameter '{op.name}' does not exist")
            # Create new Param with updated value
            old_param = current_part.params[op.name]
            current_part.params[op.name] = Param(
                name=old_param.name,
                value=op.value,
                unit=old_param.unit,
                tolerance_class=old_param.tolerance_class
            )
            
        elif isinstance(op, UpdateParameterTolerance):
            if op.name not in current_part.params:
                raise ValueError(f"Parameter '{op.name}' does not exist")
            # Create new Param with updated tolerance
            old_param = current_part.params[op.name]
            current_part.params[op.name] = Param(
                name=old_param.name,
                value=old_param.value,
                unit=old_param.unit,
                tolerance_class=op.tolerance_class
            )
            
        elif isinstance(op, AddFeature):
            # Check if feature with same name already exists
            if any(f.name == op.feature.name for f in current_part.features):
                raise ValueError(f"Feature '{op.feature.name}' already exists")
            current_part.features.append(op.feature)
            
        elif isinstance(op, UpdateFeature):
            # Find and update the feature
            found = False
            for i, feature in enumerate(current_part.features):
                if feature.name == op.name:
                    current_part.features[i] = op.feature
                    found = True
                    break
            if not found:
                raise ValueError(f"Feature '{op.name}' does not exist")
                
        elif isinstance(op, RemoveFeature):
            # Remove the feature
            current_part.features = [
                f for f in current_part.features if f.name != op.name
            ]
            if len(current_part.features) == len(part.features):
                raise ValueError(f"Feature '{op.name}' does not exist")
    
    return current_part

