from auth.rbac import PermissionDenied, Principal, RBAC, RoleDefinition


def test_rbac_default_roles_enforce_permissions():
    rbac = RBAC()
    viewer = Principal("viewer-user", ("viewer",))
    designer = Principal("designer-user", ("designer",))
    assert rbac.has_permission(viewer, "project.read")
    assert not rbac.has_permission(viewer, "deployment.execute")
    assert rbac.has_permission(designer, "config.generate")
    try:
        rbac.enforce(viewer, "deployment.execute")
    except PermissionDenied:
        pass
    else:
        raise AssertionError("viewer must not execute deployment")


def test_rbac_supports_custom_roles_and_union():
    rbac = RBAC((RoleDefinition("custom", frozenset({"custom.read"})),))
    principal = Principal("user", ("viewer", "custom"))
    assert rbac.has_permission(principal, "project.read")
    assert rbac.has_permission(principal, "custom.read")
