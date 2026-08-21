from pytest import approx, raises

from studio import contrast_ratio, palette_from_seed, passes_aa, type_scale


def test_palette_from_seed_is_deterministic_and_hex():
    first = palette_from_seed("asteria")
    second = palette_from_seed("asteria")
    other = palette_from_seed("northline")

    assert first == second
    assert first != other
    assert len(first) == 5
    for color in first:
        assert color.startswith("#")
        assert len(color) == 7
        int(color[1:], 16)


def test_palette_from_seed_snapshot():
    assert palette_from_seed("asteria") == [
        "#66381f",
        "#a76538",
        "#a9be5c",
        "#83d1db",
        "#a4b0d9",
    ]


def test_contrast_ratio_wcag_extremes():
    assert contrast_ratio("#ffffff", "#000000") == approx(21.0)
    assert contrast_ratio("#000", "#fff") == approx(21.0)
    assert contrast_ratio("#101418", "#101418") == approx(1.0)


def test_contrast_ratio_rejects_invalid_hex():
    with raises(ValueError):
        contrast_ratio("blue", "#000000")


def test_passes_aa_thresholds():
    assert passes_aa("#ffffff", "#000000") is True
    assert passes_aa("#888888", "#ffffff") is False
    assert passes_aa("#888888", "#ffffff", large=True) is True
    assert passes_aa("#999999", "#ffffff", large=True) is False


def test_type_scale_major_third():
    assert type_scale() == [16.0, 20.0, 25.0, 31.25, 39.06, 48.83]
    assert type_scale(base_px=18, ratio=1.2, steps=3) == [18.0, 21.6, 25.92]


def test_type_scale_rejects_empty():
    with raises(ValueError):
        type_scale(steps=0)
