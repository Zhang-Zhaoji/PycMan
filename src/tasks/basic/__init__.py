"""Load each S1-S5 student module only when its interface is needed."""

from importlib import import_module

_FUNCTION_STAGE = {
    'can_walk': 's1', 'move': 's1',
    'advance_power': 's2', 'collect_item': 's2',
    'resolve_collisions': 's3', 'check_result': 's3',
    'legal_directions': 's4', 'random_direction': 's4',
    'handle_key': 's5', 'continuous_direction': 's5',
}

__all__ = list(_FUNCTION_STAGE)


def __getattr__(name: str):
    stage = _FUNCTION_STAGE.get(name)
    if stage is None:
        raise AttributeError(name)
    return getattr(import_module(f'{__name__}.{stage}'), name)
