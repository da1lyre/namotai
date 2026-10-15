from aiogram.fsm.state import State, StatesGroup


class GenerateFlow(StatesGroup):
    waiting_for_source = State()
    waiting_for_difficulty = State()
    waiting_for_count = State()
    waiting_for_confirmation = State()
    processing = State()
