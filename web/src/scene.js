export function sceneSVG(empty=false,available=true,label=''){
 return `<svg class="eye-view" viewBox="0 0 360 200" role="img" aria-label="${label}" ${available?'':'aria-hidden="true"'}>
 <defs><clipPath id="eye-window"><path d="M2 100C50-18 310-18 358 100C310 218 50 218 2 100Z"/></clipPath><g id="anonymous-person"><circle class="silhouette" cx="0" cy="0" r="10"/><path class="silhouette" d="M-7 11C-18 12-23 25-22 37C-22 43-16 45-13 39L-11 30C-10 42-15 54-10 61C-6 66 1 64 2 58L3 43C5 49 3 58 7 62C13 67 18 62 16 55L13 30C16 36 17 42 22 40C27 37 21 24 18 19C15 12 6 10-7 11Z"/><rect class="face-mask" x="-11" y="-8" width="22" height="15" rx="3"/></g></defs>
 <g clip-path="url(#eye-window)"><rect class="eye-ground" width="360" height="200"/><path class="floor-lines" d="M0 61h360M0 157h360M40 0v200M320 0v200M0 200 128 0M360 200 232 0"/><path class="counting-line" d="M180 8v184"/><path class="crossing-pulse" d="M180 8v184"/>
 <path class="entry-arrow" d="M154 178h52m-8-6 8 6-8 6"/>
 <g class="silhouettes" ${empty?'visibility="hidden"':''}><use href="#anonymous-person" transform="translate(91 70) scale(.7)"/><use href="#anonymous-person" transform="translate(268 65) scale(.6)"/><use href="#anonymous-person" transform="translate(266 110) scale(.65)"/><g transform="translate(180 99)"><g class="crossing-silhouette"><use href="#anonymous-person"/></g></g></g></g></svg>`;
}
export function pulseCrossing(root=document){
 const line=root.querySelector('.crossing-pulse');if(!line||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 line.animate([{opacity:.65},{opacity:0}],{duration:420,easing:'ease-out'});
}
export function icon(name){
 const paths={eye:'M2 10Q10-2 18 10Q10 22 2 10ZM10 7a3 3 0 1 0 0 6 3 3 0 0 0 0-6',sun:'M10 1v2m0 14v2M1 10h2m14 0h2M4 4l1 1m10 10 1 1M4 16l1-1M15 5l1-1M10 6a4 4 0 1 0 0 8 4 4 0 0 0 0-8',moon:'M16 12a7 7 0 1 1-8-8 6 6 0 0 0 8 8',camera:'M2 5h11v10H2zM13 8l5-3v10l-5-3',check:'M3 10l4 4L17 4',pause:'M7 4v12m6-12v12',stop:'M5 5h10v10H5z',question:'M7 7a3 3 0 0 1 6 0c0 2-3 2-3 4m0 4h.01',lock:'M5 9h10v9H5zM7 9V6a3 3 0 0 1 6 0v3',arrow:'M3 10h14m-6-6 6 6-6 6',download:'M10 2v11m-4-4 4 4 4-4M3 14v4h14v-4',upload:'M10 13V2m-4 4 4-4 4 4M3 14v4h14v-4',close:'M4 4l12 12M16 4 4 16',link:'m7 13-2 2a3 3 0 0 1-4-4l4-4a3 3 0 0 1 4 0m2 0 2-2a3 3 0 0 1 4 4l-4 4a3 3 0 0 1-4 0m-3-3 6-6'};
 return `<svg class="icon" viewBox="0 0 20 20" aria-hidden="true"><path d="${paths[name]||paths.question}"/></svg>`;
}
