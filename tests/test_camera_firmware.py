"""Exercise the camera's flash-off helper against a GPIO hold model; no hardware."""
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("clang++") is None, reason="needs clang++")
def test_flash_stays_off_even_if_later_code_changes_the_output(tmp_path):
    driver = tmp_path / "driver"
    driver.mkdir()
    (driver / "gpio.h").write_text("""
#pragma once
#include <cassert>
constexpr int GPIO_NUM_4 = 4, GPIO_MODE_OUTPUT = 1;
static int desired = 1, actual = 1, mode = 1;
static bool held = true;
#define ESP_ERROR_CHECK(call) assert((call) == 0)
inline int gpio_set_level(int pin, int value) {
  assert(pin == 4);
  desired = value;
  if (!held) actual = desired;
  return 0;
}
inline int gpio_set_direction(int pin, int value) {
  assert(pin == 4);
  mode = value;
  return 0;
}
inline int gpio_hold_dis(int pin) {
  assert(pin == 4 && desired == 0 && mode == GPIO_MODE_OUTPUT);
  held = false; actual = desired;
  return 0;
}
inline int gpio_hold_en(int pin) {
  assert(pin == 4 && actual == 0);
  held = true;
  return 0;
}
""")
    source = tmp_path / "flash.cpp"
    source.write_text("""
#include "flash_off.h"
int main() {
  // Previous firmware/reset left a held HIGH output.
  disableFlashLight();
  assert(held && actual == 0);
  // Later writes cannot light it; repeated setup also returns to held LOW.
  gpio_set_level(GPIO_NUM_4, 1);
  assert(actual == 0);
  disableFlashLight();
  assert(held && actual == 0);
  // Cold start with no hold.
  held = false; actual = desired = 1;
  disableFlashLight();
  assert(held && actual == 0);
}
""")
    camera = Path(__file__).resolve().parents[1] / "firmware" / "camera_stream"
    binary = tmp_path / "flash"
    subprocess.run(["clang++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
                    "-I", str(tmp_path), "-I", str(camera), str(source), "-o", str(binary)],
                   check=True, capture_output=True, text=True)
    subprocess.run([str(binary)], check=True, capture_output=True, timeout=10)
