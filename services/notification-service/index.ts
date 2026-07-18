import express from 'express';
import multer from 'multer';
import { enqueue, getStats, startWorker } from './services/queue';

const app = express();
const PORT = process.env.PORT || 3000;
const upload = multer({ dest: '/tmp/uploads' });

app.use(express.json());

app.get('/health', (_req, res) => {
  res.json({ status: 'ok' });
});

app.get('/notify/queue', (_req, res) => {
  res.json(getStats());
});

app.post('/notify', (req, res) => {
  const { email, subject, message } = req.body;

  if (!email || typeof email !== 'string' || !email.includes('@') || !email.includes('.')) {
    return res.status(400).json({ erro: 'E-mail inválido' });
  }
  if (!subject || typeof subject !== 'string' || subject.trim().length === 0) {
    return res.status(400).json({ erro: 'Assunto é obrigatório' });
  }
  if (!message || typeof message !== 'string' || message.trim().length === 0) {
    return res.status(400).json({ erro: 'Mensagem é obrigatória' });
  }

  const notification = enqueue(email, subject, message);
  res.status(202).json({ id: notification.id, status: 'enfileirado' });
});

app.post('/upload', upload.single('file'), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ erro: 'Nenhum arquivo enviado' });
  }

  const ext = req.file.originalname.split('.').pop()?.toLowerCase();
  if (ext !== 'csv') {
    return res.status(400).json({ erro: 'Formato inválido. Envie um arquivo CSV' });
  }

  res.json({ filename: req.file.originalname, size: req.file.size, status: 'recebido' });
});

if (process.env.NODE_ENV !== 'test') {
  startWorker();
  app.listen(PORT, () => {
    console.log(`Notification service running on port ${PORT}`);
  });
}

export default app;
