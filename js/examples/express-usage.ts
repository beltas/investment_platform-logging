/**
 * Express middleware integration example.
 */

import express from 'express';
import { initialize, configFromEnv } from '../src/index.js';
import { loggingMiddleware, getRequestLogger } from '../src/integrations/express.js';

const app = express();

// Initialize logging
initialize(configFromEnv('express-example'));

// Add logging middleware
app.use(loggingMiddleware());

// Example route
app.get('/api/prices/:symbol', async (req, res) => {
  const logger = getRequestLogger();

  logger.info('Fetching price', { symbol: req.params.symbol });

  try {
    // Simulate database query with timer
    const price = await logger.timer(
      'Database query',
      async () => {
        await new Promise((resolve) => setTimeout(resolve, 20));
        return { symbol: req.params.symbol, price: 150.25, volume: 1000000 };
      },
      { table: 'stock_prices' }
    );

    logger.info('Price fetched successfully', { symbol: req.params.symbol });
    res.json(price);
  } catch (error) {
    logger.error('Failed to fetch price', error as Error, {
      symbol: req.params.symbol,
    });
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Error handling route
app.get('/api/error', (req, res) => {
  const logger = getRequestLogger();

  try {
    throw new Error('Simulated error');
  } catch (error) {
    logger.error('Error occurred', error as Error);
    res.status(500).json({ error: 'Error occurred' });
  }
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
  console.log(`Try: curl http://localhost:${PORT}/api/prices/AAPL`);
});
