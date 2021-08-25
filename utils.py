from PIL import Image, ImageFile
from PIL.ExifTags import TAGS, GPSTAGS

ImageFile.LOAD_TRUNCATED_IMAGES = True


def get_exif(image: Image.isImageType):
    props = {}
    i = Image.open(image)
    info = i._getexif()
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        props[decoded] = value

    return props


def extract_coordinates(image: Image.isImageType) -> list:
    exif_value = get_exif(image)
    lat_ref = exif_value['GPSInfo'][1]
    longit_ref = exif_value['GPSInfo'][3]
    lat = exif_value['GPSInfo'][2]
    longit = exif_value['GPSInfo'][4]

    # geocoding
    gps_data = {
        'GPSLatitude': exif_value['GPSInfo'][2],
        'GPSLongitude': exif_value['GPSInfo'][4],
        'GPSLatitudeRef': exif_value['GPSInfo'][1],
        'GPSLongitudeRef': exif_value['GPSInfo'][3],
    }

    if "GPSLatitude" in gps_data:
        lat = gps_data["GPSLatitude"]
        lat = decimal_coordinates_to_degress(lat)
    if "GPSLongitude" in gps_data:
        longit = gps_data["GPSLongitude"]
        longit = decimal_coordinates_to_degress(longit)
    if "GPSLatitudeRef" in gps_data:
        lat_ref = gps_data["GPSLatitudeRef"]
    if "GPSLongitudeRef" in gps_data:
        longit_ref = gps_data["GPSLongitudeRef"]

    if lat_ref is not None and lat_ref != "N":
        lat = 0 - lat
    if longit_ref is not None and longit_ref != "E":
        longit = 0 - longit

    return [lat, longit]


def decimal_coordinates_to_degress(coord):
    dec = float(coord[0][0]) / float(coord[0][1])
    minut = float(coord[1][0]) / float(coord[1][1])
    sec = float(coord[2][0]) / float(coord[2][1])
    return dec + (minut / 60.0) + (sec / 3600.0)


def show_exif(image):
    # Return exif as str to show
    exif = get_exif(image)
    try:
        exif_to_print = (
                "Модель: " + exif["Make"] + " " + exif["Model"]
                + "\nСофт: " + str(exif["Software"])
                + "\nISO: " + str(int(exif["ISOSpeedRatings"]))
                + "\nВыдержка: " + str(exif['ExposureTime']._val)
                + "\nДиафрагма: " + "f/" + str(exif["FNumber"])
                + "\nФокусное расстояние: " + str(exif["FocalLength"]) + " mm"
        )
    except:
        exif_to_print = (
                "Модель: " + exif["Make"] + " " + exif["Model"]
                + "\nISO: " + str(int(exif["ISOSpeedRatings"]))
                + "\nВыдержка: " + str(exif["ExposureTime"])
                + "\nДиафрагма: " + "f/" + str(exif["FNumber"])
                + "\nФокусное расстояние: " + str(exif["FocalLength"]) + " mm"
        )
    return exif_to_print


# Crop

def crop_image(image, n=1, size=None):
    # Crop center of image 100%

    image_object = Image.open(image)
    size = image_object.size
    W = size[0]
    H = size[1]
    left = int(W / 4)
    upper = int(H / 4)
    right = int(W / 2) + left
    lower = int(H / 2) + upper
    cropped = image_object.crop((left, upper, right, lower))
    file_name_x1 = f"{image}_cropx{n * 2}.jpeg"
    cropped.save(fp=file_name_x1)

    # Добавляем условие если нужно х4 сделать

    if n != 1:
        image_object = Image.open(file_name_x1)
        size = image_object.size
        W = size[0]
        H = size[1]
        left = int(W / 4)
        upper = int(H / 4)
        right = int(W / 2) + left
        lower = int(H / 2) + upper
        cropped = image_object.crop((left, upper, right, lower))
        file_name = f"{image}_cropx{n * 2}.jpeg"
        cropped.save(fp=file_name)

    return cropped
