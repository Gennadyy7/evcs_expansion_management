"""User-facing Russian API messages for reference dictionaries."""

from app.features.reference.constants import ReferenceErrorCode

REFERENCE_MESSAGES: dict[str, str] = {
    ReferenceErrorCode.REGION_NOT_FOUND: 'Регион не найден',
    ReferenceErrorCode.REGION_CODE_ALREADY_EXISTS: (
        'Регион с указанным кодом уже существует'
    ),
    ReferenceErrorCode.REGION_PARENT_NOT_FOUND: 'Родительский регион не найден',
    ReferenceErrorCode.REGION_SELF_PARENT: (
        'Регион не может быть родительским по отношению к самому себе'
    ),
    ReferenceErrorCode.REGION_CYCLE_DETECTED: (
        'Обнаружена циклическая зависимость в иерархии регионов'
    ),
    ReferenceErrorCode.REGION_HAS_CHILDREN: (
        'Невозможно удалить регион, так как у него есть дочерние регионы'
    ),
    ReferenceErrorCode.REGION_IN_USE: (
        'Невозможно удалить регион, так как он используется в площадках или планах развития'
    ),
    ReferenceErrorCode.CHARGER_TYPE_NOT_FOUND: ('Тип зарядного оборудования не найден'),
    ReferenceErrorCode.CHARGER_TYPE_CODE_ALREADY_EXISTS: (
        'Тип зарядного оборудования с указанным кодом уже существует'
    ),
    ReferenceErrorCode.CHARGER_TYPE_IN_USE: (
        'Невозможно удалить тип зарядного оборудования, '
        'так как он используется в станциях, планах развития или проектах'
    ),
    ReferenceErrorCode.CONNECTOR_TYPE_NOT_FOUND: ('Тип разъёма не найден'),
    ReferenceErrorCode.CONNECTOR_TYPE_CODE_ALREADY_EXISTS: (
        'Тип разъёма с указанным кодом уже существует'
    ),
    ReferenceErrorCode.CONNECTOR_TYPE_IN_USE: (
        'Невозможно удалить тип разъёма, '
        'так как он используется в разъёмах зарядного оборудования'
    ),
}


def get_reference_message(code: str) -> str:
    return REFERENCE_MESSAGES.get(code, code)
