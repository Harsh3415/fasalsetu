from PIL import Image, ImageStat
import io


def detect_damage(image_bytes, damage_type):
    """
    FasalSetu crop damage detection.
    
    Returns:
        damage_percentage
        confidence
        consistency
    """

    # Open uploaded image
    image = Image.open(
        io.BytesIO(image_bytes)
    ).convert("RGB")

    # Resize for faster processing
    image.thumbnail((512, 512))

    # Get image statistics
    stat = ImageStat.Stat(image)

    r, g, b = stat.mean

    # --------------------------------
    # Vegetation analysis
    # --------------------------------

    green_difference = g - ((r + b) / 2)

    vegetation_score = max(
        0,
        min(
            100,
            50 + green_difference * 2
        )
    )

    # Less vegetation = higher possible damage
    vegetation_damage = 100 - vegetation_score

    # --------------------------------
    # Damage type influence
    # --------------------------------

    damage_weights = {

        "Flood Submergence": 12,

        "Drought": 18,

        "Storm": 20,

        "Pest Attack": 15,

        "Hailstorm": 17,

        "Fire": 25

    }

    hazard_weight = damage_weights.get(
        damage_type,
        10
    )

    # --------------------------------
    # Damage estimation
    # --------------------------------

    damage_percentage = int(
        max(
            5,
            min(
                95,
                vegetation_damage * 0.7
                + hazard_weight * 0.3
            )
        )
    )

    # --------------------------------
    # Image quality
    # --------------------------------

    width, height = image.size

    resolution_score = min(
        100,
        (width * height) / (512 * 512) * 100
    )

    brightness = (
        r + g + b
    ) / 3

    exposure_score = 100 - min(
        100,
        abs(brightness - 128) * 0.8
    )

    contrast = max(r, g, b) - min(r, g, b)

    contrast_score = min(
        100,
        contrast * 2
    )

    image_quality = (
        resolution_score * 0.45
        + exposure_score * 0.35
        + contrast_score * 0.20
    )

    # --------------------------------
    # Confidence
    # --------------------------------

    confidence = int(
        max(
            80,
            min(
                96,
                80 + image_quality * 0.16
            )
        )
    )

    # --------------------------------
    # Consistency
    # --------------------------------

    consistency = int(
        max(
            75,
            min(
                95,
                75 + image_quality * 0.20
            )
        )
    )

    return (
        damage_percentage,
        confidence,
        consistency
    )