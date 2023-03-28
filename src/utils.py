import time
import requests
import traceback

def retry_net(func, retry_amount=1, sleep_amount=2, valid_status_codes=[200], **kwargs):
    for x in range(retry_amount):
        try:
            r = func(**kwargs)

            if len(valid_status_codes) > 0:
                if r.status_code not in valid_status_codes:
                    print(r.status_code)
                    print(r.text)
                    raise Exception('Request in retry_net failed!')

            return r

        except requests.exceptions.ConnectionError as e:
            print("ERROR: The connection has been reset.")
            time.sleep(sleep_amount)
            sleep_amount *= 2

        except Exception as e:
            print(kwargs)
            print(traceback.print_exc())
            time.sleep(sleep_amount)
            sleep_amount *= 2

    raise Exception


def sanitize(filename):
    """Return a fairly safe version of the filename.

    We don't limit ourselves to ascii, because we want to keep municipality
    names, etc, but we do want to get rid of anything potentially harmful,
    and make sure we do not exceed Windows filename length limits.
    Hence a less safe blacklist, rather than a whitelist.
    """
    blacklist = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|", "\0"]
    reserved = [
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", "COM5",
        "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5",
        "LPT6", "LPT7", "LPT8", "LPT9",
    ]  # Reserved words on Windows
    filename = "".join(c for c in filename if c not in blacklist)
    # Remove all charcters below code point 32
    filename = "".join(c for c in filename if 31 < ord(c))
    # filename = unicodedata.normalize("NFKD", filename) # TODO: Removing this since it breaks CJK lettering
    filename = filename.rstrip(". ")  # Windows does not allow these at end
    filename = filename.strip()

    if all([x == "." for x in filename]):
        filename = "__" + filename

    if filename in reserved:
        filename = "__" + filename

    if len(filename) == 0:
        filename = "__"

    if len(filename) > 255:
        parts = re.split(r"/|\\", filename)[-1].split(".")
        if len(parts) > 1:
            ext = "." + parts.pop()
            filename = filename[:-len(ext)]
        else:
            ext = ""
        if filename == "":
            filename = "__"
        if len(ext) > 254:
            ext = ext[254:]
        maxl = 255 - len(ext)
        filename = filename[:maxl]
        filename = filename + ext
        # Re-check last character (if there was no extension)
        filename = filename.rstrip(". ")
        if len(filename) == 0:
            filename = "__"

    filename = filename.replace("\\", "")

    return filename
