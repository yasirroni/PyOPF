""" IO base
"""
import os
import io
import json
from pathlib import Path
from typing import Any, BinaryIO, Callable, cast, Dict, Optional, Type, Tuple, Union, IO
from typing_extensions import TypeAlias

from opf.io.matpower import parse_matpower, mp2data
from opf.io.common import make_per_unit #, simplify_cost_terms

FILE_LIKE: TypeAlias = Union[str, os.PathLike]

def parse_file(f:FILE_LIKE) -> None:
    sfx = Path(str(f)).suffix[1:]
    if sfx != 'm':
        raise ValueError("the extension {} in {} is not supported for the input file.".format(sfx,str(f)))

    try:
        with open(f, 'r') as opened_f:
            return _parse_file(opened_f)

    except (io.UnsupportedOperation, AttributeError) as e:
        msg = (str(e) + ". The file {} is not supported for parsing"%str(f))
        raise type(e)(msg)
    

def _parse_file(f):
    lines = f.readlines()
    mp_data = parse_matpower(lines)
    data_dict = mp2data(mp_data)
    
    make_per_unit(data_dict)
    # correct_cost_functions(data)
    # simplify_cost_terms(data_dict)
    data_dict['preprocessed'] = False
    return data_dict


def export_network(obj:Dict[str,Any], f:FILE_LIKE) -> None:
    json.dump(obj, open(f,'w'), indent=2)
    return None

