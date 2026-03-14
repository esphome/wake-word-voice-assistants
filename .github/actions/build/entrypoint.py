#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ESP32_CHIP_FAMILIES = {
    "ESP32": "ESP32",
    "ESP32S2": "ESP32-S2",
    "ESP32S3": "ESP32-S3",
    "ESP32C3": "ESP32-C3",
    "ESP32C6": "ESP32-C6",
}


def parse_args(argv):
    """Parse the arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("configuration", help="Path to the configuration file")
    parser.add_argument("--release-summary", help="Release summary", nargs="?")
    parser.add_argument("--release-url", help="Release URL", nargs="?")

    complete_parser = parser.add_mutually_exclusive_group()
    complete_parser.add_argument(
        "--complete-manifest",
        help="Write complete esp-web-tools manifest.json",
        action="store_true",
        dest="complete_manifest",
    )
    complete_parser.add_argument(
        "--partial-manifest",
        help="Write partial esp-web-tools manifest.json",
        action="store_false",
        dest="complete_manifest",
    )
    parser.set_defaults(complete_manifest=False)

    parser.add_argument("--outputs-file", help="GitHub Outputs file", nargs="?")

    return parser.parse_args(argv[1:])


def compile_firmware(filename: Path) -> int:
    """Compile the firmware."""
    print("::group::Compile firmware")
    rc = subprocess.run(
        ["esphome", "compile", filename],
        stdout=sys.stdout,
        stderr=sys.stderr,
        check=False,
    )
    print("::endgroup::")
    return rc.returncode


def get_esphome_version(outputs_file: str | None) -> tuple[str, int]:
    """Get the ESPHome version."""
    print("::group::Get ESPHome version")
    try:
        version = subprocess.check_output(["esphome", "version"])
    except subprocess.CalledProcessError as e:
        print("::endgroup::")
        return "", e.returncode

    version = version.decode("utf-8").strip()
    print(version)
    version = version.split(" ")[1].strip()
    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"esphome-version={version}", file=output)
    print("::endgroup::")
    return version, 0


@dataclass
class Config:
    """Configuration data."""

    name: str
    platform: str
    original_name: str
    friendly_name: str | None = None

    project_name: str | None = None
    project_version: str | None = None

    raw_config: dict | None = None

    def dest_factory_bin(self, file_base: Path) -> Path:
        """Get the destination factory binary path."""
        if self.platform == "rp2040":
            return file_base / f"{self.name}.uf2"
        return file_base / f"{self.name}.factory.bin"

    def dest_ota_bin(self, file_base: Path) -> Path:
        """Get the destination OTA binary path."""
        return file_base / f"{self.name}.ota.bin"

    def dest_elf(self, file_base: Path) -> Path:
        """Get the destination ELF path."""
        return file_base / f"{self.name}.elf"

    def source_factory_bin(self, elf: Path) -> Path:
        """Get the source factory binary path."""
        if self.platform == "rp2040":
            return elf.with_name("firmware.uf2")
        return elf.with_name("firmware.factory.bin")

    def source_ota_bin(self, elf: Path) -> Path:
        """Get the source OTA binary path."""
        return elf.with_name("firmware.ota.bin")


def get_config(filename: Path, outputs_file: str | None) -> tuple[Config | None, int]:
    """Get the configuration."""
    print("::group::Get config")
    try:
        config = subprocess.check_output(
            ["esphome", "config", filename], stderr=sys.stderr
        )
    except subprocess.CalledProcessError as e:
        return None, e.returncode

    config = config.decode("utf-8")
    print(config)

    yaml.add_multi_constructor("", lambda _, t, n: t + " " + n.value)
    config = yaml.load(config, Loader=yaml.FullLoader)

    original_name = config["esphome"]["name"]
    friendly_name = config["esphome"].get("friendly_name")

    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"original-name={original_name}", file=output)

    platform = ""
    if "esp32" in config:
        platform = config["esp32"]["variant"].lower()
    elif "esp8266" in config:
        platform = "esp8266"
    elif "rp2040" in config:
        platform = "rp2040"

    name = f"{original_name}-{platform}"

    if outputs_file:
        with open(outputs_file, "a", encoding="utf-8") as output:
            print(f"name={name}", file=output)

    if project_config := config["esphome"].get("project"):
        project_name = project_config["name"]
        project_version = project_config["version"]
        if outputs_file:
            with open(outputs_file, "a", encoding="utf-8") as output:
                print(f"project-name={project_name}", file=output)
                print(f"project-version={project_version}", file=output)
    else:
        project_name = None
        project_version = None
    print("::endgroup::")
    return Config(
        name=name,
        platform=platform,
        original_name=original_name,
        raw_config=config,
        friendly_name=friendly_name,
        project_name=project_name,
        project_version=project_version,
    ), 0


def get_idedata(filename: Path) -> tuple[dict | None, int]:
    """Get the IDEData."""
    print("::group::Get IDEData")
    try:
        idedata = subprocess.check_output(
            ["esphome", "idedata", filename], stderr=sys.stderr
        )
    except subprocess.CalledProcessError as e:
        return None, e.returncode

    data = json.loads(idedata.decode("utf-8"))
    print(json.dumps(data, indent=2))
    print("::endgroup::")
    return data, 0


def generate_manifest_part(
    idedata: dict,
    factory_bin: Path,
    ota_bin: Path,
    release_summary: str | None,
    release_url: str | None,
) -> tuple[dict | None, int]:
    """Generate the manifest."""

    chip_family = None
    define: str
    has_factory_part = False
    for define in idedata["defines"]:
        if define == "USE_ESP8266":
            chip_family = "ESP8266"
            has_factory_part = True
            break
        if define == "USE_RP2040":
            chip_family = "RP2040"
            break
        if m := re.match(r"USE_ESP32_VARIANT_(\w+)", define):
            chip_family = m.group(1)
            if chip_family not in ESP32_CHIP_FAMILIES:
                print(f"ERROR: Unsupported chip family: {chip_family}")
                return None, 1

            chip_family = ESP32_CHIP_FAMILIES[chip_family]
            has_factory_part = True
            break

    with open(ota_bin, "rb") as f:
        ota_md5 = hashlib.md5(f.read()).hexdigest()
        f.seek(0)
        ota_sha256 = hashlib.sha256(f.read()).hexdigest()

    manifest = {
        "chipFamily": chip_family,
        "ota": {
            "path": ota_bin.name,
            "md5": ota_md5,
            "sha256": ota_sha256,
        },
    }

    if release_summary:
        manifest["ota"]["summary"] = release_summary
    if release_url:
        manifest["ota"]["release_url"] = release_url

    if has_factory_part:
        with open(factory_bin, "rb") as f:
            factory_md5 = hashlib.md5(f.read()).hexdigest()
            f.seek(0)
            factory_sha256 = hashlib.sha256(f.read()).hexdigest()
        manifest["parts"] = [
            {
                "path": str(factory_bin.name),
                "offset": 0x00,
                "md5": factory_md5,
                "sha256": factory_sha256,
            }
        ]

    return manifest, 0


def main(argv) -> int:
    """Main entrypoint."""
    args = parse_args(argv)

    filename = Path(args.configuration)

    if (rc := compile_firmware(filename)) != 0:
        return rc

    esphome_version, rc = get_esphome_version(args.outputs_file)
    if rc != 0:
        return rc

    config, rc = get_config(filename, args.outputs_file)
    if rc != 0:
        return rc

    assert config is not None

    file_base = Path(config.name)

    idedata, rc = get_idedata(filename)
    if rc != 0:
        return rc

    print("::group::Copy firmware file(s) to folder")

    elf = Path(idedata["prog_path"])

    source_factory_bin = config.source_factory_bin(elf)
    dest_factory_bin = config.dest_factory_bin(file_base)

    source_ota_bin = config.source_ota_bin(elf)
    dest_ota_bin = config.dest_ota_bin(file_base)

    dest_elf = config.dest_elf(file_base)

    file_base.mkdir(parents=True, exist_ok=True)

    shutil.copyfile(source_factory_bin, dest_factory_bin)
    print("Copied factory binary to:", dest_factory_bin)
    shutil.copyfile(source_ota_bin, dest_ota_bin)
    print("Copied OTA binary to:", dest_ota_bin)
    shutil.copyfile(elf, dest_elf)
    print("Copied ELF file to:", dest_elf)

    print("::endgroup::")

    print("::group::Generate manifest")
    manifest, rc = generate_manifest_part(
        idedata,
        dest_factory_bin,
        dest_ota_bin,
        args.release_summary,
        args.release_url,
    )
    if rc != 0:
        return rc

    if args.complete_manifest:
        manifest = {
            "name": config.project_name or config.friendly_name or config.original_name,
            "version": config.project_version or esphome_version,
            "home_assistant_domain": "esphome",
            "new_install_prompt_erase": False,
            "builds": [
                manifest,
            ],
        }

    print("Writing manifest file:")
    print(json.dumps(manifest, indent=2))

    with open(file_base / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("::endgroup::")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
