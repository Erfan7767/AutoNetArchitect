from documentation.formatters.approval_page_formatter import ApprovalPageFormatter

def test_approval_page_is_unapproved_by_default():
    assert ApprovalPageFormatter().build()[0]["signature"] == "PENDING"
