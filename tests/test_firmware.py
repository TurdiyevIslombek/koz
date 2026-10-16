"""The Arduino sketches (CLAUDE.md rule 11): motor_listener's safety rules run on the Mac with clang++,
and both sketches compile for the Arduino Uno with arduino-cli (tools/bin, git-ignored). No board needed."""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIRMWARE = ROOT / "firmware"
ARDUINO_CLI = ROOT / "tools" / "bin" / "arduino-cli"


@pytest.mark.skipif(shutil.which("clang++") is None, reason="needs clang++")
def test_motor_safety_rules_pass_on_the_mac(tmp_path):
    binary = tmp_path / "test_motor_logic"
    built = subprocess.run(["clang++", "-std=c++17", "-Wall", "-Wextra", "-Werror", "-o", str(binary),
                            str(FIRMWARE / "tests" / "test_motor_logic.cpp")], capture_output=True, text=True)
    assert built.returncode == 0, built.stderr
    ran = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
    assert ran.returncode == 0 and "checks passed" in ran.stdout, ran.stdout


@pytest.mark.skipif(not ARDUINO_CLI.exists(), reason="needs tools/bin/arduino-cli")
@pytest.mark.parametrize("sketch", ["motor_listener", "stop_test"])
def test_sketch_compiles_for_the_uno(sketch, tmp_path):
    built = subprocess.run([str(ARDUINO_CLI), "compile", "--fqbn", "arduino:avr:uno", "--build-path", str(tmp_path),
                            str(FIRMWARE / sketch)], capture_output=True, text=True, timeout=300)
    assert built.returncode == 0, built.stdout + built.stderr


def test_motor_listener_keeps_the_rule_11_numbers():
    sketch = (FIRMWARE / "motor_listener" / "motor_listener.ino").read_text()
    assert "/* watchdog_ms */ 250," in sketch          # rule 11: 250 ms
    assert "setSide(ENA, IN1, IN2, 0);             // starts stopped" in sketch
    assert "DISARMED" in (FIRMWARE / "motor_listener" / "motor_logic.h").read_text()
