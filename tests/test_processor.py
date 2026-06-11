import os
from unittest import mock
from llm2sh.core.processor import QueryProcessor

def test_get_os_info():
    processor = QueryProcessor()
    info = processor.get_os_info()
    assert "os" in info
    assert "distro_name" in info
    assert "distro_version" in info

@mock.patch("llm2sh.core.processor.get_recent_history")
def test_build_context(mock_history):
    mock_history.return_value = ["echo 1", "git status"]
    
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        processor = QueryProcessor()
        context = processor.build_context()
        
        assert "os" in context
        assert "distro" in context
        assert context["shell"] == processor.settings.shell
        assert context["cwd"] == os.getcwd()
        assert context["history"] == ["echo 1", "git status"]

@mock.patch("llm2sh.core.processor.get_recent_history")
def test_build_messages(mock_history):
    mock_history.return_value = []
    with mock.patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        processor = QueryProcessor()
        messages = processor.build_messages("find pdf files")
        
        # We expect: system prompt, environment context statement, and the user query
        assert len(messages) >= 3
        assert messages[0]["role"] == "system"
        assert "You are llm2sh" in messages[0]["content"]
        assert messages[1]["role"] == "system"
        assert "User Environment Context" in messages[1]["content"]
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "find pdf files"


def test_mode_based_prompts_and_context():
    processor = QueryProcessor()
    
    # Test shell version detection
    version = processor.get_shell_version("echo")
    assert version != ""
    
    # Test available tools check
    tools = processor.get_available_tools()
    assert isinstance(tools, list)
    
    # Test system prompt changes based on mode
    translate_prompt = processor.get_system_prompt("translate")
    explain_prompt = processor.get_system_prompt("explain")
    script_prompt = processor.get_system_prompt("script")
    
    assert "convert natural language requests" in translate_prompt
    assert "explain this command" in explain_prompt
    assert "write a complete shell/bash script" in script_prompt

