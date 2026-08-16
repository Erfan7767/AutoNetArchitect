from windows_app.release_scope import PackageTrustState, default_windows_v1_scope


def test_unsigned_v1_scope_requires_visible_warning_and_stays_lab_only() -> None:
    scope = default_windows_v1_scope("C:/AutoNetArchitect/workspace", PackageTrustState.UNSIGNED)
    assert scope.can_install() is True
    assert scope.requires_warning() is True
    assert scope.laboratory_only is True
    assert scope.production_device_execution is False
    assert scope.local_workspace.secrets_stored_locally is False


def test_discovery_requires_explicit_scope_consent() -> None:
    scope = default_windows_v1_scope("C:/AutoNetArchitect/workspace", PackageTrustState.SIGNED)
    assert scope.can_start_discovery(consent_recorded=False) is False
    assert scope.can_start_discovery(consent_recorded=True) is True


def test_unknown_package_trust_cannot_be_presented_as_signed() -> None:
    scope = default_windows_v1_scope("C:/AutoNetArchitect/workspace", PackageTrustState.UNKNOWN)
    assert scope.can_install() is False
    assert scope.requires_warning() is True
