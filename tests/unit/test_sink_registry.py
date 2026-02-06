from core.sinks.registry import SinkRegistry


def test_match_fqn_sink():
    registry = SinkRegistry("data/sink_catalog.json")
    sink = registry.match_sink("java.io.File.exists")
    assert sink is not None
    assert sink["risk"] == "Environment Verification"


def test_prevent_false_positive():
    registry = SinkRegistry("data/sink_catalog.json")
    sink = registry.match_sink("com.app.update_open_status")
    assert sink is None


def test_dual_use_context_relevant():
    registry = SinkRegistry("data/sink_catalog.json")
    sink = registry.match_sink("java.io.File.exists")
    assert registry.is_security_relevant_call(
        sink, ["/system/xbin/su"]
    ) is True


def test_dual_use_context_irrelevant():
    registry = SinkRegistry("data/sink_catalog.json")
    sink = registry.match_sink("java.io.File.exists")
    assert registry.is_security_relevant_call(
        sink, ["/sdcard/user/data.txt"]
    ) is False


def test_native_syscall_match():
    registry = SinkRegistry("data/sink_catalog.json")
    sink = registry.match_native_syscall(26)
    assert sink is not None
    assert sink["risk"] == "Anti-Debugging"
