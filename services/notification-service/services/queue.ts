export interface Notification {
  id: string;
  email: string;
  subject: string;
  message: string;
  status: 'pending' | 'sent' | 'failed';
  createdAt: Date;
  processedAt?: Date;
}

interface QueueStats {
  total: number;
  pending: number;
  sent: number;
  failed: number;
}

const queue: Notification[] = [];
let workerInterval: ReturnType<typeof setInterval> | null = null;

function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

export function enqueue(email: string, subject: string, message: string): Notification {
  const notification: Notification = {
    id: generateId(),
    email,
    subject,
    message,
    status: 'pending',
    createdAt: new Date(),
  };
  queue.push(notification);
  return notification;
}

function processItem(item: Notification): void {
  if (!item.email.includes('@')) {
    item.status = 'failed';
    item.processedAt = new Date();
    return;
  }
  item.status = 'sent';
  item.processedAt = new Date();
}

export function processQueue(): number {
  const pending = queue.filter(n => n.status === 'pending');
  for (const item of pending) {
    processItem(item);
  }
  return pending.length;
}

export function startWorker(intervalMs = 5000): void {
  if (workerInterval) return;
  workerInterval = setInterval(() => {
    const count = processQueue();
    if (count > 0) {
      console.log(`[worker] Processed ${count} notification(s)`);
    }
  }, intervalMs);
}

export function stopWorker(): void {
  if (workerInterval) {
    clearInterval(workerInterval);
    workerInterval = null;
  }
}

export function getQueue(): Notification[] {
  return queue;
}

export function getStats(): QueueStats {
  return {
    total: queue.length,
    pending: queue.filter(n => n.status === 'pending').length,
    sent: queue.filter(n => n.status === 'sent').length,
    failed: queue.filter(n => n.status === 'failed').length,
  };
}
