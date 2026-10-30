const mongoose = require('mongoose');

const TicketSchema = new mongoose.Schema({
  drain_id: { type: String, required: true },
  risk_score: { type: Number, required: true },
  priority_index: { type: Number, required: true },
  status: { type: String, enum: ['Pending', 'In Progress', 'Resolved'], default: 'Pending' },
  assigned_team: { type: String, default: 'Unassigned Crew' },
  created_at: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Ticket', TicketSchema);