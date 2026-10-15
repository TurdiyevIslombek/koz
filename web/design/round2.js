// A hand-authored SVG fixture, never camera data. No network, media, storage or tracking APIs.
const sceneCopy = {
  uz: { sees:'Koʻz nimani koʻryapti?', sample:'SVG namuna', entrance:'Eshik oldi', masks:'Yuzlar berkitilgan', play:'Oʻtishni koʻrsatish', sceneNote:'Sanash chizigʻi · kirish →', crossed:'Chiziqdan 1 kishi oʻtdi · +1', sceneOff:'Koʻrinish mavjud emas', privacyTitle:'Odam sanaladi. Shaxs aniqlanmaydi.', privacyText:'Yuzlar yashiriladi. Video va ovoz saqlanmaydi. Qurilmadan bu ekranga faqat raqamlar keladi.', review:'Maketni tekshirish', mockNote:'Bu chizilgan namuna. Kamera ulanmagan.', stop:'Vazifani toʻxtatish', actionNote:'Namuna · qurilmaga buyruq yuborilmaydi', now:'Hududda hozir', measured:'Maʼlumot yangi', measuredZero:'Oʻlchangan nol', complete:'Vazifa boshlanganidan beri · oʻtishlar soni', runningReason:'Kirish va chiqishlar sanalyapti.', fontTest:'Koʻz · Oʻzbek · toʻxtatish', sceneDescription:'Chizilgan eshik koʻrinishi. Odamlar konturda, yuzlar yopiq toʻrtburchaklar bilan berkitilgan. Koʻk chiziq sanash chegarasini koʻrsatadi.' },
  ru: { sees:'Что видит Koʻz', sample:'SVG-пример', entrance:'У входа', masks:'Лица скрыты', play:'Показать проход', sceneNote:'Линия подсчёта · вход →', crossed:'Линию пересёк 1 человек · +1', sceneOff:'Изображение недоступно', privacyTitle:'Считаем людей. Не узнаём личности.', privacyText:'Лица скрыты. Видео и звук не сохраняются. С устройства на этот экран поступают только числа.', review:'Проверить макет', mockNote:'Нарисованный пример. Камера не подключена.', stop:'Остановить задание', actionNote:'Макет · команда устройству не отправляется', now:'Сейчас в зоне', measured:'Свежие данные', measuredZero:'Измеренный ноль', complete:'С начала задания · количество проходов', runningReason:'Считаем входы и выходы.', fontTest:'Koʻz · Oʻzbek · toʻxtatish', sceneDescription:'Нарисованный вход. Люди показаны контурами, лица закрыты сплошными прямоугольниками. Синяя линия обозначает границу подсчёта.' },
  en: { sees:'What Koʻz sees', sample:'SVG sample', entrance:'At the doorway', masks:'Faces concealed', play:'Show a crossing', sceneNote:'Counting line · entry →', crossed:'1 person crossed the line · +1', sceneOff:'View unavailable', privacyTitle:'Count people. Never identify them.', privacyText:'Faces are hidden. No video or audio is saved. Only numbers travel from the device to this screen.', review:'Inspect mockup', mockNote:'An illustrated sample. No camera is connected.', stop:'Stop job', actionNote:'Mockup · no command is sent to a device', now:'In the area now', measured:'Fresh data', measuredZero:'Measured zero', complete:'Since the job started · crossing totals', runningReason:'Counting entries and exits.', fontTest:'Koʻz · Oʻzbek · toʻxtatish', sceneDescription:'An illustrated doorway. People are outlines, with faces concealed by solid rectangles. A blue line marks the counting boundary.' }
};
for (const lang of Object.keys(sceneCopy)) Object.assign(copy[lang], sceneCopy[lang]);
const emptyDescriptions = {
  uz:'Chizilgan boʻsh eshik koʻrinishi. Odamlar yoʻq. Koʻk chiziq sanash chegarasini koʻrsatadi.',
  ru:'Нарисованный пустой вход. Людей нет. Синяя линия обозначает границу подсчёта.',
  en:'An illustrated empty doorway. No people are present. The blue line marks the counting boundary.'
};
let additions = 0, previousState = state, crossingTimer, walking = null, pulse = null, crossingActive = false;
const baseRender = render;
const activeScene = () => ['running','gap'].includes(state);
function cancelCrossing() {
  clearTimeout(crossingTimer);
  walking?.cancel(); pulse?.cancel();
  walking = pulse = null; crossingActive = false;
}
render = function () {
  if (state !== previousState) {
    cancelCrossing();
    if (state !== 'pending') additions = 0;
    previousState = state;
  }
  baseRender();
  const t = copy[language];
  const active = activeScene();
  $('#scene-cover').hidden = active || state === 'zero';
  $('.scene-frame').dataset.off = String(!active && state !== 'zero');
  $('#scene-cover').textContent = t.sceneOff;
  $('.scene-svg').setAttribute('aria-hidden', String(!active && state !== 'zero'));
  $('.scene-svg').setAttribute('aria-label', state === 'zero' ? emptyDescriptions[language] : t.sceneDescription);
  $('.people').style.visibility = state === 'zero' ? 'hidden' : 'visible';
  $('#crossing').disabled = !active || crossingActive;
  $('#scene-note').textContent = additions ? t.crossed : t.sceneNote;
  if (active || (state === 'pending' && ['running','gap'].includes(pendingFrom))) {
    $('[data-field="count"]').textContent = String(7 + additions);
    $('[data-field="entered"]').textContent = String(24 + additions);
  }
  const amount = $('[data-field="count"]').textContent.length;
  $('.reading').dataset.digits = amount > 2 ? 'many' : amount > 1 ? 'two' : 'one';
  const shapes = {run:'M4 10l4 4L17 5',warn:'M7 5v10m6-10v10',stop:'M5 5h10v10H5z',unknown:'M7 7a3 3 0 0 1 6 0c0 2-3 2-3 4m0 4h.01'};
  $('#status-path').setAttribute('d', shapes[document.body.dataset.tone]);
};
$('#crossing').addEventListener('click', () => {
  if (!activeScene() || crossingActive) return;
  cancelCrossing();
  crossingActive = true;
  $('#crossing').disabled = true;
  const person = $('.crossing-person');
  const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function crossed() {
    if (!activeScene()) return;
    additions += 1;
    person.style.transform = 'translateX(45px)';
    if (!reduced) pulse = $('.line-pulse').animate([{opacity:.65},{opacity:0}],{duration:420,easing:'ease-out'});
    render();
  }
  if (reduced) {
    crossingActive = false;
    crossed();
  } else {
    walking = person.animate([{transform:'translateX(-45px)'},{transform:'translateX(45px)'}],{duration:1000,easing:'linear',fill:'forwards'});
    crossingTimer = setTimeout(crossed,500);
    walking.onfinish = () => { crossingActive = false; $('#crossing').disabled = !activeScene(); };
  }
});
// Keep the fixed dock clear of content at large text sizes and with long translations.
if ('ResizeObserver' in window) new ResizeObserver(([entry]) => {
  const room = Math.ceil(entry.target.getBoundingClientRect().height) + 30;
  $('.page').style.paddingBottom = `${room}px`;
  document.documentElement.style.scrollPaddingBottom = `${room}px`;
}).observe($('.action-dock'));
render();
