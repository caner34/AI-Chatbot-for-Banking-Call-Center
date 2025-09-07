

def try_translate(dict_translation: dict, original: str):
    if original.lower() in [str(x).lower() for x in dict_translation.values() if type(x) == str]:
        return original
    return dict_translation[original]
