from typing import Optional, Set

class KantianValidationError(ValueError):
    """Base exception for validation failures"""
    def __init__(self, message, field=None):
        super().__init__(message)
        self.field = field

class KantianValidator:
    """Centralized validation for Kantian category constraints"""
    
    # Domain-specific constraints
    ALLOWED_QUALITIES = {"Reality", "Negation", "Limitation"}
    ALLOWED_MODALITIES = {
        "Possibility/Impossibility",
        "Existence/Non-existence", 
        "Necessity/Contingency"
    }
    
    # --- ADD Allowed Spatial Units ---
    ALLOWED_SPATIAL_UNITS: Set[str] = {
        "meters", "kilometers", "miles", "feet", "inches", "centimeters", "millimeters"
        # Add any other units required by your spec
    }
    
    # --- ADD Allowed Spatial Relation Types ---
    ALLOWED_SPATIAL_RELATION_TYPES: Set[str] = {
        "near", "far", "contains", "within", "overlaps", "intersects", "disjoint",
        "above", "below", "left", "right", "front", "back" # Added more common types
    }
    
    @classmethod
    def validate_concept(cls, concept_data: dict) -> None:
        """Validate concept properties against Kantian constraints"""
        cls._validate_quality(concept_data.get('quality'))
        cls._validate_modality(concept_data.get('modality'))
    
    @classmethod
    def _validate_quality(cls, value: Optional[str]) -> None:
        if value is None:
            return
        if value not in cls.ALLOWED_QUALITIES:
            raise KantianValidationError(
                f"Invalid Quality: {value}. Must be one of {cls.ALLOWED_QUALITIES}",
                field="quality"
            )
    
    @classmethod
    def _validate_modality(cls, value: Optional[str]) -> None:
        if value is None:
            return
        if value not in cls.ALLOWED_MODALITIES:
            raise KantianValidationError(
                f"Invalid Modality: {value}. Must be one of {cls.ALLOWED_MODALITIES}",
                field="modality"
            )
    
    @classmethod
    def validate_relationship(cls, rel_type: str, properties: dict) -> None:
        """Validate relationship properties based on type."""
        if rel_type == "SPATIALLY_RELATES_TO":
            # Check 1: Missing unit when distance is present
            if 'distance' in properties and 'spatial_unit' not in properties:
                raise KantianValidationError(
                    "Spatial relationships require 'spatial_unit' when 'distance' is present",
                    field="spatial_unit"
                )
            # Check 2: Invalid unit when unit IS present
            elif 'spatial_unit' in properties:
                unit = properties['spatial_unit']
                if unit not in cls.ALLOWED_SPATIAL_UNITS:
                    raise KantianValidationError(
                        f"Invalid spatial_unit: '{unit}'. Must be one of {cls.ALLOWED_SPATIAL_UNITS}",
                        field="spatial_unit"
                    )

            # --- ADD Check 3: Invalid relation_type when it IS present ---
            if 'relation_type' in properties:
                spatial_rel_type = properties['relation_type']
                if spatial_rel_type not in cls.ALLOWED_SPATIAL_RELATION_TYPES:
                    raise KantianValidationError(
                        f"Invalid relation_type for SPATIALLY_RELATES_TO: '{spatial_rel_type}'. Must be one of {cls.ALLOWED_SPATIAL_RELATION_TYPES}",
                        field="relation_type"
                    )

        # --- Add checks for other relationship types if needed ---
        # elif rel_type == "PRECEDES":
        #    # Validate temporal properties like 'temporal_unit'
        #    pass
    
    @classmethod
    def _validate_spatial_unit(cls, value: Optional[str]) -> None:
        if value is None:
            return
        # Implement the logic to validate the spatial unit
        # This is a placeholder and should be replaced with the actual validation logic
        pass 