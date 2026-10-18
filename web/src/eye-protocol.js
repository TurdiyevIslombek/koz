import {parseStrict} from './protocol.js';

export const MAX_EYE_BYTES = 160 * 1024;   // contract section 14 (raised Oct 18)
export const MAX_EYE_WIDTH = 640;
export const EYE_FRESH_MS = 1000;
export const eyeClosed = reason => ({v:1,type:'preview',state:'closed',reason});

export function readEyeClosed(text) {
 const data = parseStrict(text, 256);
 if (!data || Object.keys(data).sort().join(',') !== 'reason,state,type,v' ||
     data.v !== 1 || data.type !== 'preview' || data.state !== 'closed' ||
     !['checking','not_running','not_fresh'].includes(data.reason)) throw Error('Invalid preview');
 return data;
}

// Check JPEG framing and dimensions before handing bytes to the browser's image decoder.
// No decoding, conversion to text, persistence or event-log path exists here.
export function validEyeJPEG(bytes) {
 const size = bytes.byteLength;
 if (size < 12 || size > MAX_EYE_BYTES || bytes[0] !== 255 || bytes[1] !== 216 ||
     bytes[size-2] !== 255 || bytes[size-1] !== 217) return false;
 let offset = 2, dimensions = false;
 while (offset + 3 < size) {
  if (bytes[offset++] !== 255) return false;
  while (bytes[offset] === 255) offset++;
  const marker = bytes[offset++];
  if (marker === 218) return dimensions; // compressed image data follows Start of Scan
  if (marker === 217 || marker === 0) return false;
  const length = bytes[offset] * 256 + bytes[offset+1];
  if (length < 2 || offset + length > size-2) return false;
  if ([192,193,194].includes(marker)) {
   const height = bytes[offset+3] * 256 + bytes[offset+4];
   const width = bytes[offset+5] * 256 + bytes[offset+6];
   if (length < 8 || !height || !width || width > MAX_EYE_WIDTH) return false;
   dimensions = true;
  }
  offset += length;
 }
 return false;
}
