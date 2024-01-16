import fontforge  # type: ignore - FontForge's Python instance handles this properly
import psMat  # type: ignore - FontForge's Python instance handles this properly
import os
from sys import argv
import yaml

basePath = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + "/../")
fontsPath = os.path.join(basePath, "fonts")
useDebug = False

pathTypes = ["regular", "italic", "mono", "target"]


def debug(anything):
    if useDebug:
        print(anything)


def loadSettingsYaml():
    if len(argv) > 1:
        if os.path.exists(argv[1]):
            filePath = argv[1]
        elif os.path.exists(os.path.join(basePath, argv[1])):
            filePath = os.path.join(basePath, argv[1])
        else:
            print("Settings file not found: " + argv[1])
            exit()
    else:
        filePath = os.path.join(basePath, "settings-roboto.yaml")

    with open(filePath, "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def select_symbols(instance, settings: dict, action: str = "none"):
    ranges = tuple()
    for symbolRange in settings["symbolRanges"]:
        ranges += (("ranges", None), symbolRange[0], symbolRange[1])

    # Have FontForge select the symbols
    instance.selection.select(*ranges)

    if action == "copy":
        instance.copy()
    elif action == "paste":
        instance.paste()

    return instance


def select_all(instance):
    instance.selection.all()
    return instance


def transform_size(instance, size: float):
    # transform_matrix = (100, 100, size, size, 100, 100)
    transform_matrix = psMat.scale(size)
    debug("transform_matrix = ")
    debug(transform_matrix)
    instance.transform(
        transform_matrix,
    )

    return instance


def create_fonts(font_type: str, settings: dict):
    for weight in settings["weights"]:
        create_font(font_type, weight, settings=settings)


def get_copyright(settings: dict):
    # check to see if the version is a string
    if isinstance(settings["copyright"], str):
        return settings["copyright"]
    return " ".join(settings["copyright"])


def adjust_font_names(
    target_font, font_type: str, weight: str, is_italic: bool, settings: dict
):
    # adjust the technical font names
    target_font.familyname = (
        settings["fullName"] + " " + (weight if weight != "Regular" else "")
    )
    target_font.fullname = (
        settings["fullName"] + " " + weight + (" Italic" if is_italic else "")
    )
    target_font.fontname = settings["technicalName"] + "-" + weight
    target_font.weight = weight if weight != "Regular" else "Book"

    if font_type == "italic":
        target_font.fontname += "Italic"
    target_font.version = settings["version"]
    target_font.copyright = get_copyright(settings)

    # convert sfnt tuple to dictionary
    # sfnt tuple format is (language, name, string_value)
    sfnt_obj = {}
    for sfnt in target_font.sfnt_names:
        temp_key = sfnt[1]
        temp_value = sfnt[2]
        sfnt_obj[temp_key] = temp_value

    updated_obj = {
        "Copyright": get_copyright(settings),
        "Version": "Version " + settings["version"],
        "Family": settings["fullName"],
        #
        "Fullname": settings["fullName"]
        + (" " + weight if weight != "Regular" else "")
        + (" Italic" if is_italic else ""),
        #
        "UniqueID": settings["fullName"]
        + (" " + weight if weight != "Regular" else "")
        + (" Italic" if is_italic else ""),
        #
        "PostScriptName": settings["technicalName"]
        + "-"
        + weight
        + ("Italic" if is_italic else ""),
    }

    if weight != "Regular":
        updated_obj["Preferred Family"] = settings["fullName"]
        updated_obj["Preferred Styles"] = weight + (" Italic" if is_italic else "")

    debug("updated_obj = ")
    debug(updated_obj)

    sfnt_obj.update(updated_obj)

    debug("updated sfnt_obj = ")
    debug(sfnt_obj)

    # convert dictionary back to sfnt tuple
    sfnt_list = []
    for key, value in sfnt_obj.items():
        debug(key + " = " + value)
        sfnt_list.append(("English (US)", key, value))
    target_font.sfnt_names = tuple(sfnt_list)

    return target_font


def hydrate_paths(settings: dict):
    for pathType in pathTypes:
        if pathType in settings:
            if "path" in settings[pathType]:
                settings[pathType]["path"] = os.path.join(
                    fontsPath, settings[pathType]["path"]
                )
                os.makedirs(settings[pathType]["path"], exist_ok=True)
            if "exportPath" in settings[pathType]:
                settings[pathType]["exportPath"] = os.path.join(
                    fontsPath, settings[pathType]["exportPath"]
                )
                os.makedirs(settings[pathType]["exportPath"], exist_ok=True)
    return settings


def create_font(font_type: str, weight: str, settings: dict):
    font_info = settings[font_type]
    mono_info = settings["mono"]
    target_info = settings["target"]
    orig_font_name, mono_font_name, target_font_name = "", "", ""
    is_italic = False

    if font_type == "italic":
        if weight == "Regular":
            orig_font_name = font_info["baseName"] + "Italic"
            mono_font_name = mono_info["baseName"] + "Italic"
            target_font_name = target_info["baseName"] + "Italic"
            is_italic = True
        else:
            orig_font_name = font_info["baseName"] + weight + "Italic"
            mono_font_name = mono_info["baseName"] + weight + "Italic"
            target_font_name = target_info["baseName"] + weight + "Italic"
            is_italic = True
    else:
        orig_font_name = font_info["baseName"] + weight
        mono_font_name = mono_info["baseName"] + weight
        target_font_name = target_info["baseName"] + weight

    font_paths = {
        "orig": font_info["path"] + orig_font_name + settings["fontFileType"],
        "mono": mono_info["path"] + mono_font_name + settings["fontFileType"],
        "target": target_info["path"] + target_font_name + settings["saveFileType"],
        "export": target_info["exportPath"]
        + target_font_name
        + settings["fontFileType"],
    }
    debug("font_paths = ")
    debug(font_paths)

    # open fonts
    orig_font = fontforge.open(font_paths["orig"])
    mono_font = fontforge.open(font_paths["mono"])
    target_font = orig_font

    debug("fontname = " + target_font.fontname)
    debug("familyname = " + target_font.familyname)
    debug("copyright = " + target_font.copyright)
    debug("version = " + target_font.version)
    debug("weight = " + target_font.weight)
    debug("sfnt_names = ")
    debug(target_font.sfnt_names)

    # try to transform sizes if italic
    if is_italic:
        select_all(target_font)
        try:
            target_font = transform_size(
                target_font, font_info["resize"]["italic"]["font"]
            )
        except KeyError:
            debug("italic font resize not found - skipping")
            pass

    # copy in mono font symbols
    select_symbols(mono_font, settings, "copy")
    select_symbols(target_font, settings, "paste")

    # transform symbol sizes if available
    if is_italic:
        select_symbols(target_font, settings)
        try:
            transform_size(target_font, font_info["resize"]["italic"]["symbol"])
        except KeyError:
            debug("italic symbol resize not found - skipping")
            pass
    else:
        try:
            transform_size(target_font, font_info["resize"]["regular"]["symbol"])
        except KeyError:
            debug("regular symbol resize not found - skipping")
            pass

    # adjust font names
    target_font = adjust_font_names(
        target_font, font_type, weight, is_italic, settings=settings
    )

    # save and export font
    target_font.save(font_paths["target"])
    target_font.generate(font_paths["export"])


def load_settings():
    with open("settings.yaml", "r") as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)


def main():
    print("Starting script...")

    print("Loading settings from YAML file...")
    settings = loadSettingsYaml()

    if isinstance(settings, dict):
        print("Settings loaded successfully.")

        print("Hydrating paths...")
        settings = hydrate_paths(settings)

        print("Creating non-italic fonts...")
        create_fonts("regular", settings=settings)

        print("Creating italic fonts...")
        create_fonts("italic", settings=settings)
    else:
        print("Settings not loaded successfully.")

    print("Script complete.")
