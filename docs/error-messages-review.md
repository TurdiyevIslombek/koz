# Error messages to check (38)

Made from `contracts/events.md`, section 11 (Oct 14). Read the Russian and Uzbek lines;
tick the box when it reads naturally, or write the better wording under it.
Claude then copies your fixes into `contracts/events.md` (wording only, the codes stay).

## 1. `INVALID_RECIPE` — rule 1
*When:* Bad JSON, unknown fields/blocks, code, URLs, paths, model files, wrong order, out-of-range or too large

- EN: Recipe is invalid.
- RU: Рецепт недопустим.
- UZ: Retsept yaroqsiz.
- [ ] Russian OK   - [ ] Uzbek OK

## 2. `SAFETY_LOCKED` — rule 1
*When:* Removing or weakening a locked protection

- EN: Safety settings are locked.
- RU: Настройки безопасности заблокированы.
- UZ: Xavfsizlik sozlamalari qulflangan.
- [ ] Russian OK   - [ ] Uzbek OK

## 3. `ADJUSTMENT_LIMIT` — rule 1
*When:* Round 3 did not pass

- EN: Three attempts failed. Job is off.
- RU: Три попытки не удались. Задание отключено.
- UZ: Uch urinish muvaffaqiyatsiz. Vazifa o'chirildi.
- [ ] Russian OK   - [ ] Uzbek OK

## 4. `CHECK_FAILED` — rule 1
*When:* Failed check with no allowed fix

- EN: Check failed. Job stopped.
- RU: Проверка не пройдена. Задание остановлено.
- UZ: Tekshiruv o'tmadi. Vazifa to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK

## 5. `PLANNER_UNAVAILABLE` — rule 1
*When:* Planner down or timed out

- EN: Planner is unavailable.
- RU: Планировщик недоступен.
- UZ: Rejalashtiruvchi ishlamayapti.
- [ ] Russian OK   - [ ] Uzbek OK

## 6. `PRIVATE_BATHROOM` — rule 2
*When:* Scene check: bathroom

- EN: Bathroom view blocked.
- RU: Вид ванной заблокирован.
- UZ: Hammom ko'rinishi bloklandi.
- [ ] Russian OK   - [ ] Uzbek OK

## 7. `PRIVATE_TOILET` — rule 2
*When:* Scene check: toilet

- EN: Toilet view blocked.
- RU: Вид туалета заблокирован.
- UZ: Hojatxona ko'rinishi bloklandi.
- [ ] Russian OK   - [ ] Uzbek OK

## 8. `PRIVATE_BEDROOM` — rule 2
*When:* Scene check: bedroom

- EN: Bedroom view blocked.
- RU: Вид спальни заблокирован.
- UZ: Yotoqxona ko'rinishi bloklandi.
- [ ] Russian OK   - [ ] Uzbek OK

## 9. `PRIVATE_CHANGING_ROOM` — rule 2
*When:* Scene check: changing room

- EN: Changing-room view blocked.
- RU: Вид раздевалки заблокирован.
- UZ: Kiyinish xonasi ko'rinishi bloklandi.
- [ ] Russian OK   - [ ] Uzbek OK

## 10. `PRIVACY_UNCERTAIN` — rule 2
*When:* Low confidence or unclear scene

- EN: Scene safety is unknown.
- RU: Безопасность сцены неизвестна.
- UZ: Ko'rinish xavfsizligi noma'lum.
- [ ] Russian OK   - [ ] Uzbek OK

## 11. `PRIVACY_UNAVAILABLE` — rule 2
*When:* Guard model missing, failed or too slow

- EN: Privacy check is unavailable.
- RU: Проверка приватности недоступна.
- UZ: Maxfiylik tekshiruvi ishlamayapti.
- [ ] Russian OK   - [ ] Uzbek OK

## 12. `BLUR_UNAVAILABLE` — rule 2, 6
*When:* Face blur can't run

- EN: Face blur is unavailable.
- RU: Размытие лиц недоступно.
- UZ: Yuzlarni xiralashtirish ishlamayapti.
- [ ] Russian OK   - [ ] Uzbek OK

## 13. `SCENE_CHANGED` — rule 3 (stretch)
*When:* Fixed camera's view changed

- EN: View changed. Outputs stopped.
- RU: Вид изменился. Выходы отключены.
- UZ: Ko'rinish o'zgardi. Chiqishlar to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK

## 14. `LENS_COVERED` — rule 3 (stretch)
*When:* Dark, flat image

- EN: Lens may be covered.
- RU: Возможно, объектив закрыт.
- UZ: Obyektiv yopilgan bo'lishi mumkin.
- [ ] Russian OK   - [ ] Uzbek OK

## 15. `IDENTITY_FORBIDDEN` — rule 4
*When:* Recognition, matching, plates, documents, badges, OCR, following a person

- EN: Identifying people is not allowed.
- RU: Идентификация людей запрещена.
- UZ: Odamlarni tanib olish taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

## 16. `PROFILING_FORBIDDEN` — rule 5
*When:* Traits, judging, per-person timers/scores, police or discipline reports

- EN: Judging or profiling people is not allowed.
- RU: Оценивать и профилировать людей запрещено.
- UZ: Odamlarni baholash va profillash taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

## 17. `SCHOOL_COUNTS_ONLY` — rule 6
*When:* Anything but counts in school mode

- EN: School mode allows counts only.
- RU: В школьном режиме разрешён только подсчёт.
- UZ: Maktab rejimida faqat sanash mumkin.
- [ ] Russian OK   - [ ] Uzbek OK

## 18. `OWNERSHIP_REQUIRED` — rule 7
*When:* "I own this camera" not confirmed

- EN: Confirm on this computer that you own the camera.
- RU: Подтвердите на этом компьютере, что камера ваша.
- UZ: Kamera sizniki ekanini shu kompyuterda tasdiqlang.
- [ ] Russian OK   - [ ] Uzbek OK

## 19. `ALLOWED_AREA_REQUIRED` — rule 7
*When:* Mask missing, invalid or empty

- EN: Draw the allowed area on this computer.
- RU: Отметьте разрешённую область на этом компьютере.
- UZ: Ruxsat etilgan hududni shu kompyuterda belgilang.
- [ ] Russian OK   - [ ] Uzbek OK

## 20. `VIEW_FORBIDDEN` — rule 7
*When:* Hidden camera, neighbour's property, other forbidden view

- EN: This camera use is not allowed.
- RU: Такое использование камеры запрещено.
- UZ: Kameradan bunday foydalanish taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

## 21. `AUDIO_FORBIDDEN` — rule 8
*When:* Microphone or audio request

- EN: Audio is not allowed.
- RU: Аудио запрещено.
- UZ: Audio taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

## 22. `FRAMES_FORBIDDEN` — rule 8, 9
*When:* Saving, screenshotting or sending frames or video

- EN: Saving or sending frames is not allowed.
- RU: Сохранять и передавать кадры запрещено.
- UZ: Kadrlarni saqlash va yuborish taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

## 23. `INVALID_EVENT` — rule 9
*When:* Forbidden or malformed event

- EN: Event data is not allowed.
- RU: Данные события недопустимы.
- UZ: Hodisa ma'lumotlari yaroqsiz.
- [ ] Russian OK   - [ ] Uzbek OK

## 24. `AUTH_REQUIRED` — rule 9
*When:* Missing or bad login or runner token

- EN: Sign in or connect the runner.
- RU: Войдите или подключите исполнитель.
- UZ: Tizimga kiring yoki ijrochini ulang.
- [ ] Russian OK   - [ ] Uzbek OK

## 25. `FRAME_STALE` — rule 10
*When:* Frame missing, frozen or late

- EN: Camera data is stale. Outputs stopped.
- RU: Данные камеры устарели. Выходы отключены.
- UZ: Kamera ma'lumoti eskirgan. Chiqishlar to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK

## 26. `OVERLOADED` — rule 10
*When:* Processing over budget

- EN: Too much processing. Outputs stopped.
- RU: Обработка перегружена. Выходы отключены.
- UZ: Ishlov berish haddan oshdi. Chiqishlar to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK

## 27. `SOLE_PROTECTION_FORBIDDEN` — rule 10
*When:* Ko'z as the only protection for a child, fire, medical or similar

- EN: Ko'z cannot be the only safeguard.
- RU: Ko'z не может быть единственной защитой.
- UZ: Ko'z yagona himoya bo'la olmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

## 28. `MOTOR_TARGET_FORBIDDEN` — rule 11
*When:* Chasing or aiming at people or animals

- EN: Chasing people or animals is not allowed.
- RU: Преследовать людей или животных запрещено.
- UZ: Odam yoki hayvonni quvish taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

## 29. `ACTUATOR_FORBIDDEN` — rule 11
*When:* Locks, gates, shocks, sprays or other unapproved actuators

- EN: This device action is not allowed.
- RU: Это действие устройства запрещено.
- UZ: Qurilmaning bu harakati taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

## 30. `MOTOR_NOT_ARMED` — rule 11
*When:* Motors not armed locally

- EN: Arm the motors on this computer.
- RU: Включите моторы на этом компьютере.
- UZ: Motorlarni shu kompyuterda yoqing.
- [ ] Russian OK   - [ ] Uzbek OK

## 31. `MOTOR_SAFETY_STOP` — rule 11
*When:* Firmware timer, obstacle, switch or motor fault

- EN: Motor safety stop.
- RU: Защитная остановка моторов.
- UZ: Motorlar xavfsizlik uchun to'xtadi.
- [ ] Russian OK   - [ ] Uzbek OK

## 32. `RETENTION_LOCKED` — rule 12
*When:* Asking to keep data longer

- EN: Storage times are fixed.
- RU: Сроки хранения фиксированы.
- UZ: Saqlash muddatlari o'zgarmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

## 33. `UNSUPPORTED_CAPABILITY`
*When:* Block, camera type or OpenCV feature not available

- EN: This feature is not available.
- RU: Эта функция недоступна.
- UZ: Bu imkoniyat mavjud emas.
- [ ] Russian OK   - [ ] Uzbek OK

## 34. `INVALID_COMMAND`
*When:* Unknown command, bad fields or wrong state

- EN: Command is invalid.
- RU: Команда недопустима.
- UZ: Buyruq yaroqsiz.
- [ ] Russian OK   - [ ] Uzbek OK

## 35. `BUSY`
*When:* Another job or trial is active

- EN: Stop the current job first.
- RU: Сначала остановите текущее задание.
- UZ: Avval joriy vazifani to'xtating.
- [ ] Russian OK   - [ ] Uzbek OK

## 36. `COMMAND_EXPIRED`
*When:* Command arrived after its expiry

- EN: Command expired.
- RU: Срок команды истёк.
- UZ: Buyruq muddati tugadi.
- [ ] Russian OK   - [ ] Uzbek OK

## 37. `PROTOCOL_VERSION`
*When:* Unsupported contract version

- EN: Contract version is not supported.
- RU: Версия контракта не поддерживается.
- UZ: Kontrakt versiyasi qo'llab-quvvatlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

## 38. `INTERNAL_ERROR`
*When:* Unexpected failure

- EN: Internal error. Job stopped.
- RU: Внутренняя ошибка. Задание остановлено.
- UZ: Ichki xato. Vazifa to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK
