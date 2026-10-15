import { WebSocket } from 'ws';

// One connection, no offline command queue. Reconnects never replay commands.
export function connectRunner({ url, onSocket, onWaiting, retryMs = 1000 }) {
  const parsed = new URL(url);
  if (parsed.protocol !== 'ws:' || !['127.0.0.1', 'localhost', '[::1]'].includes(parsed.hostname)) {
    throw new Error('The development runner must use a loopback WebSocket.');
  }
  let socket, timer, closed = false;
  function connect() {
    if (closed) return;
    let source = 'runner';
    socket = new WebSocket(url, { maxPayload: 32768, perMessageDeflate: false, handshakeTimeout: 2500 });
    socket.on('upgrade', response => {
      if (response.headers['x-koz-source'] === 'replay') source = 'replay';
    });
    socket.on('open', () => onSocket(socket, source));
    socket.on('error', () => {}); // Only fixed UI messages; never expose exceptions.
    socket.on('close', () => {
      if (closed) return;
      onWaiting();
      timer = setTimeout(connect, retryMs);
      timer.unref();
    });
  }
  connect();
  return { close() { closed = true; clearTimeout(timer); socket?.terminate(); } };
}
