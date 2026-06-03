from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field


# ── Shared sub-models ──────────────────────────────────────────────

class CardSource(BaseModel):
    icon_url: str | None = None
    desc: str | None = None
    desc_color: int | None = None


class ActionMenuItem(BaseModel):
    text: str
    key: str


class ActionMenu(BaseModel):
    desc: str | None = None
    action_list: list[ActionMenuItem]


class MainTitle(BaseModel):
    title: str
    desc: str | None = None


class EmphasisContent(BaseModel):
    title: str | None = None
    desc: str | None = None


class QuoteArea(BaseModel):
    type: int | None = None
    url: str | None = None
    appid: str | None = None
    pagepath: str | None = None
    title: str | None = None
    quote_text: str | None = None


class HorizontalContentItem(BaseModel):
    keyname: str
    value: str | None = None
    type: int | None = None
    url: str | None = None
    media_id: str | None = None
    userid: str | None = None


class JumpItem(BaseModel):
    type: int | None = None
    title: str
    url: str | None = None
    appid: str | None = None
    pagepath: str | None = None


class CardAction(BaseModel):
    type: int
    url: str | None = None
    appid: str | None = None
    pagepath: str | None = None


class CardImage(BaseModel):
    url: str
    aspect_ratio: float | None = None


class VerticalContentItem(BaseModel):
    title: str
    desc: str | None = None


class ImageTextArea(BaseModel):
    type: int | None = None
    url: str | None = None
    appid: str | None = None
    pagepath: str | None = None
    title: str | None = None
    desc: str | None = None
    image_url: str


# ── Button interaction sub-models ──────────────────────────────────

class ButtonOption(BaseModel):
    id: str
    text: str


class ButtonSelection(BaseModel):
    question_key: str
    title: str | None = None
    option_list: list[ButtonOption]
    selected_id: str | None = None


class ButtonItem(BaseModel):
    text: str
    style: int | None = None
    key: str | None = None
    url: str | None = None
    type: int | None = None


# ── Vote interaction sub-models ────────────────────────────────────

class CheckboxOption(BaseModel):
    id: str
    text: str
    is_checked: bool = False


class Checkbox(BaseModel):
    question_key: str
    option_list: list[CheckboxOption]
    mode: int | None = None


class SubmitButton(BaseModel):
    text: str | None = None
    key: str


# ── Multiple interaction sub-models ────────────────────────────────

class SelectOption(BaseModel):
    id: str
    text: str


class SelectItem(BaseModel):
    question_key: str
    title: str | None = None
    option_list: list[SelectOption]
    selected_id: str | None = None


# ── 5 card types ───────────────────────────────────────────────────

class TextNoticeCard(BaseModel):
    card_type: Literal["text_notice"] = "text_notice"
    source: CardSource | None = None
    action_menu: ActionMenu | None = None
    task_id: str | None = None
    main_title: MainTitle | None = None
    quote_area: QuoteArea | None = None
    emphasis_content: EmphasisContent | None = None
    sub_title_text: str | None = None
    horizontal_content_list: list[HorizontalContentItem] | None = None
    jump_list: list[JumpItem] | None = None
    card_action: CardAction


class NewsNoticeCard(BaseModel):
    card_type: Literal["news_notice"] = "news_notice"
    source: CardSource | None = None
    action_menu: ActionMenu | None = None
    task_id: str | None = None
    main_title: MainTitle
    quote_area: QuoteArea | None = None
    image_text_area: ImageTextArea | None = None
    card_image: CardImage | None = None
    vertical_content_list: list[VerticalContentItem] | None = None
    horizontal_content_list: list[HorizontalContentItem] | None = None
    jump_list: list[JumpItem] | None = None
    card_action: CardAction


class ButtonInteractionCard(BaseModel):
    card_type: Literal["button_interaction"] = "button_interaction"
    source: CardSource | None = None
    action_menu: ActionMenu | None = None
    main_title: MainTitle
    quote_area: QuoteArea | None = None
    sub_title_text: str | None = None
    horizontal_content_list: list[HorizontalContentItem] | None = None
    card_action: CardAction | None = None
    task_id: str
    button_selection: ButtonSelection | None = None
    button_list: list[ButtonItem]


class VoteInteractionCard(BaseModel):
    card_type: Literal["vote_interaction"] = "vote_interaction"
    source: CardSource | None = None
    main_title: MainTitle
    task_id: str
    checkbox: Checkbox
    submit_button: SubmitButton


class MultipleInteractionCard(BaseModel):
    card_type: Literal["multiple_interaction"] = "multiple_interaction"
    source: CardSource | None = None
    main_title: MainTitle
    task_id: str
    select_list: list[SelectItem]
    submit_button: SubmitButton


TemplateCard = Annotated[
    TextNoticeCard | NewsNoticeCard | ButtonInteractionCard | VoteInteractionCard | MultipleInteractionCard,
    Field(discriminator="card_type"),
]


# ── Request model ──────────────────────────────────────────────────

class SendTemplateCardRequest(BaseModel):
    touser: str | None = None
    toparty: str | None = None
    totag: str | None = None
    template_card: TemplateCard  # type: ignore[valid-type]
    enable_id_trans: int = 0
    enable_duplicate_check: int = 0
    duplicate_check_interval: int = 1800
