#pragma once
#include "driver/gpio.h"

// AI-Thinker white illuminator: active HIGH on GPIO4. This sketch never uses it.
// Prepare the LOW output before releasing any hold left by a previous reset,
// then latch it LOW so later peripheral configuration cannot turn it on.
inline void disableFlashLight() {
  ESP_ERROR_CHECK(gpio_set_level(GPIO_NUM_4, 0));
  ESP_ERROR_CHECK(gpio_set_direction(GPIO_NUM_4, GPIO_MODE_OUTPUT));
  ESP_ERROR_CHECK(gpio_hold_dis(GPIO_NUM_4));
  ESP_ERROR_CHECK(gpio_hold_en(GPIO_NUM_4));
}
