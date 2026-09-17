import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:5000/api' });

export const runWhatIfSimulation = (data) => API.post('/simulation/run-whatif', data);
export const dispatchTicket = (ticketData) => API.post('/tickets/dispatch', ticketData);
export const fetchTickets = () => API.get('/tickets');
export const resolveTicket = (id) => API.patch(`/tickets/resolve/${id}`);