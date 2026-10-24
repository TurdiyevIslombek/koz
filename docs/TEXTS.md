# Texts to check (Uzbek and Russian)

Every text Ko'z itself shows in Uzbek and Russian: the plan after you type a job, the
refusals, and the fixed stop and error messages. Made by `scripts/make_texts.py` from
`koz/agent/planner.py` and `contracts/events.md`, so this is exactly what Ko'z says.
Tick the box when it reads naturally, or write the better wording under it; Claude then
puts your fixes into the code or the contract (the codes stay) and makes this file again.

The web app's own screens are in `web/src/i18n.js` (Codex's lane), not here.

## 1. Plans

What Ko'z says it will do, in the language of the job. A colour plan with each colour:

### Find a colour

**red**
- EN: I will look for a round red object, like a ball, and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый красный предмет, например мяч, и говорить, где он: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq qizil narsani (masalan, koptokni) qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**orange**
- EN: I will look for a round orange object, like a ball, and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый оранжевый предмет, например мяч, и говорить, где он: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq to'q sariq narsani (masalan, koptokni) qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**yellow**
- EN: I will look for a round yellow object, like a ball, and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый жёлтый предмет, например мяч, и говорить, где он: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq sariq narsani (masalan, koptokni) qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**green**
- EN: I will look for a round green object, like a ball, and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый зелёный предмет, например мяч, и говорить, где он: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq yashil narsani (masalan, koptokni) qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**blue**
- EN: I will look for a round blue object, like a ball, and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый синий предмет, например мяч, и говорить, где он: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq ko'k narsani (masalan, koptokni) qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**purple**
- EN: I will look for a round purple object, like a ball, and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый фиолетовый предмет, например мяч, и говорить, где он: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq binafsha narsani (masalan, koptokni) qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

### Chase a coloured ball (the fly-brain car)

**red**
- EN: I will look for a round red object, like a ball, and the fly brain will drive the car toward it. Arm the motors on this computer first; the car stops by itself close to obstacles. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый красный предмет, например мяч, и мозг мухи поведёт машинку к нему. Сначала включите моторы на этом компьютере; у препятствий машинка остановится сама. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq qizil narsani (masalan, koptokni) qidiraman, pashsha miyasi mashinani unga qarab haydaydi. Avval motorlarni shu kompyuterda yoqing; to'siq oldida mashina o'zi to'xtaydi. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**orange**
- EN: I will look for a round orange object, like a ball, and the fly brain will drive the car toward it. Arm the motors on this computer first; the car stops by itself close to obstacles. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый оранжевый предмет, например мяч, и мозг мухи поведёт машинку к нему. Сначала включите моторы на этом компьютере; у препятствий машинка остановится сама. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq to'q sariq narsani (masalan, koptokni) qidiraman, pashsha miyasi mashinani unga qarab haydaydi. Avval motorlarni shu kompyuterda yoqing; to'siq oldida mashina o'zi to'xtaydi. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**yellow**
- EN: I will look for a round yellow object, like a ball, and the fly brain will drive the car toward it. Arm the motors on this computer first; the car stops by itself close to obstacles. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый жёлтый предмет, например мяч, и мозг мухи поведёт машинку к нему. Сначала включите моторы на этом компьютере; у препятствий машинка остановится сама. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq sariq narsani (masalan, koptokni) qidiraman, pashsha miyasi mashinani unga qarab haydaydi. Avval motorlarni shu kompyuterda yoqing; to'siq oldida mashina o'zi to'xtaydi. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**green**
- EN: I will look for a round green object, like a ball, and the fly brain will drive the car toward it. Arm the motors on this computer first; the car stops by itself close to obstacles. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый зелёный предмет, например мяч, и мозг мухи поведёт машинку к нему. Сначала включите моторы на этом компьютере; у препятствий машинка остановится сама. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq yashil narsani (masalan, koptokni) qidiraman, pashsha miyasi mashinani unga qarab haydaydi. Avval motorlarni shu kompyuterda yoqing; to'siq oldida mashina o'zi to'xtaydi. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**blue**
- EN: I will look for a round blue object, like a ball, and the fly brain will drive the car toward it. Arm the motors on this computer first; the car stops by itself close to obstacles. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый синий предмет, например мяч, и мозг мухи поведёт машинку к нему. Сначала включите моторы на этом компьютере; у препятствий машинка остановится сама. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq ko'k narsani (masalan, koptokni) qidiraman, pashsha miyasi mashinani unga qarab haydaydi. Avval motorlarni shu kompyuterda yoqing; to'siq oldida mashina o'zi to'xtaydi. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**purple**
- EN: I will look for a round purple object, like a ball, and the fly brain will drive the car toward it. Arm the motors on this computer first; the car stops by itself close to obstacles. Faces are blurred and nothing is saved.
- RU: Я буду искать круглый фиолетовый предмет, например мяч, и мозг мухи поведёт машинку к нему. Сначала включите моторы на этом компьютере; у препятствий машинка остановится сама. Лица размываются, ничего не сохраняется.
- UZ: Yumaloq binafsha narsani (masalan, koptokni) qidiraman, pashsha miyasi mashinani unga qarab haydaydi. Avval motorlarni shu kompyuterda yoqing; to'siq oldida mashina o'zi to'xtaydi. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

### Count people

- EN: I will count people crossing the line in the middle of the view (right to left = in). Faces are blurred; only the numbers are kept.
- RU: Я посчитаю людей, пересекающих линию посередине кадра (справа налево — вошли). Лица размываются, сохраняются только числа.
- UZ: Ko'rinish o'rtasidagi chiziqdan o'tgan odamlarni sanayman (o'ngdan chapga — kirdi). Yuzlar xiralashtiriladi, faqat sonlar saqlanadi.
- [ ] Russian OK   - [ ] Uzbek OK

### Count pupils (school mode)

- EN: I will count students crossing the line in the middle of the view (right to left = in). School mode: counts only, faces blurred, nothing saved.
- RU: Я посчитаю учеников, пересекающих линию посередине кадра (справа налево — вошли). Школьный режим: только подсчёт, лица размываются, ничего не сохраняется.
- UZ: Ko'rinish o'rtasidagi chiziqdan o'tgan o'quvchilarni sanayman (o'ngdan chapga — kirdi). Maktab rejimi: faqat sanash, yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

### Find a thing (phone, backpack, bottle...)

Each thing once; the colours are spread over them ("any" = no colour said).

**phone, any**
- EN: I will look for the phone with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать телефон детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Telefonni shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**backpack, blue**
- EN: I will look for the blue backpack with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать рюкзак синего цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Ko'k ryukzakni shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**bag, red**
- EN: I will look for the red bag with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать сумку красного цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Qizil sumkani shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**bottle, green**
- EN: I will look for the green bottle with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать бутылку зелёного цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Yashil shishani shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**cup, white**
- EN: I will look for the white cup with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать чашку белого цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Oq piyolani shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**laptop, grey**
- EN: I will look for the grey (or silver) laptop with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать ноутбук серого (или серебристого) цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Kulrang (yoki kumushrang) noutbukni shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**book, black**
- EN: I will look for the black book with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать книгу чёрного цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Qora kitobni shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**chair, yellow**
- EN: I will look for the yellow chair with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать стул жёлтого цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Sariq stulni shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**bicycle, orange**
- EN: I will look for the orange bicycle with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать велосипед оранжевого цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: To'q sariq velosipedni shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**suitcase, purple**
- EN: I will look for the purple suitcase with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать чемодан фиолетового цвета детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Binafsha chamadonni shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

**umbrella, any**
- EN: I will look for the umbrella with the object detector on this computer and say whether it is left, center or right. Faces are blurred and nothing is saved.
- RU: Я буду искать зонт детектором предметов на этом компьютере и говорить, где предмет: слева, по центру или справа. Лица размываются, ничего не сохраняется.
- UZ: Soyabonni shu kompyuterdagi narsa topuvchi bilan qidiraman va u chapda, o'rtada yoki o'ngda ekanini aytaman. Yuzlar xiralashtiriladi, hech narsa saqlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

## 2. Refusals

When Ko'z refuses a job, before any camera opens. The same text for every planner.

### `ACTUATOR_FORBIDDEN`
- EN: This device action is not allowed.
- RU: Это действие устройства запрещено.
- UZ: Qurilmaning bu harakati taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

### `AUDIO_FORBIDDEN`
- EN: Audio is not allowed.
- RU: Аудио запрещено.
- UZ: Audio taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

### `IDENTITY_FORBIDDEN`
- EN: Identifying people is not allowed.
- RU: Идентификация людей запрещена.
- UZ: Odamlarni tanib olish taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

### `MOTOR_TARGET_FORBIDDEN`
- EN: Chasing people or animals is not allowed.
- RU: Преследовать людей или животных запрещено.
- UZ: Odam yoki hayvonni quvish taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

### `PRIVATE_BATHROOM`
- EN: Bathroom view blocked.
- RU: Вид ванной заблокирован.
- UZ: Hammom ko'rinishi bloklandi.
- [ ] Russian OK   - [ ] Uzbek OK

### `PRIVATE_BEDROOM`
- EN: Bedroom view blocked.
- RU: Вид спальни заблокирован.
- UZ: Yotoqxona ko'rinishi bloklandi.
- [ ] Russian OK   - [ ] Uzbek OK

### `PRIVATE_CHANGING_ROOM`
- EN: Changing-room view blocked.
- RU: Вид раздевалки заблокирован.
- UZ: Kiyinish xonasi ko'rinishi bloklandi.
- [ ] Russian OK   - [ ] Uzbek OK

### `PRIVATE_TOILET`
- EN: Toilet view blocked.
- RU: Вид туалета заблокирован.
- UZ: Hojatxona ko'rinishi bloklandi.
- [ ] Russian OK   - [ ] Uzbek OK

### `PROFILING_FORBIDDEN`
- EN: Judging or profiling people is not allowed.
- RU: Оценивать и профилировать людей запрещено.
- UZ: Odamlarni baholash va profillash taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

### `SOLE_PROTECTION_FORBIDDEN`
- EN: Ko'z cannot be the only safeguard.
- RU: Ko'z не может быть единственной защитой.
- UZ: Ko'z yagona himoya bo'la olmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

### `UNSUPPORTED_CAPABILITY`
- EN: This feature is not available.
- RU: Эта функция недоступна.
- UZ: Bu imkoniyat mavjud emas.
- [ ] Russian OK   - [ ] Uzbek OK

### `VIEW_FORBIDDEN`
- EN: This camera use is not allowed.
- RU: Такое использование камеры запрещено.
- UZ: Kameradan bunday foydalanish taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

### `INVALID_COMMAND`
- EN: Command is invalid.
- RU: Команда недопустима.
- UZ: Buyruq yaroqsiz.
- [ ] Russian OK   - [ ] Uzbek OK

### `PLANNER_UNAVAILABLE`
- EN: Planner is unavailable.
- RU: Планировщик недоступен.
- UZ: Rejalashtiruvchi ishlamayapti.
- [ ] Russian OK   - [ ] Uzbek OK

## 3. Other stop and error messages

Shown when a running job stops, or a command or recipe is refused.

### `INVALID_RECIPE`
- EN: Recipe is invalid.
- RU: Рецепт недопустим.
- UZ: Retsept yaroqsiz.
- [ ] Russian OK   - [ ] Uzbek OK

### `SAFETY_LOCKED`
- EN: Safety settings are locked.
- RU: Настройки безопасности заблокированы.
- UZ: Xavfsizlik sozlamalari qulflangan.
- [ ] Russian OK   - [ ] Uzbek OK

### `ADJUSTMENT_LIMIT`
- EN: Three attempts failed. Job is off.
- RU: Три попытки не удались. Задание отключено.
- UZ: Uch urinish muvaffaqiyatsiz. Vazifa o'chirildi.
- [ ] Russian OK   - [ ] Uzbek OK

### `CHECK_FAILED`
- EN: Check failed. Job stopped.
- RU: Проверка не пройдена. Задание остановлено.
- UZ: Tekshiruv o'tmadi. Vazifa to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK

### `PRIVACY_UNCERTAIN`
- EN: Scene safety is unknown.
- RU: Безопасность сцены неизвестна.
- UZ: Ko'rinish xavfsizligi noma'lum.
- [ ] Russian OK   - [ ] Uzbek OK

### `PRIVACY_UNAVAILABLE`
- EN: Privacy check is unavailable.
- RU: Проверка приватности недоступна.
- UZ: Maxfiylik tekshiruvi ishlamayapti.
- [ ] Russian OK   - [ ] Uzbek OK

### `BLUR_UNAVAILABLE`
- EN: Face blur is unavailable.
- RU: Размытие лиц недоступно.
- UZ: Yuzlarni xiralashtirish ishlamayapti.
- [ ] Russian OK   - [ ] Uzbek OK

### `SCENE_CHANGED`
- EN: View changed. Outputs stopped.
- RU: Вид изменился. Выходы отключены.
- UZ: Ko'rinish o'zgardi. Chiqishlar to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK

### `LENS_COVERED`
- EN: Lens may be covered.
- RU: Возможно, объектив закрыт.
- UZ: Obyektiv yopilgan bo'lishi mumkin.
- [ ] Russian OK   - [ ] Uzbek OK

### `SCHOOL_COUNTS_ONLY`
- EN: School mode allows counts only.
- RU: В школьном режиме разрешён только подсчёт.
- UZ: Maktab rejimida faqat sanash mumkin.
- [ ] Russian OK   - [ ] Uzbek OK

### `OWNERSHIP_REQUIRED`
- EN: Confirm on this computer that you own the camera.
- RU: Подтвердите на этом компьютере, что камера ваша.
- UZ: Kamera sizniki ekanini shu kompyuterda tasdiqlang.
- [ ] Russian OK   - [ ] Uzbek OK

### `ALLOWED_AREA_REQUIRED`
- EN: Draw the allowed area on this computer.
- RU: Отметьте разрешённую область на этом компьютере.
- UZ: Ruxsat etilgan hududni shu kompyuterda belgilang.
- [ ] Russian OK   - [ ] Uzbek OK

### `FRAMES_FORBIDDEN`
- EN: Saving or sending frames is not allowed.
- RU: Сохранять и передавать кадры запрещено.
- UZ: Kadrlarni saqlash va yuborish taqiqlangan.
- [ ] Russian OK   - [ ] Uzbek OK

### `INVALID_EVENT`
- EN: Event data is not allowed.
- RU: Данные события недопустимы.
- UZ: Hodisa ma'lumotlari yaroqsiz.
- [ ] Russian OK   - [ ] Uzbek OK

### `AUTH_REQUIRED`
- EN: Sign in or connect the runner.
- RU: Войдите или подключите исполнитель.
- UZ: Tizimga kiring yoki ijrochini ulang.
- [ ] Russian OK   - [ ] Uzbek OK

### `FRAME_STALE`
- EN: Camera data is stale. Outputs stopped.
- RU: Данные камеры устарели. Выходы отключены.
- UZ: Kamera ma'lumoti eskirgan. Chiqishlar to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK

### `OVERLOADED`
- EN: Too much processing. Outputs stopped.
- RU: Обработка перегружена. Выходы отключены.
- UZ: Ishlov berish haddan oshdi. Chiqishlar to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK

### `MOTOR_NOT_ARMED`
- EN: Arm the motors on this computer.
- RU: Включите моторы на этом компьютере.
- UZ: Motorlarni shu kompyuterda yoqing.
- [ ] Russian OK   - [ ] Uzbek OK

### `MOTOR_SAFETY_STOP`
- EN: Motor safety stop.
- RU: Защитная остановка моторов.
- UZ: Motorlar xavfsizlik uchun to'xtadi.
- [ ] Russian OK   - [ ] Uzbek OK

### `RETENTION_LOCKED`
- EN: Storage times are fixed.
- RU: Сроки хранения фиксированы.
- UZ: Saqlash muddatlari o'zgarmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

### `VIDEO_UNREADABLE`
- EN: video file not found or unreadable.
- RU: Видеофайл не найден или не читается.
- UZ: Video fayl topilmadi yoki uni o'qib bo'lmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

### `BUSY`
- EN: Stop the current job first.
- RU: Сначала остановите текущее задание.
- UZ: Avval joriy vazifani to'xtating.
- [ ] Russian OK   - [ ] Uzbek OK

### `COMMAND_EXPIRED`
- EN: Command expired.
- RU: Срок команды истёк.
- UZ: Buyruq muddati tugadi.
- [ ] Russian OK   - [ ] Uzbek OK

### `PROTOCOL_VERSION`
- EN: Contract version is not supported.
- RU: Версия контракта не поддерживается.
- UZ: Kontrakt versiyasi qo'llab-quvvatlanmaydi.
- [ ] Russian OK   - [ ] Uzbek OK

### `INTERNAL_ERROR`
- EN: Internal error. Job stopped.
- RU: Внутренняя ошибка. Задание остановлено.
- UZ: Ichki xato. Vazifa to'xtatildi.
- [ ] Russian OK   - [ ] Uzbek OK
