import reflex as rx
from typing import (
    TypedDict,
    List,
    Optional as TypingOptional,
)
import os
import anthropic


class Message(TypedDict):
    role: str
    content: str
    is_initial_greeting: TypingOptional[bool]


API_MODEL_MAPPING = {
    "Claude 3.7 Sonnet": "claude-3-5-sonnet-20240620",
    "Claude 3.5 Opus": "claude-3-opus-20240229",
    "Claude 3 Haiku": "claude-3-haiku-20240307",
}


class ChatState(rx.State):
    messages: List[Message] = []
    is_streaming: bool = False
    selected_model: str = "Claude 3 Haiku"
    error_message: str = ""

    @rx.event
    def go_back_and_clear_chat(self):
        self.messages = []
        self.is_streaming = False
        self.error_message = ""
        return rx.redirect("/")

    @rx.event
    def submit_suggestion_as_prompt(
        self, suggestion_text: str
    ):
        prompt = f"Help me {suggestion_text.lower()}"
        form_data = {"prompt_input": prompt}
        yield ChatState.send_initial_message_and_navigate(
            form_data
        )

    @rx.event
    def send_initial_message_and_navigate(
        self, form_data: dict
    ):
        prompt = form_data.get("prompt_input", "").strip()
        if not prompt or self.is_streaming:
            if not prompt:
                yield rx.toast(
                    "Please enter a message.", duration=3000
                )
            return
        self.messages = []
        self.messages.append(
            {"role": "user", "content": prompt}
        )
        self.messages.append(
            {
                "role": "assistant",
                "content": "",
                "is_initial_greeting": False,
            }
        )
        self.is_streaming = True
        self.error_message = ""
        yield ChatState.stream_anthropic_response
        yield rx.redirect("/chat")

    @rx.event
    def send_chat_page_message(self, form_data: dict):
        prompt = form_data.get(
            "chat_page_prompt_input", ""
        ).strip()
        if not prompt or self.is_streaming:
            if not prompt:
                yield rx.toast(
                    "Please enter a message.", duration=3000
                )
            return
        self.messages.append(
            {"role": "user", "content": prompt}
        )
        self.messages.append(
            {
                "role": "assistant",
                "content": "",
                "is_initial_greeting": False,
            }
        )
        self.is_streaming = True
        self.error_message = ""
        yield ChatState.stream_anthropic_response

    @rx.event(background=True)
    async def stream_anthropic_response(self):
        # Prefer a direct Anthropic key.
        # Fall back to OpenRouter if present. Many OpenRouter keys are
        # prefixed with `sk-or-` and are stored in `.env` as
        # `ANTHROPIC_API_KEY` or `OPENROUTER_API_KEY`.
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        openrouter_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key and openrouter_key:
            # Use the OpenRouter key in place of ANTHROPIC_API_KEY so the
            # existing Anthropic client code can continue to work.
            api_key = openrouter_key
            # Ensure the environment variable is also set for any downstream
            # code that reads ANTHROPIC_API_KEY.
            os.environ["ANTHROPIC_API_KEY"] = openrouter_key
            # If the consumer needs to call the OpenRouter endpoint, set a
            # sensible default base to point to OpenRouter's API. This does
            # not change behavior of the Anthropic SDK directly here, but
            # provides an environment hint for libraries which respect it.
            os.environ.setdefault(
                "ANTHROPIC_API_BASE", "https://api.openrouter.ai/v1"
            )
        if not api_key:
            async with self:
                self.messages[-1][
                    "content"
                ] = "ANTHROPIC_API_KEY not set. Please configure your API key."
                self.is_streaming = False
                self.error_message = (
                    "API key not configured."
                )
            return
        client = anthropic.Anthropic(api_key=api_key)
        api_call_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in self.messages[:-1]
            if m["content"]
            and m["content"].strip()
            and (not m.get("is_initial_greeting"))
        ]
        if (
            self.messages[-2]["role"] == "user"
            and self.messages[-2]["content"].strip()
        ):
            api_call_messages.append(
                {
                    "role": "user",
                    "content": self.messages[-2]["content"],
                }
            )
        if not any(
            (m["role"] == "user" for m in api_call_messages)
        ):
            async with self:
                self.messages[-1][
                    "content"
                ] = "Cannot send an empty request to the AI."
                self.is_streaming = False
                self.error_message = "Empty request."
            return
        model_id = API_MODEL_MAPPING.get(
            self.selected_model, "claude-3-haiku-20240307"
        )
        try:
            with client.messages.stream(
                max_tokens=1024,
                messages=api_call_messages,
                model=model_id,
            ) as stream:
                for text_chunk in stream.text_stream:
                    async with self:
                        if not self.is_streaming:
                            break
                        self.messages[-1][
                            "content"
                        ] += text_chunk
                if self.is_streaming:
                    final_text_snapshot = (
                        stream.get_final_text()
                    )
                    async with self:
                        self.messages[-1][
                            "content"
                        ] = final_text_snapshot
        except anthropic.APIError as e:
            async with self:
                error_detail = (
                    f"Anthropic API Error: "
                    f"{e.message if hasattr(e, 'message') else str(e)}"
                )
                self.messages[-1]["content"] = (
                    f"Sorry, I encountered an error. {error_detail}"
                )
                self.error_message = error_detail
        except Exception as e:
            async with self:
                self.messages[-1][
                    "content"
                ] = f"An unexpected error occurred: {str(e)}"
                self.error_message = str(e)
        finally:
            async with self:
                self.is_streaming = False
