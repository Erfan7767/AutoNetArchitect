from config_generators.base_generator import BaseGenerator, DeviceConfig


class ExampleGenerator(BaseGenerator):
    def __init__(self):
        super().__init__("ExampleVendor", "example", "base.j2")


def test_generated_artifact_is_versioned_and_serializable():
    result = ExampleGenerator().generate({"device_id": "edge-1", "features": []})
    assert isinstance(result.artifact, DeviceConfig)
    assert result.artifact.schema_version == "1.0"
    assert result.artifact.status == "generated_empty_config"
    assert result.artifact.artifact_hash
    assert result.artifact.to_dict()["device_id"] == "edge-1"


def test_inline_secret_is_blocked_and_not_rendered():
    result = ExampleGenerator().generate({"device_id": "edge-1", "secrets": {"password": "clear-text"}, "features": []})
    assert result.artifact.status == "blocked_unsupported_features"
    assert result.artifact.rendered_config == ""
    assert result.artifact.secret_references == ()
