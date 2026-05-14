from pathlib import Path

import yaml  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "games" / "astro_knights" / "data"


def _load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def test_astro_knights_box_to_wave_references_are_consistent_across_files():
    waves = _load_yaml(DATA_DIR / "astro_knights_waves.yaml")
    boxes_to_waves = waves["boxes"]

    knights = _load_yaml(DATA_DIR / "astro_knights_knights.yaml")
    for knight in knights["knights"]:
        for variant in knight["variants"]:
            assert variant["box"] in boxes_to_waves
            assert variant["wave_name"] == boxes_to_waves[variant["box"]]

    bosses = _load_yaml(DATA_DIR / "astro_knights_bosses.yaml")
    for boss in bosses["bosses"]:
        assert boss["box"] in boxes_to_waves
        assert boss["wave_name"] == boxes_to_waves[boss["box"]]

    homeworlds = _load_yaml(DATA_DIR / "astro_knights_homeworlds.yaml")
    for homeworld in homeworlds["homeworlds"]:
        assert homeworld["box"] in boxes_to_waves
        assert homeworld["wave_name"] == boxes_to_waves[homeworld["box"]]


def test_astro_knights_boss_battle_difficulties_have_valid_keys_and_values():
    bosses = _load_yaml(DATA_DIR / "astro_knights_bosses.yaml")

    allowed_battles = {"1", "2", "3", "4", 1, 2, 3, 4}
    allowed_difficulties = {"normal", "expert"}

    for boss in bosses["bosses"]:
        difficulties = boss["battle_difficulties"]
        assert difficulties, f"Boss has no battle_difficulties: {boss['name']}"

        for battle, difficulty in difficulties.items():
            assert battle in allowed_battles, f"Unexpected battle key for {boss['name']}: {battle}"
            assert difficulty in allowed_difficulties, f"Unexpected difficulty value for {boss['name']}: {difficulty}"


def test_astro_knights_entity_ids_and_names_are_unique_within_each_data_file():
    knights = _load_yaml(DATA_DIR / "astro_knights_knights.yaml")["knights"]
    bosses = _load_yaml(DATA_DIR / "astro_knights_bosses.yaml")["bosses"]
    homeworlds = _load_yaml(DATA_DIR / "astro_knights_homeworlds.yaml")["homeworlds"]

    def assert_unique(items, key, label):
        values = [item[key] for item in items]
        assert len(values) == len(set(values)), f"Duplicate {label} values detected for key '{key}'"

    assert_unique(knights, "id", "knights")
    assert_unique(knights, "name", "knights")
    assert_unique(bosses, "id", "bosses")
    assert_unique(bosses, "name", "bosses")
    assert_unique(homeworlds, "id", "homeworlds")
    assert_unique(homeworlds, "name", "homeworlds")


def test_astro_knights_waves_and_wave_settings_cover_same_wave_names():
    waves = _load_yaml(DATA_DIR / "astro_knights_waves.yaml")
    settings = _load_yaml(DATA_DIR / "wave_settings.yaml")

    wave_names_from_boxes = set(waves["boxes"].values())
    wave_names_from_settings = set(settings["wave_settings"].keys())

    assert wave_names_from_boxes == wave_names_from_settings
