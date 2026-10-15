// Presentation fixtures only. No camera, API, storage, timer, or runner connection.
const copy = {
  uz: {
    skip:'Vazifaga oʻtish', static:'Statik maket', theme:'Tungi', light:'Kunduzgi', language:'Til',
    liveJob:'Joriy vazifa', title:'Kirishni sanash', subtitle:'Chiziqdan oʻtganlarni ikki yoʻnalishda sanash.',
    now:'Hududda hozir', people:'kishi', entered:'Kirgan', exited:'Chiqqan', reading:'Joriy oʻlchov',
    protection:'Maxfiylik himoyasi', locked:'QULFLANGAN', guardNote:'Faqat ruxsat etilgan hudud sanaladi.',
    blurNote:'Odamlarning shaxsi aniqlanmaydi.', noVideo:'Video yuborilmaydi', noVideoNote:'Bu ekranga faqat raqamlar keladi.',
    local:'Tasvir shu yerda qoladi', localNote:'Tasvir kameraga ulangan kompyuterda qayta ishlanadi. Video va ovoz saqlanmaydi.',
    recipe:'Vazifa qanday ishlaydi?', step1:'Koʻrinish maxfiylik uchun tekshiriladi.', step2:'Yuzlar xiralashtiriladi.',
    step3:'Chiziqdan oʻtishlar sanaladi.', step4:'Raqamlar shu ekranga yuboriladi.',
    mockNote:'Dizayn namunasi. Kamera ulanmagan; raqamlar misol uchun.', previewState:'Namuna holati',
    optionRunning:'Ishlayapti · 7 kishi', optionZero:'Ishlayapti · oʻlchangan 0', optionPaused:'Kutilyapti · maxfiylik tekshiruvi',
    optionStopped:'Toʻxtatilgan · qurilma tasdiqlagan', optionBlocked:'Bloklangan · maxfiy hudud', optionUnknown:'Nomaʼlum · aloqa uzilgan',
    optionGap:'Ishlayapti · hisobda uzilish bor', optionPending:'Toʻxtatish soʻralgan · tasdiq kutilmoqda',
    fontTest:'Yozuvlarni tekshirish', stop:'Vazifani toʻxtatish', stopping:'Tasdiq kutilmoqda',
    running:'Ishlayapti', runningReason:'Kamera kirish va chiqishlarni sanayapti.',
    zeroReason:'Kamera javob beryapti; hududda hech kim aniqlanmadi.', paused:'Kutilyapti',
    pausedReason:'Maxfiylik qayta tekshirilmoqda; sanash kutib turibdi.', stopped:'Toʻxtatilgan',
    stoppedReason:'Vazifa toʻxtatilganini qurilma tasdiqladi.', blocked:'Bloklangan',
    // Fixed fault copy is verbatim from contracts/events.md, including its apostrophe style.
    blockedReason:"Hammom ko'rinishi bloklandi.", unknown:'Nomaʼlum',
    unknownReason:'Aloqa uzilgan; vazifa holati nomaʼlum.', gapReason:'Sanash davom etmoqda; uzilishdagi oʻtishlar hisobga kirmagan.',
    measured:'Oʻlchangan · maʼlumot yangi', measuredZero:'Oʻlchangan 0 · hududda hech kim yoʻq',
    noMeasure:'Hozirgi son nomaʼlum', noResponse:'Qurilma javob bermayapti · bu 0 emas',
    complete:'Vazifa boshlanganidan beri · uzilishsiz', gapped:'Vazifa boshlanganidan beri · hisob toʻliq emas',
    unavailable:'Hozirgi raqamlar mavjud emas', guard:'Tekshiruvdan oʻtgan', guardChecking:'Tekshiruv davom etmoqda',
    guardBlocked:'Maxfiylik uchun bloklangan', guardUnknown:'Tekshiruv holati nomaʼlum', guardOff:'Tekshiruv ishlamayapti',
    blur:'Yuzlar xiralashtirilgan', blurWaiting:'Yuzlarni xiralashtirish kutilyapti', blurOff:'Tasvir qayta ishlanmayapti', blurUnknown:'Yuzlar xiraligi nomaʼlum',
    camera:'Kamera yoqilgan', cameraOff:'Kamera oʻchirilgan', cameraUnknown:'Kamera holati nomaʼlum',
    guardShort:'Tekshiruv: ruxsat', guardCheckingShort:'Tekshiruv: kutilmoqda', guardBlockedShort:'Tekshiruv: bloklangan', guardUnknownShort:'Tekshiruv: nomaʼlum', guardOffShort:'Tekshiruv: oʻchiq',
    blurShort:'Yuzlar: xira', blurWaitingShort:'Yuzlar: kutilmoqda', blurOffShort:'Tasvir: toʻxtatilgan', blurUnknownShort:'Yuzlar: nomaʼlum',
    actionNote:'Namuna tugmasi · haqiqiy qurilmaga buyruq yuborilmaydi', pendingNote:'Soʻrov yuborildi · qurilma tasdigʻi kutilmoqda (namuna)',
    offlineNote:'Buyruq yetib bormaydi. Kameraga ulangan kompyuterni tekshiring.', stoppedNote:'Vazifa toʻxtatilgan · namuna holati', blockedNote:'Himoya vazifani bloklagan · namuna holati'
  },
  ru: {
    skip:'Перейти к заданию', static:'Статичный макет', theme:'Тёмная', light:'Светлая', language:'Язык',
    liveJob:'Текущее задание', title:'Подсчёт входов', subtitle:'Подсчёт пересечений линии в обе стороны.',
    now:'Сейчас в зоне', people:'человек', entered:'Вошли', exited:'Вышли', reading:'Текущий замер',
    protection:'Защита приватности', locked:'ЗАБЛОКИРОВАНО', guardNote:'Подсчёт только в разрешённой зоне.',
    blurNote:'Личность людей не определяется.', noVideo:'Видео не передаётся', noVideoNote:'На этот экран поступают только числа.',
    local:'Изображение остаётся здесь', localNote:'Кадры обрабатываются на компьютере, подключённом к камере. Видео и звук не сохраняются.',
    recipe:'Как работает задание?', step1:'Проверяется приватность сцены.', step2:'Лица размываются.', step3:'Считаются пересечения линии.', step4:'Числа отправляются на этот экран.',
    mockNote:'Макет дизайна. Камера не подключена; числа приведены для примера.', previewState:'Пример состояния',
    optionRunning:'Работает · 7 человек', optionZero:'Работает · измеренный 0', optionPaused:'Ожидание · проверка приватности',
    optionStopped:'Остановлено · устройство подтвердило', optionBlocked:'Заблокировано · приватная зона', optionUnknown:'Неизвестно · нет связи',
    optionGap:'Работает · есть пропуск в подсчёте', optionPending:'Запрошена остановка · ждём подтверждения',
    fontTest:'Проверка шрифтов', stop:'Остановить задание', stopping:'Ждём подтверждения',
    running:'Работает', runningReason:'Камера считает входы и выходы.', zeroReason:'Камера отвечает; в зоне никто не обнаружен.',
    paused:'Ожидание', pausedReason:'Повторная проверка приватности; подсчёт приостановлен.', stopped:'Остановлено',
    stoppedReason:'Устройство подтвердило остановку задания.', blocked:'Заблокировано', blockedReason:'Вид ванной заблокирован.',
    unknown:'Неизвестно', unknownReason:'Связь потеряна; состояние задания неизвестно.', gapReason:'Подсчёт продолжается; пересечения во время сбоя не учтены.',
    measured:'Измерено · свежие данные', measuredZero:'Измеренный 0 · в зоне никого нет', noMeasure:'Текущее число неизвестно', noResponse:'Устройство не отвечает · это не 0',
    complete:'С начала задания · без пропусков', gapped:'С начала задания · подсчёт неполный', unavailable:'Текущие числа недоступны',
    guard:'Проверка пройдена', guardChecking:'Идёт проверка', guardBlocked:'Заблокировано для приватности', guardUnknown:'Состояние проверки неизвестно', guardOff:'Проверка не выполняется',
    blur:'Лица размыты', blurWaiting:'Размытие лиц ожидает', blurOff:'Кадры не обрабатываются', blurUnknown:'Состояние размытия неизвестно',
    camera:'Камера включена', cameraOff:'Камера выключена', cameraUnknown:'Состояние камеры неизвестно',
    guardShort:'Проверка: разрешено', guardCheckingShort:'Проверка: ожидание', guardBlockedShort:'Проверка: запрет', guardUnknownShort:'Проверка: неизвестно', guardOffShort:'Проверка: выключена',
    blurShort:'Лица: размыты', blurWaitingShort:'Лица: ожидание', blurOffShort:'Обработка: остановлена', blurUnknownShort:'Лица: неизвестно',
    actionNote:'Кнопка макета · команда устройству не отправляется', pendingNote:'Запрос отправлен · ждём подтверждения устройства (макет)',
    offlineNote:'Команда не дойдёт. Проверьте компьютер у камеры.', stoppedNote:'Задание остановлено · пример состояния', blockedNote:'Защита заблокировала задание · пример состояния'
  },
  en: {
    skip:'Skip to job', static:'Static mockup', theme:'Dark', light:'Light', language:'Language',
    liveJob:'Live job', title:'Count entries', subtitle:'Count line crossings in both directions.', now:'In the area now', people:'people', entered:'Entered', exited:'Exited', reading:'Current reading',
    protection:'Privacy protection', locked:'LOCKED', guardNote:'Only the allowed area is counted.', blurNote:'People are never identified.',
    noVideo:'No video is sent', noVideoNote:'Only numbers reach this screen.', local:'Images stay here', localNote:'Frames are processed on the computer connected to the camera. Video and audio are not saved.',
    recipe:'How does this job work?', step1:'Check the scene for privacy.', step2:'Blur faces.', step3:'Count line crossings.', step4:'Send numbers to this screen.',
    mockNote:'Design mockup. No camera is connected; numbers are examples.', previewState:'Preview state',
    optionRunning:'Running · 7 people', optionZero:'Running · measured 0', optionPaused:'Paused · privacy check', optionStopped:'Stopped · confirmed by device',
    optionBlocked:'Blocked · private area', optionUnknown:'Unknown · connection lost', optionGap:'Running · count has a gap', optionPending:'Stop requested · awaiting confirmation',
    fontTest:'Check font coverage', stop:'Stop job', stopping:'Awaiting confirmation', running:'Running', runningReason:'The camera is counting entries and exits.',
    zeroReason:'The camera is responding; no one was detected in the area.', paused:'Paused', pausedReason:'Privacy is being checked again; counting is on hold.',
    stopped:'Stopped', stoppedReason:'The device confirmed that the job stopped.', blocked:'Blocked', blockedReason:'Bathroom view blocked.',
    unknown:'Unknown', unknownReason:'Connection lost; job state is unknown.', gapReason:'Counting continues; crossings during the gap were not counted.',
    measured:'Measured · fresh data', measuredZero:'Measured 0 · no one in the area', noMeasure:'Current count unknown', noResponse:'Device not responding · this is not 0',
    complete:'Since this job started · no gaps', gapped:'Since this job started · count incomplete', unavailable:'Current readings unavailable',
    guard:'Privacy check approved', guardChecking:'Privacy check in progress', guardBlocked:'Blocked for privacy', guardUnknown:'Privacy check state unknown', guardOff:'Privacy check inactive',
    blur:'Faces blurred', blurWaiting:'Face blur waiting', blurOff:'Frames are not processed', blurUnknown:'Face blur state unknown',
    camera:'Camera on', cameraOff:'Camera off', cameraUnknown:'Camera state unknown',
    guardShort:'Check: approved', guardCheckingShort:'Check: waiting', guardBlockedShort:'Check: blocked', guardUnknownShort:'Check: unknown', guardOffShort:'Check: off',
    blurShort:'Faces: blurred', blurWaitingShort:'Faces: waiting', blurOffShort:'Processing: stopped', blurUnknownShort:'Faces: unknown',
    actionNote:'Mockup button · no command is sent to a device', pendingNote:'Request sent · awaiting device confirmation (mockup)',
    offlineNote:'Cannot deliver a command. Check the computer by the camera.', stoppedNote:'Job stopped · sample state', blockedNote:'Protection blocked the job · sample state'
  }
};

const parameters = new URLSearchParams(location.search);
const states = ['running','zero','paused','stopped','blocked','unknown','gap','pending'];
let language = Object.hasOwn(copy, parameters.get('lang')) ? parameters.get('lang') : 'uz';
let state = states.includes(parameters.get('state')) ? parameters.get('state') : 'running';
// Pending is a command state, not a new measurement. Keep the source fixture intact.
let pendingFrom = 'running';
const systemDark = matchMedia('(prefers-color-scheme: dark)').matches;
let dark = parameters.has('theme') ? parameters.get('theme') === 'dark' : systemDark;
const $ = (selector) => document.querySelector(selector);

function render() {
  const text = copy[language];
  document.documentElement.lang = language;
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = text[el.dataset.i18n]; });
  $('#theme span').textContent = dark ? text.light : text.theme;
  $('#theme').setAttribute('aria-pressed', String(dark));
  $('#theme').setAttribute('aria-label', dark ? text.light : text.theme);
  $('#language').value = language;
  $('#state').value = state;

  const pending = state === 'pending';
  const fixture = pending ? pendingFrom : state;
  const valid = ['running','zero','gap'].includes(fixture);
  const stopped = fixture === 'stopped';
  const blocked = fixture === 'blocked';
  const paused = fixture === 'paused';
  const unknown = fixture === 'unknown';
  const zero = fixture === 'zero';
  const tone = paused ? 'warn' : stopped || blocked ? 'stop' : unknown ? 'unknown' : 'run';
  document.body.dataset.tone = tone;
  const fields = {
    status: text[valid ? 'running' : fixture],
    mark: paused ? 'Ⅱ' : stopped ? '■' : blocked ? '×' : unknown ? '?' : '✓',
    reason: text[zero ? 'zeroReason' : fixture === 'gap' ? 'gapReason' : valid ? 'runningReason' : `${fixture}Reason`],
    count: valid ? zero ? '0' : '7' : '—',
    // Zero occupancy does not erase cumulative crossings.
    entered: valid ? '24' : '—', exited: valid ? zero ? '24' : '17' : '—',
    measurement: text[unknown ? 'noResponse' : !valid ? 'noMeasure' : zero ? 'measuredZero' : 'measured'],
    coverage: text[fixture === 'gap' || unknown ? 'gapped' : valid ? 'complete' : 'unavailable'],
    camera: text[unknown ? 'cameraUnknown' : stopped ? 'cameraOff' : 'camera'],
    guard: text[unknown ? 'guardUnknown' : paused ? 'guardChecking' : blocked ? 'guardBlocked' : stopped ? 'guardOff' : 'guard'],
    blur: text[unknown ? 'blurUnknown' : paused ? 'blurWaiting' : stopped || blocked ? 'blurOff' : 'blur'],
    guardShort: text[unknown ? 'guardUnknownShort' : paused ? 'guardCheckingShort' : blocked ? 'guardBlockedShort' : stopped ? 'guardOffShort' : 'guardShort'],
    blurShort: text[unknown ? 'blurUnknownShort' : paused ? 'blurWaitingShort' : stopped || blocked ? 'blurOffShort' : 'blurShort'],
    actionNote: text[pending ? 'pendingNote' : unknown ? 'offlineNote' : stopped ? 'stoppedNote' : blocked ? 'blockedNote' : 'actionNote']
  };
  document.querySelectorAll('[data-field]').forEach(el => { el.textContent = fields[el.dataset.field]; });
  $('[data-field="coverage"]').dataset.gapped = String(fixture === 'gap' || unknown);
  $('#stop').disabled = unknown || stopped || blocked || pending;
  $('#stop [data-i18n]').textContent = pending ? text.stopping : text.stop;
  // Preserve the comparison settings when opening the other direction.
  document.querySelectorAll('.design-bar nav a').forEach(a => {
    a.search = new URLSearchParams({theme:dark?'dark':'light',lang:language,state}).toString();
  });
}

$('#theme').addEventListener('click', () => { dark = !dark; render(); });
$('#language').addEventListener('change', event => { language = event.target.value; render(); });
$('#state').addEventListener('change', event => { state = event.target.value; pendingFrom = 'running'; render(); });
// Stop previews only a pending request. A simulated acknowledgement never proves a stop.
// Select the explicit "device confirmed" fixture to inspect the stopped presentation.
$('#stop').addEventListener('click', () => { pendingFrom = state; state = 'pending'; render(); });
render();
