import pytest
from pydantic import ValidationError

from app.schemas.run import MAX_RUN_INPUT_BYTES, RunCreate
from app.schemas.storable import contains_nul


def test_input_defaults_to_an_empty_object() -> None:
    assert RunCreate.model_validate({}).input == {}


def test_input_is_kept_as_given() -> None:
    value = {"incident": "latency spike", "services": ["api", "db"], "severity": 2, "ok": None}
    assert RunCreate.model_validate({"input": value}).input == value


@pytest.mark.parametrize("value", ["text", 3, ["a"], None])
def test_input_must_be_an_object(value: object) -> None:
    with pytest.raises(ValidationError):
        RunCreate.model_validate({"input": value})


def test_unknown_fields_are_rejected() -> None:
    with pytest.raises(ValidationError, match="extra"):
        RunCreate.model_validate({"input": {}, "priority": "high"})


def test_input_at_the_size_limit_is_accepted_and_one_byte_over_is_not() -> None:
    # {"k":"aaa..."} is 8 bytes of punctuation and key around the string.
    at_limit = {"k": "a" * (MAX_RUN_INPUT_BYTES - 8)}
    assert RunCreate.model_validate({"input": at_limit}).input == at_limit

    with pytest.raises(ValidationError, match="the limit is 65536"):
        RunCreate.model_validate({"input": {"k": "a" * (MAX_RUN_INPUT_BYTES - 7)}})


def test_size_is_measured_in_bytes_not_characters() -> None:
    # Each of these characters is 3 bytes in UTF-8, so a third of the limit is already too many.
    with pytest.raises(ValidationError, match="the limit is"):
        RunCreate.model_validate({"input": {"k": "€" * (MAX_RUN_INPUT_BYTES // 3)}})


@pytest.mark.parametrize("number", [float("nan"), float("inf"), float("-inf")])
def test_numbers_that_jsonb_cannot_store_are_rejected(number: float) -> None:
    with pytest.raises(ValidationError, match="NaN or Infinity"):
        RunCreate.model_validate({"input": {"nested": [{"value": number}]}})


@pytest.mark.parametrize(
    "value",
    [{"note": "a\x00b"}, {"a\x00b": 1}, {"list": ["ok", {"deep": "\x00"}]}],
    ids=["string value", "key", "nested"],
)
def test_nul_characters_are_rejected_anywhere_in_the_input(value: dict[str, object]) -> None:
    with pytest.raises(ValidationError, match="NUL"):
        RunCreate.model_validate({"input": value})


def test_contains_nul_ignores_values_that_are_not_text() -> None:
    assert not contains_nul({"a": [1, 2.5, True, None, {"b": "plain"}]})
    # The six characters backslash-u-0-0-0-0 are ordinary text, not a NUL character.
    assert not contains_nul({"a": "\\u0000"})
