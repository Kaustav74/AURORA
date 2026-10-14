export type ConnectionStatus = 'CONNECTED' | 'DISCONNECTED' | 'RECONNECTING';

export interface WebSocketEnvelope {
  type: string;
  run_id?: string;
  timestamp_sim?: number;
  timestamp_wall?: string;
  payload: any;
}

export class TelemetryWebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private onMessageCallback: ((data: WebSocketEnvelope) => void) | null = null;
  private onStatusChangeCallback: ((status: ConnectionStatus) => void) | null = null;
  private reconnectTimeout: any = null;
  private shouldReconnect: boolean = true;
  private retryDelayMs: number = 2000;

  constructor(path: string = '/api/v1/ws/telemetry') {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.url = `${protocol}//${window.location.host}${path}`;
  }

  public connect(
    onMessage: (data: WebSocketEnvelope) => void,
    onStatusChange: (status: ConnectionStatus) => void
  ) {
    this.onMessageCallback = onMessage;
    this.onStatusChangeCallback = onStatusChange;
    this.shouldReconnect = true;
    this._initWebSocket();
  }

  private _initWebSocket() {
    try {
      this.onStatusChangeCallback?.('RECONNECTING');
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.onStatusChangeCallback?.('CONNECTED');
        this.retryDelayMs = 2000;
      };

      this.ws.onmessage = (event) => {
        try {
          const envelope: WebSocketEnvelope = JSON.parse(event.data);
          this.onMessageCallback?.(envelope);
        } catch {
          // parse error
        }
      };

      this.ws.onclose = () => {
        this.onStatusChangeCallback?.('DISCONNECTED');
        if (this.shouldReconnect) {
          this.reconnectTimeout = setTimeout(() => {
            this.retryDelayMs = Math.min(this.retryDelayMs * 1.5, 10000);
            this._initWebSocket();
          }, this.retryDelayMs);
        }
      };

      this.ws.onerror = () => {
        this.ws?.close();
      };
    } catch {
      this.onStatusChangeCallback?.('DISCONNECTED');
    }
  }

  public disconnect() {
    this.shouldReconnect = false;
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    this.ws?.close();
    this.ws = null;
  }
}
