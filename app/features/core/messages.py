"""User-facing Russian API messages for core domain entities."""

from app.features.core.constants import CoreErrorCode

CORE_MESSAGES: dict[str, str] = {
    CoreErrorCode.ORGANIZATION_NOT_FOUND: 'Организация не найдена',
    CoreErrorCode.ORGANIZATION_REGISTRATION_CODE_EXISTS: (
        'Организация с указанным регистрационным кодом уже существует'
    ),
    CoreErrorCode.ORGANIZATION_IN_USE: (
        'Невозможно удалить организацию, так как она используется '
        'в площадках, подключениях к сети, договорах, этапах, '
        'разрешениях или проблемах'
    ),
}


def get_core_message(code: str) -> str:
    return CORE_MESSAGES.get(code, code)
