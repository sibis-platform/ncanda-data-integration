from itertools import chain
import os
from six import string_types


def flatten_path_dict(path_dict, base_prefix="", delimiter=os.sep):
    """
    Convert a directory tree dict into a list of leaf file paths.

    For example:

    paths = {'ohsu':
                {'test': 'simple',
                 'pasat': [
                     'A-31',
                     'B-32',
                     {'example': ['C-20']}
                 ]}}

    flatten_path_dict(paths, base_prefix='/fs/storage/laptops/import')

    # => ['/fs/storage/laptops/import/ohsu/test/simple',
    #     '/fs/storage/laptops/import/ohsu/pasat/A-31',
    #     '/fs/storage/laptops/import/ohsu/pasat/B-32',
    #     '/fs/storage/laptops/import/ohsu/pasat/example/C-20']
    """
    # NOTE: On reflection, this is not well-recursed; working towards a string
    # base case would have been more elegant and possibly more robust.
    output = []
    for key, val in path_dict.items():
        new_prefix = base_prefix + delimiter + key
        if isinstance(val, dict):
            # The value is a subdirectory -> recurse
            output.extend(flatten_path_dict(val, new_prefix, delimiter))
        elif isinstance(val, list):
            # List will contain either strings ready for concatenation...
            output.extend(
                    [new_prefix + delimiter + item
                        for item in val if not isinstance(item, dict)])
            # ...or more dict subdirs to recurse into
            output.extend(  # chain.from_iterable flattens the resulting list
                    chain.from_iterable(
                        [flatten_path_dict(item, new_prefix, delimiter)
                            for item in val if isinstance(item, dict)]))
        elif isinstance(val, string_types):
            output.append(new_prefix + delimiter + val)
    return output

# if __name__ == '__main__':
#     paths = {'ohsu': 
#                 {'test': 'simple', 
#                  'pasat': [
#                      'A-31', 
#                      'B-32', 
#                      {'example': ['C-20']}]}}
#         ['/fs/storage/laptops/import/ohsu/test/simple',
#          '/fs/storage/laptops/import/ohsu/pasat/A-31',
#          '/fs/storage/laptops/import/ohsu/pasat/B-32',
#          '/fs/storage/laptops/import/ohsu/pasat/example/C-20']
#     print(flatten_path_dict(paths, '/fs/storage/laptops/import'))
