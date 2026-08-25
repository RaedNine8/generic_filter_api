import express from 'express';

export const app = express();
app.use(express.json());

app.get('/health', (_req, res) => res.json({ok: true}));
// FILTERX:ROUTER_MOUNT
