import reflex as rx
from app.states.chat_state import ChatState
from app.components.header_section import header_section
from app.components.greeting_section import greeting_section
from app.components.input_section import input_section
from app.components.suggestions_section import (
    suggestions_section,
)
from app.pages.chat_page import chat_page


def index() -> rx.Component:
    return rx.el.div(
        header_section(),
        rx.el.main(
            greeting_section(),
            input_section(),
            suggestions_section(),
            class_name="flex flex-col items-center justify-center grow w-full max-w-2xl px-4 space-y-10 mt-[-5vh]",
        ),
        class_name="bg-[#202123] min-h-screen flex flex-col items-center pt-8 text-neutral-200 font-['Inter'] selection:bg-[#E97055] selection:text-white",
    )


app = rx.App(
    theme=rx.theme(appearance="light"),
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap",
        "https://fonts.googleapis.com/css2?family=Lora:wght@400;500;700&display=swap",
    ],
)
app.add_page(index)
app.add_page(chat_page, route="/chat")