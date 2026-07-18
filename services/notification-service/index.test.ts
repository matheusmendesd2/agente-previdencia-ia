import request from 'supertest';
import app from './index';
import { getQueue, stopWorker } from './services/queue';

beforeEach(() => {
  getQueue().length = 0;
});

afterAll(() => {
  stopWorker();
});

describe('Health Check', () => {
  it('should return 200 on GET /health', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toEqual({ status: 'ok' });
  });
});

describe('POST /notify', () => {
  it('should enqueue a valid notification and return 202', async () => {
    const res = await request(app)
      .post('/notify')
      .send({ email: 'teste@example.com', subject: 'Assunto', message: 'Mensagem' });
    expect(res.status).toBe(202);
    expect(res.body).toHaveProperty('id');
    expect(res.body.status).toBe('enfileirado');
  });

  it('should return 400 for invalid email', async () => {
    const res = await request(app)
      .post('/notify')
      .send({ email: 'invalido', subject: 'Assunto', message: 'Mensagem' });
    expect(res.status).toBe(400);
    expect(res.body.erro).toContain('E-mail');
  });

  it('should return 400 for missing subject', async () => {
    const res = await request(app)
      .post('/notify')
      .send({ email: 'teste@example.com', message: 'Mensagem' });
    expect(res.status).toBe(400);
    expect(res.body.erro).toContain('Assunto');
  });

  it('should return 400 for missing message', async () => {
    const res = await request(app)
      .post('/notify')
      .send({ email: 'teste@example.com', subject: 'Assunto' });
    expect(res.status).toBe(400);
    expect(res.body.erro).toContain('Mensagem');
  });

  it('should return 400 for empty subject', async () => {
    const res = await request(app)
      .post('/notify')
      .send({ email: 'teste@example.com', subject: '', message: 'Mensagem' });
    expect(res.status).toBe(400);
  });
});

describe('POST /upload', () => {
  it('should reject request without file', async () => {
    const res = await request(app).post('/upload');
    expect(res.status).toBe(400);
    expect(res.body.erro).toContain('arquivo');
  });

  it('should reject non-CSV file', async () => {
    const res = await request(app)
      .post('/upload')
      .attach('file', Buffer.from('teste'), 'arquivo.txt');
    expect(res.status).toBe(400);
    expect(res.body.erro).toContain('CSV');
  });

  it('should accept CSV file', async () => {
    const csvContent = 'nome,email\nJoão,joao@teste.com';
    const res = await request(app)
      .post('/upload')
      .attach('file', Buffer.from(csvContent), 'apolices.csv');
    expect(res.status).toBe(200);
    expect(res.body.filename).toBe('apolices.csv');
    expect(res.body.status).toBe('recebido');
  });
});

describe('GET /notify/queue', () => {
  it('should return queue stats', async () => {
    await request(app)
      .post('/notify')
      .send({ email: 'a@b.com', subject: 'S', message: 'M' });
    const res = await request(app).get('/notify/queue');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('total');
    expect(res.body).toHaveProperty('pending');
    expect(res.body).toHaveProperty('sent');
    expect(res.body).toHaveProperty('failed');
    expect(res.body.total).toBe(1);
  });
});
