from llm.service import OllamaClient


class BrokenClient(OllamaClient):
    def _post(self, path, payload):
        raise OSError("offline")


def test_ollama_error_is_captured_not_raised():
    result = BrokenClient().generate("not-installed", "system", "prompt")
    assert "offline" in result["error"]
    assert result["raw_response"] == ""
    assert result["parse_error"] == "empty response"
