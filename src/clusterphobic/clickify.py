'''
Module docstring
'''
from typing import Union, Annotated
from typing import get_args, get_origin
from functools import wraps
from uuid import uuid4
from pydantic import BaseModel
from pydantic_core._pydantic_core import PydanticUndefined
import click


MODEL_SEP = f'_{uuid4().hex}_'


class HiddenTypeOption(click.Option):
    '''
    Extends click.Option. Overrides the 'get_help_record' method to modify the
    help message and remove the type hints.
    '''
    def get_help_record(self, ctx):
        ''' Overrides click.Option to remove type hint from help message '''
        help_record = list(super().get_help_record(ctx))
        help_record[0] = help_record[0].split(' ')[0].strip()
        return tuple(help_record)


def _get_field_default(field_info):
    ''' Helper to get default field's value in clickify decorator'''
    if field_info.default_factory is not None:
        default = field_info.default_factory()
    elif field_info.default is not PydanticUndefined:
        default = field_info.default
    else:
        default = None
    return default


def issubclass_field(field, cls):
    ''' 
    Modified issubclass function with support for special typing classes
    (e.g., typing.Optional, typing.Annotated, etc.)
    '''
    field_type = field.annotation
    while get_origin(field_type) in [Union, Annotated]:
        field_type = get_args(field_type)[0]
    return issubclass(field_type, cls)


def _add_options_from_model_fields(
    func,
    model: BaseModel,
    prefix: str = MODEL_SEP,
):
    '''
    Recursively add click options to function 'func' for each field of a 
    Pydantic model 'model' which may include fields that are, themselves, 
    Pydantic models.
    '''
    for field_name, field_info in model.model_fields.items():
        if issubclass_field(field_info, BaseModel):
            func = _add_options_from_model_fields(
                func,
                field_info.annotation,
                prefix=prefix+field_name+MODEL_SEP
            )
        else:
            func = click.option(
                f"--{field_name.replace('_', '-')}",  # option name
                prefix+field_name,  # non-option name
                default=_get_field_default(field_info),
                required=field_info.is_required(),
                help=field_info.description,
                cls=HiddenTypeOption,
            )(func)
    return func


def _reassign_model_fields(
    func,
    model: BaseModel,
):
    '''
    Recurse through the fields of 'model' and generate valid instances of
    'model' and Pydantic models contained in its fields. Add as single kwarg
    to the decorated function.
    '''
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Subset kwargs to fields used to construct Pydantic model(s)
        model_kwargs = {
            key: kwargs[key] for key in filter(
                lambda k: k.startswith(MODEL_SEP),
                kwargs.keys()
            )
        }
        # Reconstruct dictionary from serialized command line inputs
        result_dict = {}
        for key, val in model_kwargs.items():
            kwargs.pop(key)
            keys = key.split(MODEL_SEP)[1:]
            current_dict = result_dict
            for k in keys[:-1]:
                if k not in current_dict:
                    current_dict[k] = {}
                current_dict = current_dict[k]
            current_dict[keys[-1]] = val
        # Instantiate Pydantic model(s) and add to kwargs
        model_obj = model(**result_dict)
        kwargs[model.__name__] = model_obj
        return func(*args, **kwargs)
    return wrapper


def clickify(
    model: BaseModel,
):
    '''
    Function decorator to convert Pydantic model to click command using the
    following logic:
    1) Models
        a) The Pydantic Model 'model' and all associated models (e.g., a field
        of type model, a field of a field of type model, etc.) are included in
        the final click command.  
    2) Fields
        a) All Fields of the Pydantic Model become click options.
        b) Click options are of type str without type hints. The decorator
        relies on Pydantic to coerce inputs to a valid field type.
        c) Fields of type 'enum' provide possible values as examples.
    TODO: Extend 'model' so that all fields have a) default of 'None' if not
    already provided, and b) Optional type if not required
    TODO: Fully support enums (2c)
    '''
    def decorator(func):
        func = _add_options_from_model_fields(func, model)
        func = _reassign_model_fields(func, model)
        return func
    return decorator
