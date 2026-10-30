const express = require('express');
const router = express.Router();

let inMemoryTickets = [];

router.post('/dispatch', (req, res) => {
  const { drain_id, risk_score, priority_index, location_name } = req.body;
  const newTicket = {
    _id: Date.now().toString(),
    drain_id,
    location_name: location_name || 'CMC Zone Drain',
    risk_score,
    priority_index,
    status: 'Pending',
    created_at: new Date()
  };
  inMemoryTickets.unshift(newTicket);
  res.status(201).json({ success: true, ticket: newTicket });
});

router.get('/', (req, res) => {
  res.status(200).json(inMemoryTickets);
});

// Resolve endpoint matching /api/tickets/resolve/:id
router.patch('/resolve/:id', (req, res) => {
  const { id } = req.params;
  inMemoryTickets = inMemoryTickets.map(t => 
    t._id === id ? { ...t, status: 'Resolved' } : t
  );
  res.status(200).json({ success: true });
});

module.exports = router;