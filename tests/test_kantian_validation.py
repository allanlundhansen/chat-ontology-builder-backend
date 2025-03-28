import pytest
from src.validation.kantian_validator import KantianValidator, KantianValidationError

@pytest.mark.parametrize("quality,valid", [
    ("Reality", True),
    ("Negation", True),
    ("Limitation", True),
    ("Existence", False),
    (None, True)
])
def test_quality_validation(quality, valid):
    concept_data = {"name": "TestConcept"}
    if quality is not None:
        concept_data["quality"] = quality
    
    if valid:
        KantianValidator.validate_concept(concept_data)
    else:
        with pytest.raises(KantianValidationError) as exc_info:
            KantianValidator.validate_concept(concept_data)
        assert exc_info.value.field == "quality"

@pytest.mark.parametrize("rel_type,properties,valid", [
    ("SPATIALLY_RELATES_TO", {"distance": 5, "spatial_unit": "meters"}, True),
    ("SPATIALLY_RELATES_TO", {"distance": 5}, False),
    ("CAUSES", {"confidence": 0.8}, True)
])
def test_relationship_validation(rel_type, properties, valid):
    if valid:
        KantianValidator.validate_relationship(rel_type, properties)
    else:
        with pytest.raises(KantianValidationError):
            KantianValidator.validate_relationship(rel_type, properties) 