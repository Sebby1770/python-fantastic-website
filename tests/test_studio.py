from pytest import approx, raises

from studio import (
    INK,
    TYPE_RATIOS,
    best_on_ink,
    contrast_ratio,
    css_variables,
    palette_from_seed,
    pairing_table,
    passes_aa,
    passes_aaa,
    recommend_body,
    scss_map,
    type_scale,
)


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


def test_passes_aaa_thresholds():
    assert passes_aaa("#ffffff", "#000000") is True
    assert passes_aaa("#ffffff", "#000000", large=True) is True
    assert passes_aaa("#888888", "#ffffff") is False
    assert passes_aaa("#888888", "#ffffff", large=True) is False
    assert passes_aaa("#595959", "#ffffff") is True
    assert passes_aaa("#777777", "#ffffff", large=True) is False
    assert passes_aaa("#767676", "#ffffff", large=True) is True
    assert passes_aaa("#767676", "#ffffff") is False


def test_css_variables_snapshot():
    css = css_variables(palette_from_seed("asteria"))
    assert css.splitlines()[0] == (
        ":root { --studio-1: #66381f; --studio-2: #a76538; "
        "--studio-3: #a9be5c; --studio-4: #83d1db; --studio-5: #a4b0d9; "
        "--studio-ink: #101418; }"
    )


def test_scss_map_snapshot():
    assert scss_map(palette_from_seed("asteria")) == (
        '$studio: ("1": #66381f, "2": #a76538, "3": #a9be5c, '
        '"4": #83d1db, "5": #a4b0d9, "ink": #101418);'
    )


def test_best_on_ink_asteria():
    palette = palette_from_seed("asteria")
    best = best_on_ink(palette)
    assert best["hex"] == "#83d1db"
    assert best["ratio"] == approx(contrast_ratio("#83d1db", INK))
    assert best["aa"] is True
    assert best["aaa"] is True
    assert set(best) == {"hex", "ratio", "aa", "aaa"}


def test_best_on_ink_tie_keeps_first():
    tied = ["#c8c8c8", "#c8c8c8"]
    best = best_on_ink(tied)
    assert best["hex"] == "#c8c8c8"
    lighter = best_on_ink(["#444444", "#f2f2f2", "#e8e8e8"])
    assert lighter["hex"] == "#f2f2f2"


def test_recommend_body_asteria_has_no_aa_pair():
    assert recommend_body(palette_from_seed("asteria")) is None


def test_recommend_body_first_consecutive_aa_pair():
    palette = ["#111111", "#222222", "#f7f7f7", "#eeeeee"]
    recommended = recommend_body(palette)
    assert recommended is not None
    assert recommended["fg"] == "#222222"
    assert recommended["bg"] == "#f7f7f7"
    assert recommended["aa"] is True
    assert recommended["aaa"] is passes_aaa("#222222", "#f7f7f7")
    assert recommended["ratio"] == approx(contrast_ratio("#222222", "#f7f7f7"))


def test_pairing_table_ink_and_neighbors():
    palette = palette_from_seed("asteria")
    rows = pairing_table(palette)
    assert len(rows) == 9
    for row in rows:
        assert set(row) == {"fg", "bg", "ratio", "aa", "aaa"}
        assert row["ratio"] == approx(contrast_ratio(row["fg"], row["bg"]))
        assert row["aa"] is passes_aa(row["fg"], row["bg"])
        assert row["aaa"] is passes_aaa(row["fg"], row["bg"])
    for index, color in enumerate(palette):
        assert rows[index]["fg"] == color
        assert rows[index]["bg"] == INK
    for index in range(len(palette) - 1):
        neighbor = rows[len(palette) + index]
        assert neighbor["fg"] == palette[index]
        assert neighbor["bg"] == palette[index + 1]


def test_type_ratios():
    assert TYPE_RATIOS == {
        "minor-third": 1.2,
        "major-third": 1.25,
        "perfect-fourth": 1.333,
        "perfect-fifth": 1.5,
    }


def test_type_scale_major_third():
    assert type_scale() == [16.0, 20.0, 25.0, 31.25, 39.06, 48.83]
    assert type_scale(base_px=18, ratio=1.2, steps=3) == [18.0, 21.6, 25.92]


def test_type_scale_rejects_empty():
    with raises(ValueError):
        type_scale(steps=0)
