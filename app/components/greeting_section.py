import reflex as rx
import datetime

def greeting_section() -> rx.Component:
    current_time = datetime.datetime.now()
    greeting = "Good morning!" if current_time.hour < 12 else "Good afternoon!"
    return rx.el.div(
        rx.icon(
            "sparkle",
            class_name="text-[#E97055] mr-3",
            size=36,
        ),
        rx.el.h1(
            greeting,
            class_name="text-4xl font-['Lora'] text-neutral-100",
        ),
        class_name="flex items-center justify-center",
    )