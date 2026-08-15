from change_management import ChangeCommunicationGenerator, ChangeRequest


def test_change_communication_generator_creates_arabic_and_english_messages():
    request = ChangeRequest("CHG-16", "Planned change", "Detailed impact", "alice")
    messages = ChangeCommunicationGenerator().generate(request, "pre_change", ["noc", "owner"], language="both")
    assert len(messages) == 2
    assert {message.language for message in messages} == {"ar", "en"}
    assert all(message.sent is False for message in messages)
    assert all(request.change_id in message.subject for message in messages)
